## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-23 - Global Lock Bottleneck in Async Caches
**Learning:** A single global lock in `ConversationCache` serialized all file I/O operations across all users, even though the I/O itself was offloaded to threads. `async with lock:` blocks the event loop's access to the lock until the critical section completes, including awaited I/O tasks.
**Action:** Use fine-grained locking (per-user locks) for I/O operations and restrict global locks to in-memory state updates only. Snapshot state under the global lock, then perform I/O outside it.
