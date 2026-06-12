## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-02-19 - Unblocking Async Event Loops
**Learning:** The Supabase Python client's `execute()` method is synchronous. Calling it directly inside async functions like `ensure_user_exists` blocks the main asyncio event loop, causing severe latency for all concurrent requests.
**Action:** When making synchronous network/DB calls in async functions, always use `asyncio.get_running_loop().run_in_executor(None, sync_func, *args)` to offload the blocking work to a thread pool. Additionally, caching results in memory (like `_known_users` set) drastically reduces these redundant DB round-trips.
