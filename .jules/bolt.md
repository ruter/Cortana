## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Skipping Redundant DB Lookups
**Learning:** Repetitive database queries for static assertions (like `ensure_user_exists` across many tools) cause unnecessary latency and block the event loop if the DB calls are synchronous and not offloaded.
**Action:** Implement an in-memory cache (e.g., a global `set` of known users) to skip redundant operations, and extract any synchronous DB calls to a helper executed via `run_in_executor` to prevent blocking the async loop.
