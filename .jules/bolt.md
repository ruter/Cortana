## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - [Conversation Cache Global Lock Bottleneck]
**Learning:** The `ConversationCache` used a single global `asyncio.Lock` for both in-memory updates and file persistence. This meant that saving one user's conversation to disk (which is slow) blocked *all* other users from accessing the cache.
**Action:** Split locking strategies: use global lock for fast in-memory operations and per-user locks for slow I/O operations. Always snapshot state inside the global lock before persisting outside it.
