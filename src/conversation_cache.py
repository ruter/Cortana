"""
Conversation Cache Module
=========================

Provides in-memory conversation history caching with TTL-based expiration
and automatic compaction when approaching context limits.

Features:
- TTL-based automatic expiration (sliding window)
- Token counting and threshold-based compaction
- LLM-powered conversation summarization
- File-based persistence for crash recovery
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import config
from .rotator_client import token_count, rotating_completion, normalize_model_name

logger = logging.getLogger(__name__)


# Default configuration values
DEFAULT_TTL_SECONDS = 1800  # 30 minutes
DEFAULT_TOKEN_THRESHOLD = 0.8  # 80% of model limit
DEFAULT_KEEP_RECENT = 3  # Keep last N message pairs after compact

# Default fallback context limit when model info is unavailable
DEFAULT_CONTEXT_LIMIT = 32000


def get_model_context_limit(model: str) -> int:
    """
    Get the context window limit for a model using litellm.
    
    Uses litellm's model_cost dictionary which contains max_input_tokens
    for all supported models. Falls back to get_max_tokens() if needed.
    
    Args:
        model: Model name (with or without provider prefix).
    
    Returns:
        Context window size in tokens.
    """
    # Normalize model name - remove provider prefix for litellm lookup
    model_name = model.split("/")[-1] if "/" in model else model
    
    try:
        import litellm
        
        # Try litellm.model_cost first (contains max_input_tokens)
        if hasattr(litellm, 'model_cost') and litellm.model_cost:
            # Try exact match
            if model_name in litellm.model_cost:
                info = litellm.model_cost[model_name]
                # Prefer max_input_tokens, fall back to max_tokens
                return info.get("max_input_tokens") or info.get("max_tokens") or DEFAULT_CONTEXT_LIMIT
            
            # Try with provider prefix (e.g., "openai/gpt-4o")
            if model in litellm.model_cost:
                info = litellm.model_cost[model]
                return info.get("max_input_tokens") or info.get("max_tokens") or DEFAULT_CONTEXT_LIMIT
        
        # Fallback to get_max_tokens function
        try:
            max_tokens = litellm.get_max_tokens(model_name)
            if max_tokens and max_tokens > 0:
                return max_tokens
        except Exception:
            pass
        
    except ImportError:
        logger.debug("litellm not available, using default context limit")
    except Exception as e:
        logger.debug(f"Error getting model context limit from litellm: {e}")
    
    return DEFAULT_CONTEXT_LIMIT


@dataclass
class CachedMessage:
    """A single cached message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    token_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenAI message format."""
        return {"role": self.role, "content": self.content}
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable format."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "token_count": self.token_count,
        }
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "CachedMessage":
        """Create from JSON data."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            token_count=data.get("token_count", 0),
        )


