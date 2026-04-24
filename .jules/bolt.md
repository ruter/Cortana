## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-02-19 - Supabase Sync DB Calls in Async Context
**Learning:** The `supabase` Python client's `.execute()` method is synchronous. When called directly within `async def` application code (like `ensure_user_exists`), it blocks the entire `asyncio` event loop while waiting for the network round-trip.
**Action:** Always extract synchronous database calls (or external API calls) in async code into an internal def and use `await asyncio.get_running_loop().run_in_executor(None, fn)` to offload them to a thread pool, preventing event loop blocking. Additionally, use an in-memory cache (`set` or `dict`) to bypass repeated database lookups for known states (like "user exists") when safe.
