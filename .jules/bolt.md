## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Global Lock in Conversation Cache
**Learning:** The `ConversationCache` used a single global `asyncio.Lock` for both in-memory updates and disk I/O. This meant that saving one user's conversation to disk blocked all other users from accessing the cache.
**Action:** When implementing persistence for a shared cache, separate the in-memory synchronization (global lock) from the I/O synchronization (per-user/item lock) to improve concurrency.
