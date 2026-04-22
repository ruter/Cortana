## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2024-05-20 - [Redundant DB lookups in ensure_user_exists]
**Learning:** ensure_user_exists is called repeatedly before every database operation (add_todo, etc) doing a synchronous Supabase call that blocks the async event loop and performs redundant lookups for users we already know exist.
**Action:** Use an in-memory caching pattern (like a global `set` called `_known_users`) to skip redundant database lookups for users we've already ensured exist in the current process. Also execute synchronous Supabase calls using run_in_executor to avoid blocking the event loop.
