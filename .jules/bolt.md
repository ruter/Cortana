## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2023-10-24 - Caching Database Queries in Async Tools
**Learning:** Synchronous Supabase database calls inside frequent async functions (like ensure_user_exists) block the event loop and cause redundant DB lookups. Caching known user IDs and wrapping the DB calls in run_in_executor significantly reduces latency.
**Action:** Always wrap synchronous DB calls in run_in_executor when used in async functions and use in-memory caches like global sets to skip redundant synchronous database lookups.
