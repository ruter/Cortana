## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-24 - Lock Granularity Impact
**Learning:** A single global lock protecting both cache structure and file persistence serialized all user requests, causing a 10-user concurrent load to take ~2.5s (serial I/O). Switching to per-user locking reduced this to ~0.37s (parallel I/O).
**Action:** Always audit lock scope. Use fine-grained locks for independent resources (like user sessions) to enable parallelism, especially when I/O is involved.
