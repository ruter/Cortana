## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-02-19 - Supabase Sync Client Blocking Async Loop
**Learning:** The Supabase Python client's `.execute()` method is fundamentally synchronous. When used inside an `async def` function (like `ensure_user_exists` or other tool handlers in `src/tools.py`), it blocks the entire asyncio event loop, causing severe latency for all concurrent requests.
**Action:** When working with the Supabase python client in this async codebase, either offload the query to a separate thread via `asyncio.get_running_loop().run_in_executor(None, sync_func)` or wrap it with an async alternative if the client supports it. Furthermore, redundant db calls can be avoided with an in-memory short-circuit set.
