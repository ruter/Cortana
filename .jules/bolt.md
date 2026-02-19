## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Granular Locking in Async Caches
**Learning:** Moving file I/O out of a global lock in an async cache requires strict versioning (`persisted_version` vs `current_version`) to prevent race conditions where an older state overwrite a newer one. A per-user/per-item lock is essential to serialize writes for the same item.
**Action:** When optimizing locks, always implement a snapshot+version check pattern if the data is mutable and operations are asynchronous.