@dataclass
class ConversationState:
    """
    State of a single conversation.
    
    Attributes:
        user_id: The user's identifier.
        messages: List of cached messages.
        compact_summary: Summary from previous compaction (if any).
        last_activity: Timestamp of last activity (for TTL).
        ttl_seconds: Time-to-live in seconds.
        total_tokens: Cached total token count.
    """
    user_id: str
    messages: List[CachedMessage] = field(default_factory=list)
    compact_summary: Optional[str] = None
    last_activity: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = DEFAULT_TTL_SECONDS
    total_tokens: int = 0
    
    def is_expired(self) -> bool:
        """Check if the conversation has expired."""
        return datetime.now() > self.last_activity + timedelta(seconds=self.ttl_seconds)
    
    def touch(self) -> None:
        """Update last activity timestamp (sliding window TTL)."""
        self.last_activity = datetime.now()
    
    def get_openai_messages(self) -> List[Dict[str, Any]]:
        """
        Get messages in OpenAI format.
        
        If there's a compact summary, prepend it as a system message supplement.
        """
        result = []
        
        if self.compact_summary:
            result.append({
                "role": "system",
                "content": f"[Conversation Summary]\n{self.compact_summary}\n[End Summary]"
            })
        
        for msg in self.messages:
            result.append(msg.to_dict())
        
        return result
    
    def calculate_tokens(self, model: str) -> int:
        """Calculate and cache total token count."""
        total = 0
        
        if self.compact_summary:
            total += token_count(model, text=self.compact_summary)
        
        for msg in self.messages:
            if msg.token_count == 0:
                msg.token_count = token_count(model, text=msg.content)
            total += msg.token_count
        
        self.total_tokens = total
        return total
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable format."""
        return {
            "user_id": self.user_id,
            "messages": [m.to_json() for m in self.messages],
            "compact_summary": self.compact_summary,
            "last_activity": self.last_activity.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "total_tokens": self.total_tokens,
        }
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "ConversationState":
        """Create from JSON data."""
        return cls(
            user_id=data["user_id"],
            messages=[CachedMessage.from_json(m) for m in data.get("messages", [])],
            compact_summary=data.get("compact_summary"),
            last_activity=datetime.fromisoformat(data.get("last_activity", datetime.now().isoformat())),
            ttl_seconds=data.get("ttl_seconds", DEFAULT_TTL_SECONDS),
            total_tokens=data.get("total_tokens", 0),
        )


class ConversationCache:
    """
    In-memory conversation cache with TTL and compaction.
    
    Thread-safe via asyncio.Lock.
    
    Usage:
        cache = ConversationCache()
        
        # Add messages
        await cache.add_message(user_id, "user", "Hello!")
        await cache.add_message(user_id, "assistant", "Hi there!")
        
        # Get history for LLM
        history = await cache.get_history(user_id, model="gpt-4o")
        
        # Clear on explicit reset
        await cache.clear(user_id)
    """
    
    def __init__(
        self,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        token_threshold: float = DEFAULT_TOKEN_THRESHOLD,
        keep_recent: int = DEFAULT_KEEP_RECENT,
        persistence_dir: Optional[str] = None,
    ):
        """
        Initialize the conversation cache.
        
        Args:
            ttl_seconds: Time-to-live for conversations.
            token_threshold: Fraction of context limit to trigger compaction.
            keep_recent: Number of recent message pairs to keep after compaction.
            persistence_dir: Directory for file-based persistence (optional).
        """
        self._cache: Dict[str, ConversationState] = {}
        self._lock = asyncio.Lock()
        self._user_locks: Dict[str, asyncio.Lock] = {}
        self.ttl_seconds = ttl_seconds
        self.token_threshold = token_threshold
        self.keep_recent = keep_recent
        self.persistence_dir = Path(persistence_dir) if persistence_dir else None
        
        # Create persistence directory if specified
        if self.persistence_dir:
            self.persistence_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ConversationCache initialized: TTL={ttl_seconds}s, threshold={token_threshold}")
    
    def _get_user_lock(self, user_id: str) -> asyncio.Lock:
        """Get or create a lock for a specific user."""
        if user_id not in self._user_locks:
            self._user_locks[user_id] = asyncio.Lock()
        return self._user_locks[user_id]

    def _get_persistence_path(self, user_id: str) -> Optional[Path]:
        """Get the persistence file path for a user."""
        if not self.persistence_dir:
            return None
        return self.persistence_dir / f"conversation_{user_id}.jsonl"
    
    def _sync_load(self, path: Path) -> Optional[Dict[str, Any]]:
        """Synchronous load for executor."""
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def _load_from_file(self, user_id: str) -> Optional[ConversationState]:
        """Load conversation state from file if exists."""
        path = self._get_persistence_path(user_id)
        if not path:
            return None
        
        try:
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, self._sync_load, path)

            if not data:
                return None
            
            state = ConversationState.from_json(data)
            
            # Check if loaded state is expired
            if state.is_expired():
                await self._delete_file(user_id)
                return None
            
            logger.debug(f"Loaded conversation state from file for user {user_id}")
            return state
            
        except Exception as e:
            logger.warning(f"Failed to load conversation from file: {e}")
            return None
    
    def _sync_save(self, path: Path, data: Dict[str, Any]) -> None:
        """Synchronous save for executor."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def _save_to_file(self, state: ConversationState) -> None:
        """Save conversation state to file."""
        path = self._get_persistence_path(state.user_id)
        if not path:
            return
        
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._sync_save, path, state.to_json())
            logger.debug(f"Saved conversation state to file for user {state.user_id}")
        except Exception as e:
            logger.warning(f"Failed to save conversation to file: {e}")
    
    def _sync_delete(self, path: Path) -> None:
        """Synchronous delete for executor."""
        if path.exists():
            path.unlink()

    async def _delete_file(self, user_id: str) -> None:
        """Delete the persistence file for a user."""
        path = self._get_persistence_path(user_id)
        if path:
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self._sync_delete, path)
                logger.debug(f"Deleted conversation file for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to delete conversation file: {e}")
    
    async def get_or_create(self, user_id: str) -> ConversationState:
        """Get existing conversation or create new one."""
        async with self._lock:
            # Check in-memory cache first
            if user_id in self._cache:
                state = self._cache[user_id]
                if state.is_expired():
                    # Expired, remove and create new
                    del self._cache[user_id]
                    await self._delete_file(user_id)
                else:
                    return state
            
            # Try to load from file
            state = await self._load_from_file(user_id)
            if state:
                self._cache[user_id] = state
                return state
            
            # Create new conversation
            state = ConversationState(
                user_id=user_id,
                ttl_seconds=self.ttl_seconds,
            )
            self._cache[user_id] = state
            return state
    
    async def add_message(
        self,
        user_id: str,
        role: str,
        content: str,
        model: Optional[str] = None,
    ) -> None:
        """
        Add a message to the conversation cache.
        
        Args:
            user_id: User identifier.
            role: Message role ("user" or "assistant").
            content: Message content.
            model: Model name for token counting.
        """
        while True:
            # Get state (uses global lock internally)
            state = await self.get_or_create(user_id)
            user_lock = self._get_user_lock(user_id)
            
            async with user_lock:
                # 1. Verify lock identity (race condition with cleanup/clear)
                if self._user_locks.get(user_id) is not user_lock:
                    continue

                # 2. Verify state is still valid (prevent resurrection bug)
                async with self._lock:
                    if user_id not in self._cache or self._cache[user_id] is not state:
                        # State changed or removed, retry
                        continue

                # Calculate token count
                model = model or config.LLM_MODEL_NAME
                tokens = token_count(model, text=content)

                # Create message
                msg = CachedMessage(
                    role=role,
                    content=content,
                    token_count=tokens,
                )

                state.messages.append(msg)
                state.total_tokens += tokens
                state.touch()

                # Save to file
                await self._save_to_file(state)
                break
        
        logger.debug(f"Added {role} message for user {user_id}: {tokens} tokens, total: {state.total_tokens}")
    
    async def get_history(
        self,
        user_id: str,
        model: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for LLM consumption.
        
        Automatically triggers compaction if token limit is approached.
        
        Args:
            user_id: User identifier.
            model: Model name for context limit check.
        
        Returns:
            List of messages in OpenAI format.
        """
        state = await self.get_or_create(user_id)
        
        if state.is_expired():
            await self.clear(user_id)
            return []
        
        model = model or config.LLM_MODEL_NAME
        context_limit = get_model_context_limit(model)
        threshold = int(context_limit * self.token_threshold)
        
        user_lock = self._get_user_lock(user_id)
        async with user_lock:
            # Verify lock identity
            if self._user_locks.get(user_id) is not user_lock:
                return await self.get_history(user_id, model)

            # Verify state validity
            async with self._lock:
                if user_id not in self._cache or self._cache[user_id] is not state:
                    # Retry
                    return await self.get_history(user_id, model)

            current_tokens = state.calculate_tokens(model)
        
            # Check if compaction is needed
            if current_tokens > threshold:
                logger.info(f"Token threshold exceeded ({current_tokens}/{threshold}), compacting...")
                # _compact handles its own locking logic.
                pass

        # Call _compact outside user_lock to avoid reentrancy issues if _compact acquires it
        if current_tokens > threshold:
            await self._compact(user_id, model)
        
        state.touch()
        return state.get_openai_messages()
    
    async def _compact(self, user_id: str, model: str) -> None:
        """
        Compact the conversation by summarizing old messages.
        
        1. Generate LLM summary of conversation
        2. Keep only recent N message pairs
        3. Store summary as compact_summary
        4. Reset TTL
        """
        while True:
            state = await self.get_or_create(user_id)
            user_lock = self._get_user_lock(user_id)
            
            messages_to_summarize_count = 0
            
            async with user_lock:
                if self._user_locks.get(user_id) is not user_lock:
                    continue

                async with self._lock:
                    if user_id not in self._cache or self._cache[user_id] is not state:
                        continue

                if len(state.messages) <= self.keep_recent * 2:
                    return

                # Prepare messages for summarization
                messages_to_summarize = state.messages[:-self.keep_recent * 2]
                messages_to_summarize_count = len(messages_to_summarize)

                # Build conversation text for summary
                conversation_text = ""
                if state.compact_summary:
                    conversation_text = f"[Previous Summary]\n{state.compact_summary}\n\n[New Conversation]\n"

                for msg in messages_to_summarize:
                    role_label = "User" if msg.role == "user" else "Assistant"
                    conversation_text += f"{role_label}: {msg.content}\n\n"
            
            # Generate summary (outside lock to avoid blocking)
            summary = await self._generate_summary(conversation_text, model)
            
            async with user_lock:
                if self._user_locks.get(user_id) is not user_lock:
                    continue

                async with self._lock:
                     if user_id not in self._cache or self._cache[user_id] is not state:
                         continue

                # Update state
                state.compact_summary = summary

                # Safely update messages preserving concurrency
                if len(state.messages) >= messages_to_summarize_count:
                    state.messages = state.messages[messages_to_summarize_count:]
                else:
                    state.messages = state.messages[-self.keep_recent * 2:]

                state.touch()

                # Recalculate tokens
                state.calculate_tokens(model)

                # Save to file
                await self._save_to_file(state)
            break
        
        logger.info(f"Compacted conversation for user {user_id}: {messages_to_summarize_count} messages summarized")
    
    async def _generate_summary(self, conversation_text: str, model: str) -> str:
        """
        Generate a summary of the conversation using LLM.
        
        Args:
            conversation_text: The conversation to summarize.
            model: Model to use for summarization.
        
        Returns:
            Summary string.
        """
        prompt = """Summarize the following conversation history into a concise summary, preserving:
1. User's key needs and preferences
2. Important task context and ongoing items
3. Key decisions, conclusions, and commitments
4. Relevant factual information (dates, times, names, etc.)

Output as concise bullet points, maximizing information density.

Conversation history:
"""
        
        try:
            response = await rotating_completion(
                model=normalize_model_name(model),
                messages=[
                    {"role": "system", "content": "You are a conversation summarization assistant. Extract and compress key information from conversations."},
                    {"role": "user", "content": prompt + conversation_text}
                ],
                max_tokens=1000,
            )
            
            if hasattr(response, "choices") and response.choices:
                return response.choices[0].message.content or ""
            
            return ""
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            # Fallback: just keep a truncated version
            return f"[Summary generation failed. Conversation had approximately {len(conversation_text)} characters.]"
    
    async def clear(self, user_id: str) -> None:
        """
        Clear conversation cache for a user.
        
        Args:
            user_id: User identifier.
        """
        user_lock = self._get_user_lock(user_id)
        async with user_lock:
            if self._user_locks.get(user_id) is not user_lock:
                return await self.clear(user_id)

            async with self._lock:
                if user_id in self._cache:
                    del self._cache[user_id]

                if user_id in self._user_locks:
                    del self._user_locks[user_id]

                await self._delete_file(user_id)
        
        logger.info(f"Cleared conversation cache for user {user_id}")
    
    async def cleanup_expired(self) -> int:
        """
        Remove all expired conversations.
        
        Returns:
            Number of conversations removed.
        """
        removed_count = 0

        # Snapshot candidates under global lock
        async with self._lock:
            candidates = list(self._cache.items())
            
        for user_id, state in candidates:
            # Optimistic check
            if state.is_expired():
                user_lock = self._get_user_lock(user_id)
                async with user_lock:
                    if self._user_locks.get(user_id) is not user_lock:
                         continue

                    async with self._lock:
                        # Verify still in cache, same state, and still expired
                        if (user_id in self._cache and
                            self._cache[user_id] is state and
                            state.is_expired()):

                            del self._cache[user_id]

                            if user_id in self._user_locks:
                                del self._user_locks[user_id]

                            await self._delete_file(user_id)
                            removed_count += 1
        
        if removed_count:
            logger.info(f"Cleaned up {removed_count} expired conversations")
        
        return removed_count
    
    def get_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cache statistics for a user.
        
        Args:
            user_id: User identifier.
        
        Returns:
            Stats dict or None if not cached.
        """
        state = self._cache.get(user_id)
        if not state:
            return None
        
        return {
            "message_count": len(state.messages),
            "total_tokens": state.total_tokens,
            "has_summary": state.compact_summary is not None,
            "last_activity": state.last_activity.isoformat(),
            "expires_in": (state.last_activity + timedelta(seconds=state.ttl_seconds) - datetime.now()).total_seconds(),
        }


# Global singleton instance
_conversation_cache: Optional[ConversationCache] = None


def get_conversation_cache() -> ConversationCache:
    """
    Get or create the global ConversationCache instance.
    
    Returns:
        The singleton ConversationCache.
    """
    global _conversation_cache
    
    if _conversation_cache is None:
        # Get configuration from environment
        ttl = int(os.getenv("CONVERSATION_TTL_SECONDS", DEFAULT_TTL_SECONDS))
        threshold = float(os.getenv("CONVERSATION_TOKEN_THRESHOLD", DEFAULT_TOKEN_THRESHOLD))
        keep_recent = int(os.getenv("CONVERSATION_KEEP_RECENT", DEFAULT_KEEP_RECENT))
        
        # Use workspace directory for persistence
        persistence_dir = os.path.join(config.WORKSPACE_DIR, ".conversation_cache")
        
        _conversation_cache = ConversationCache(
            ttl_seconds=ttl,
            token_threshold=threshold,
            keep_recent=keep_recent,
            persistence_dir=persistence_dir,
        )
    
    return _conversation_cache
