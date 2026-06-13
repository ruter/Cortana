## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2024-06-13 - Sync Supabase Calls and Async Execution
**Learning:** By default, the Supabase python client's `execute()` method is synchronous and can block the event loop in async applications, especially when executed repetitively on hot paths like checking user existence before every tool call.
**Action:** Implement an in-memory caching layer (`set` or `dict`) to bypass repeated checks, and wrap unavoidable synchronous database calls in `asyncio.get_running_loop().run_in_executor(None, sync_func)` to prevent event loop blocking.
