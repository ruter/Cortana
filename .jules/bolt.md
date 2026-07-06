## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Supabase Synchronous Event Loop Blocking
**Learning:** The Supabase Python client's `execute()` method is synchronous by default. When called inside asynchronous functions (like `ensure_user_exists`), it blocks the main asyncio event loop, causing severe latency degradation under load. Redundant calls for static entities (like checking user existence on every bot message) compound this issue.
**Action:** Introduced an in-memory `_known_users` cache to provide a fast path, completely avoiding the DB query for known entities. Offloaded the remaining synchronous Supabase `execute()` calls to `run_in_executor` to prevent blocking the event loop on cache misses. This pattern of in-memory caching combined with thread-pool offloading for synchronous clients is critical for maintaining responsiveness in this codebase's async architecture.
