## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-24 - Database Overheads in Async Contexts
**Learning:** The Supabase Python client's `execute()` method is synchronous. Performing repetitive checks like `ensure_user_exists` inline within async bot commands blocks the asyncio event loop and adds unnecessary latency.
**Action:** Implement an in-memory cache (like a global `set` of `_known_users`) to avoid redundant DB lookups for operations known to be idempotent over short periods, and offload any remaining necessary synchronous DB calls to `run_in_executor`.
