## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-23 - Optimistic Locking in Async I/O
**Learning:** When moving I/O out of a global lock to improve concurrency, simple `await` is insufficient. Race conditions can occur where a slower, older write overwrites a newer one.
**Action:** Implement optimistic locking using a `version` counter and a per-resource lock. Check `version <= persisted_version` before writing to ensure only newer data persists.
