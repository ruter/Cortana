## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - N+1 Queries & Event Loop Blocking in Supabase
**Learning:** The Supabase Python client's `execute()` method is synchronous by default. When called inside asynchronous functions, particularly helper functions like `ensure_user_exists` that run before many other database operations, it creates a dual performance bottleneck: it blocks the asyncio event loop and creates N+1 query patterns.
**Action:** Use an in-memory cache (like a global `set` for known IDs) to skip redundant synchronous lookups, and wrap the underlying synchronous `execute()` call in `asyncio.get_running_loop().run_in_executor()` to prevent it from blocking the event loop when a database call is necessary.
