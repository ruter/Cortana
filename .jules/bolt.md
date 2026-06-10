## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-02-19 - Supabase Synchronous Client Event Loop Blocking
**Learning:** The Supabase Python client's `execute()` method is synchronous by default. When called directly inside asynchronous functions (like tool handlers), it blocks the main asyncio event loop, halting all concurrent operations.
**Action:** Always wrap synchronous Supabase database calls in a separate synchronous helper function and invoke them using `asyncio.get_running_loop().run_in_executor()` within async application code to prevent event loop blocking. Combine this with in-memory caching to bypass redundant network calls entirely where possible.
