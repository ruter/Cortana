## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Synchronous Database Client Optimization
**Learning:** In asynchronous applications where synchronous database clients (like Supabase Python client's default `.execute()`) are heavily used within tight event loops (such as repetitive `ensure_user_exists` calls), it creates a major performance bottleneck by blocking the asyncio loop.
**Action:** When working with synchronous I/O operations inside async functions, always use `asyncio.get_running_loop().run_in_executor(None, func, *args)` to offload the work to a separate thread. Additionally, combine this with an in-memory cache (like a global `set`) to bypass the DB lookup entirely for known entities.
