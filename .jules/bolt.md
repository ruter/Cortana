## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Global Async Lock Blocking Thread Pool I/O
**Learning:** Holding an `asyncio.Lock` while awaiting `loop.run_in_executor` effectively serializes the threaded operations, negating the benefits of the thread pool for concurrent requests. The `await` yields control, but the lock prevents other coroutines from entering the critical section to schedule their own threaded work.
**Action:** Always release global async locks before awaiting `run_in_executor` operations. Use granular (per-resource) locks or snapshots to ensure data consistency during the off-critical-path I/O.
