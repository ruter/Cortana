## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-25 - Database Query Optimization
**Learning:** Frequent existence checks (`ensure_user_exists`) backed by database queries can become a significant bottleneck, especially when blocking the event loop. In-memory caching for immutable or append-only data (like user existence) is a highly effective optimization.
**Action:** Always check for redundant database queries in frequently called helper functions and consider local caching for stable data.
