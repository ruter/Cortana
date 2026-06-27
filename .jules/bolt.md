## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-23 - Asyncio Event Loop Blocking with Supabase
**Learning:** The Supabase Python client's `execute()` method is synchronous by default. When called inside asynchronous functions, it can block the event loop, causing performance bottlenecks, especially in repetitive operations like `ensure_user_exists`.
**Action:** Extract synchronous Supabase database calls into separate synchronous helper functions and invoke them using `asyncio.get_running_loop().run_in_executor()`. Implement in-memory caches to prevent redundant synchronous database queries during bot operations.
