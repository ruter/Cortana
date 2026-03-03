"""
Tests for the ConversationCache module.
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.conversation_cache import (
    CachedMessage,
    ConversationCache,
    ConversationState,
    get_model_context_limit,
    DEFAULT_TTL_SECONDS,
    DEFAULT_TOKEN_THRESHOLD,
    DEFAULT_KEEP_RECENT,
    DEFAULT_CONTEXT_LIMIT,
)


class TestModelContextLimits:
    """Tests for model context limit lookup using litellm."""
    
    def test_known_model_returns_positive_value(self):
        """Known models should return a positive context limit."""
        limit = get_model_context_limit("gpt-4o")
        assert limit > 0
        # GPT-4o should have a large context window
        assert limit >= 32000
    
    def test_model_with_provider_prefix(self):
        """Models with provider prefix should work."""
        limit = get_model_context_limit("openai/gpt-4o")
        assert limit > 0
    
    def test_unknown_model_fallback(self):
        """Unknown models should return the default fallback."""
        assert get_model_context_limit("some-completely-unknown-model-xyz") == DEFAULT_CONTEXT_LIMIT
    
    def test_returns_integer(self):
        """Should always return an integer."""
        limit = get_model_context_limit("gpt-4o")
        assert isinstance(limit, int)


class TestCachedMessage:
    """Tests for CachedMessage dataclass."""
    
    def test_to_dict(self):
        msg = CachedMessage(role="user", content="Hello!")
        result = msg.to_dict()
        assert result == {"role": "user", "content": "Hello!"}
    
    def test_to_json_and_back(self):
        msg = CachedMessage(
            role="assistant",
            content="Hi there!",
            token_count=5,
        )
        json_data = msg.to_json()
        restored = CachedMessage.from_json(json_data)
        
        assert restored.role == msg.role
        assert restored.content == msg.content
        assert restored.token_count == msg.token_count


class TestConversationState:
    """Tests for ConversationState dataclass."""
    
    def test_is_expired_fresh(self):
        state = ConversationState(user_id="123", ttl_seconds=60)
        assert not state.is_expired()
    
    def test_is_expired_old(self):
        state = ConversationState(user_id="123", ttl_seconds=60)
        state.last_activity = datetime.now() - timedelta(seconds=120)
        assert state.is_expired()
    
    def test_touch_refreshes_ttl(self):
        state = ConversationState(user_id="123", ttl_seconds=60)
        old_time = datetime.now() - timedelta(seconds=30)
        state.last_activity = old_time
        
        state.touch()
        
        assert state.last_activity > old_time
    
    def test_get_openai_messages_without_summary(self):
        state = ConversationState(user_id="123")
        state.messages = [
            CachedMessage(role="user", content="Hello"),
            CachedMessage(role="assistant", content="Hi!"),
        ]
        
        messages = state.get_openai_messages()
        
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
    
    def test_get_openai_messages_with_summary(self):
        state = ConversationState(user_id="123")
        state.compact_summary = "Previous context summary"
        state.messages = [
            CachedMessage(role="user", content="New message"),
        ]
        
        messages = state.get_openai_messages()
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "Previous context summary" in messages[0]["content"]
        assert messages[1]["role"] == "user"
    
    def test_json_serialization(self):
        state = ConversationState(
            user_id="123",
            ttl_seconds=3600,
            compact_summary="Summary text",
        )
        state.messages = [
            CachedMessage(role="user", content="Test"),
        ]
        
        json_data = state.to_json()
        restored = ConversationState.from_json(json_data)
        
        assert restored.user_id == state.user_id
        assert restored.ttl_seconds == state.ttl_seconds
        assert restored.compact_summary == state.compact_summary
        assert len(restored.messages) == 1
        assert restored.messages[0].content == "Test"


class TestConversationCache:
    """Tests for ConversationCache class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for persistence tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def cache(self, temp_dir):
        """Create a ConversationCache instance with temp persistence."""
        return ConversationCache(
            ttl_seconds=60,
            token_threshold=0.8,
            keep_recent=2,
            persistence_dir=temp_dir,
        )
    
    @pytest.mark.asyncio
    async def test_get_or_create_new(self, cache):
        state = await cache.get_or_create("user123")
        assert state.user_id == "user123"
        assert len(state.messages) == 0
    
    @pytest.mark.asyncio
    async def test_get_or_create_existing(self, cache):
        state1 = await cache.get_or_create("user123")
        state1.messages.append(CachedMessage(role="user", content="Test"))
        
        state2 = await cache.get_or_create("user123")
        
        assert state1 is state2
        assert len(state2.messages) == 1
    
    @pytest.mark.asyncio
    async def test_add_message(self, cache):
        with patch("src.conversation_cache.token_count", return_value=10):
            await cache.add_message("user123", "user", "Hello!")
            await cache.add_message("user123", "assistant", "Hi there!")
        
        state = await cache.get_or_create("user123")
        assert len(state.messages) == 2
        assert state.messages[0].content == "Hello!"
        assert state.messages[1].content == "Hi there!"
    
    @pytest.mark.asyncio
    async def test_get_history_empty(self, cache):
        history = await cache.get_history("user123")
        assert history == []
    
    @pytest.mark.asyncio
    async def test_get_history_with_messages(self, cache):
        with patch("src.conversation_cache.token_count", return_value=10):
            await cache.add_message("user123", "user", "Hello!")
            await cache.add_message("user123", "assistant", "Hi!")
        
        history = await cache.get_history("user123")
        
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
    
    @pytest.mark.asyncio
    async def test_clear(self, cache, temp_dir):
        with patch("src.conversation_cache.token_count", return_value=10):
            await cache.add_message("user123", "user", "Hello!")
        
        # Ensure message is saved before clearing (although clear handles locking correctly)
        await cache.await_all_background_tasks()

        await cache.clear("user123")
        
        history = await cache.get_history("user123")
        assert history == []
        
        # Check file is deleted
        assert not (Path(temp_dir) / "conversation_user123.jsonl").exists()
    
    @pytest.mark.asyncio
    async def test_persistence_save_and_load(self, temp_dir):
        cache1 = ConversationCache(persistence_dir=temp_dir)
        
        with patch("src.conversation_cache.token_count", return_value=10):
            await cache1.add_message("user123", "user", "Persisted message")
        
        # Wait for background save to complete
        await cache1.await_all_background_tasks()

        # Create new cache instance (simulating restart)
        cache2 = ConversationCache(persistence_dir=temp_dir)
        
        state = await cache2.get_or_create("user123")
        
        assert len(state.messages) == 1
        assert state.messages[0].content == "Persisted message"

    @pytest.mark.asyncio
    async def test_add_message_async_behavior(self, cache):
        """Verify that add_message creates a background task."""
        with patch("src.conversation_cache.token_count", return_value=10):
            await cache.add_message("user123", "user", "Hello!")

        # Should have at least one background task
        assert len(cache._background_tasks) > 0

        # Wait for it
        await cache.await_all_background_tasks()

        # Should be done
        pending = {t for t in cache._background_tasks if not t.done()}
        assert len(pending) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self, cache):
        state = await cache.get_or_create("user123")
        state.last_activity = datetime.now() - timedelta(seconds=3600)
        
        removed = await cache.cleanup_expired()
        
        assert removed == 1
        assert "user123" not in cache._cache
    
    @pytest.mark.asyncio
    async def test_get_stats(self, cache):
        with patch("src.conversation_cache.token_count", return_value=10):
            await cache.add_message("user123", "user", "Hello!")
        
        stats = cache.get_stats("user123")
        
        assert stats is not None
        assert stats["message_count"] == 1
        assert stats["total_tokens"] == 10
        assert not stats["has_summary"]
    
    @pytest.mark.asyncio
    async def test_compaction_triggered(self, cache):
        """Test that compaction is triggered when token threshold is exceeded."""
        # Mock to simulate exceeding threshold
        with patch("src.conversation_cache.token_count", return_value=100000):
            with patch("src.conversation_cache.get_model_context_limit", return_value=200000):
                with patch.object(cache, "_compact", new_callable=AsyncMock) as mock_compact:
                    # Add many messages
                    for i in range(10):
                        await cache.add_message("user123", "user", f"Message {i}")
                        await cache.add_message("user123", "assistant", f"Response {i}")
                    
                    # This should trigger compaction
                    await cache.get_history("user123", model="gpt-4o")
                    
                    mock_compact.assert_called()


