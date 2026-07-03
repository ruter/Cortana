## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Supabase Synchronous Blockers
**Learning:** Supabase Python client's `execute()` method is synchronous. When called repeatedly inside async code (like `ensure_user_exists`), it blocks the asyncio event loop.
**Action:** Use an in-memory cache (like `_known_users` set) to skip redundant synchronous database lookups during repetitive bot operations, and use `asyncio.get_running_loop().run_in_executor()` to offload the initial synchronous lookup/insert. Only update the cache on successful DB operations or expected errors (like 'duplicate') to prevent cache poisoning.
