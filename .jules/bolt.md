## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Caching Synchronous DB Queries
**Learning:** The Supabase Python client's `execute()` method is synchronous by default. When called repetitively inside asynchronous functions (like `ensure_user_exists`), it can block the event loop and add significant database latency.
**Action:** Use an in-memory caching pattern (like a global `set`) to skip redundant database lookups, and offload the actual database operations using `asyncio.get_running_loop().run_in_executor()` to prevent blocking the async event loop.
