## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-05-23 - Database Lookup Bottlenecks in Repetitive Tool Calls
**Learning:** Repetitive setup functions like `ensure_user_exists` that execute synchronous database queries can create significant bottlenecks when tools are used frequently, blocking the event loop and causing redundant network latency.
**Action:** Use an in-memory set (like `_known_users`) to skip DB lookups for already-verified entries, and offload the initial synchronous lookup to a background thread (`run_in_executor`) to avoid event loop blocking.
