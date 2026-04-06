## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-02-19 - Supabase Sync Blocking Async Loop
**Learning:** The Supabase Python client's `.execute()` method is synchronous. If called inside an async route or tool (like `ensure_user_exists`), it blocks the entire event loop, severely degrading the performance of the async application.
**Action:** Always wrap synchronous database calls (like Supabase `.execute()`) in `asyncio.get_running_loop().run_in_executor()` when they are used inside `async` functions to prevent blocking the event loop. In addition, an in-memory cache `_known_users` is very effective at mitigating this exact bottleneck.
