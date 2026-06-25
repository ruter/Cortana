## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Caching Repetitive DB Queries
**Learning:** Repetitive synchronous database queries (like `ensure_user_exists` checked on every operation) block the event loop and degrade performance. A simple in-memory `set` can eliminate almost all of these calls.
**Action:** Use an in-memory cache (like a global `set`) to skip redundant synchronous database lookups, and offload the actual DB writes to a thread pool via `run_in_executor` to avoid blocking the event loop.
