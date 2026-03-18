## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Caching Supabase User Verification
**Learning:** Returning users will trigger `ensure_user_exists` multiple times in succession due to tool invocations. The Supabase Python client's synchronous `execute()` calls block the main asyncio event loop and introduce ~50-200ms latency per DB check.
**Action:** Use an in-memory caching mechanism like `_known_users = set()` combined with offloading DB calls using `run_in_executor` to dramatically reduce redundant DB queries and improve performance.
