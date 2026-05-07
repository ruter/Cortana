## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Synchronous Database Client Blocks Asyncio Loop
**Learning:** The Supabase Python client's `execute()` method is synchronous. When called inside high-frequency async tools like `ensure_user_exists`, it blocks the entire asyncio event loop, causing severe latency for all concurrent tasks.
**Action:** Always wrap synchronous Supabase calls in `asyncio.get_running_loop().run_in_executor(None, ...)` when used inside asynchronous functions, and utilize in-memory caching to reduce the frequency of these calls entirely.
