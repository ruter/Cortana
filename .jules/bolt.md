## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-02-19 - Supabase Sync/Async Impedance Mismatch
**Learning:** The Supabase Python client's `.execute()` method is synchronous by default. When called inside an `async def` function like `ensure_user_exists` in `src/tools.py`, it blocks the entire `asyncio` event loop while waiting for network I/O, negating the benefits of asynchronous concurrency for the whole application.
**Action:** Always wrap synchronous database calls (like Supabase `.execute()`) in `asyncio.get_running_loop().run_in_executor()` when they must be called from within an async context to prevent event loop blocking. Consider adding a lightweight in-memory cache layer (`set` or `dict`) to bypass the database call entirely for high-frequency "ensure exists" patterns.
