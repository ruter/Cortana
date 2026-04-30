## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-23 - Offloading Synchronous Supabase Calls
**Learning:** The default Supabase Python client is synchronous. In an `asyncio` application (like this Discord bot), calling `.execute()` directly blocks the main event loop, causing severe latency for all concurrent users, especially in frequently hit functions like `ensure_user_exists`.
**Action:** When using synchronous libraries in async applications, wrap the network/IO operations in a helper function and use `asyncio.get_running_loop().run_in_executor(None, sync_func, *args)` to offload the work to a background thread pool.
