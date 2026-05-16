## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-02-19 - Supabase Synchronous Client Blocking
**Learning:** The default Supabase Python client's `.execute()` method is synchronous. When called inside frequent async operations (like the transaction tools' repeated calls to `ensure_user_exists`), it blocks the asyncio event loop entirely, causing significant performance degradation for the bot.
**Action:** Always wrap Supabase `.execute()` calls in `run_in_executor` when executing them within an `async def` function, or cache the results in memory to avoid redundant database calls.
