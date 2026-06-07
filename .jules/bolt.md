## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-02-19 - Synchronous Database Operations in Async Functions
**Learning:** The Supabase Python client's `execute()` method is synchronous. When called inside `async def` functions (like `ensure_user_exists`), it blocks the entire asyncio event loop, causing severe performance degradation for frequent bot operations.
**Action:** Always offload synchronous database operations to a thread pool using `asyncio.get_running_loop().run_in_executor` in this codebase. Additionally, use in-memory caching to bypass the database entirely for redundant lookups.
