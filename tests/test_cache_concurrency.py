import asyncio
import time
import pytest
import tempfile
import shutil
from src.conversation_cache import ConversationCache, ConversationState, DEFAULT_TTL_SECONDS
from pathlib import Path
from unittest.mock import patch

# Mock slow sync save
def slow_sync_save(path, data):
    time.sleep(0.5)  # Simulate slow I/O
    # Real save logic if needed, but we can skip for repro
    pass

# Mock fast token count
def fast_token_count(model, text=None, messages=None):
    return 10

@pytest.mark.asyncio
async def test_cache_blocking_behavior():
    """
    Test that saving a conversation for one user currently blocks another user.
    With optimization, this should run much faster.
    """
    # Create temp dir for persistence
    tmp_dir = tempfile.mkdtemp()
    try:
        cache = ConversationCache(persistence_dir=tmp_dir)

        # Monkeypatch _sync_save to be slow
        # We need to bind it to the instance or just use a static/free function if self isn't used (it isn't in mock)
        # But run_in_executor calls it.
        # Let's monkeypatch the method on the instance.
        cache._sync_save = slow_sync_save

        # Patch token_count to avoid external calls/slowdowns
        with patch("src.conversation_cache.token_count", side_effect=fast_token_count):
            start_time = time.time()

            # Task 1: User A adds message (will take ~0.5s due to save)
            task1 = asyncio.create_task(cache.add_message("user_A", "user", "Hello A"))

            # Small delay to ensure task1 starts and grabs lock
            await asyncio.sleep(0.1)

            # Task 2: User B adds message (should be blocked if global lock is held)
            task2 = asyncio.create_task(cache.add_message("user_B", "user", "Hello B"))

            await asyncio.gather(task1, task2)

            duration = time.time() - start_time
            print(f"\nTotal duration: {duration:.4f}s")

            # Without optimization: task1 holds lock for 0.5s. task2 waits. Total ~0.5s + overhead.
            # Wait, if task1 runs 0.5s, task2 waits 0.5s, then runs 0.5s. Total 1.0s.
            # If parallel: 0.5s total.

            assert duration < 0.7, f"Blocking detected! Duration: {duration:.4f}s (Expected < 0.7s)"

    finally:
        shutil.rmtree(tmp_dir)

if __name__ == "__main__":
    asyncio.run(test_cache_blocking_behavior())
