## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2026-06-16 - Synchronous Database Client Bottlenecks
**Learning:** In async functions, the Supabase Python client's `execute()` method runs synchronously and will block the asyncio event loop. Repeatedly making synchronous database queries (like checking if a user exists via `ensure_user_exists` inside tool functions) introduces significant performance overhead and blocks parallel bot operations.
**Action:** Always extract synchronous database calls (like Supabase `.execute()`) to synchronous helper functions and offload them using `asyncio.get_running_loop().run_in_executor`. Supplement repetitive queries with simple in-memory caches (like `set()` for known users) populated conditionally on successful execution.
