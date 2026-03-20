## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2026-03-20 - Supabase execute() Blocking Event Loop
**Learning:** The Supabase Python client's `execute()` method is synchronous by default. When called inside asynchronous functions (like `ensure_user_exists`), it blocks the async event loop, reducing application throughput and responsiveness.
**Action:** Always wrap synchronous database calls (like Supabase's `execute()`) in `asyncio.get_running_loop().run_in_executor(None, sync_func, *args)` when inside an async function to maintain non-blocking behavior.
