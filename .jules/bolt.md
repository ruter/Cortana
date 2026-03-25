## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-03-01 - User existence cache and database call optimization
**Learning:** Checking for user existence in the database on every transaction tool call can be a significant bottleneck due to the synchronous nature of the database client, which could also block the event loop.
**Action:** Used a fast, global `_known_users` cache to bypass the database lookup entirely. For when a database call is necessary, offloaded it using `run_in_executor` to prevent blocking the event loop.