class TestCompaction:
    """Tests for the compaction logic."""
    
    @pytest.fixture
    def cache(self):
        return ConversationCache(
            ttl_seconds=60,
            token_threshold=0.8,
            keep_recent=2,
        )
    
    @pytest.mark.asyncio
    async def test_generate_summary_success(self, cache):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Summary of conversation"
        
        with patch("src.conversation_cache.rotating_completion", new_callable=AsyncMock, return_value=mock_response):
            summary = await cache._generate_summary("Some conversation text", "gpt-4o")
        
        assert summary == "Summary of conversation"
    
    @pytest.mark.asyncio
    async def test_generate_summary_failure(self, cache):
        with patch("src.conversation_cache.rotating_completion", new_callable=AsyncMock, side_effect=Exception("API Error")):
            summary = await cache._generate_summary("Some conversation text", "gpt-4o")
        
        assert "Summary generation failed" in summary
    
    @pytest.mark.asyncio
    async def test_compact_preserves_recent_messages(self, cache):
        with patch("src.conversation_cache.token_count", return_value=10):
            # Add 10 message pairs
            for i in range(10):
                await cache.add_message("user123", "user", f"User message {i}")
                await cache.add_message("user123", "assistant", f"Assistant response {i}")
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Compacted summary"
        
        with patch("src.conversation_cache.rotating_completion", new_callable=AsyncMock, return_value=mock_response):
            await cache._compact("user123", "gpt-4o")
        
        state = await cache.get_or_create("user123")
        
        # Should keep only last 2 pairs (4 messages)
        assert len(state.messages) == 4
        assert state.compact_summary == "Compacted summary"
        # Verify the kept messages are the most recent ones
        assert state.messages[0].content == "User message 8"
        assert state.messages[-1].content == "Assistant response 9"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
