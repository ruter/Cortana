## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-03-05 - Synchronous DB calls in Async Event Loop
**Learning:** The Supabase Python client's `.execute()` method is synchronous. When called within an `async def` tool function (like `ensure_user_exists`), it blocks the entire `asyncio` event loop for the duration of the network request, degrading concurrent bot performance.
**Action:** Use `asyncio.get_running_loop().run_in_executor()` to offload synchronous network calls to a thread pool, preventing event loop blocking. Additionally, employ in-memory caches (like a `set` for known users) to completely skip redundant lookups when feasible.
