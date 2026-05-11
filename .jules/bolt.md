## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Supabase Synchronous Blockers
**Learning:** The Supabase Python client's `.execute()` method is synchronous by default. When called inside standard `async def` tool functions (like `ensure_user_exists`), it blocks the entire asyncio event loop, severely impacting concurrent performance.
**Action:** Extract synchronous Supabase calls into separate synchronous helper functions and execute them via `asyncio.get_running_loop().run_in_executor()` to maintain high throughput in async environments.
