## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-02-19 - Supabase Synchronous I/O in Async Functions
**Learning:** The Supabase Python client's `execute()` method is synchronous. When called repeatedly inside an asynchronous function (like `ensure_user_exists` checked on every tool call), it creates a significant performance bottleneck by blocking the asyncio event loop.
**Action:** Use an in-memory cache to skip redundant database checks, and extract necessary `execute()` calls into a synchronous helper function invoked via `asyncio.get_running_loop().run_in_executor()` to preserve asynchronous performance.
