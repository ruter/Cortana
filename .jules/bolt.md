## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2024-05-14 - Cache Token Counts for Repetitive Static Strings
**Learning:** Relying on implicit manual external state synchronization for cache invalidation (e.g. resetting to 0 from an external caller) is brittle. String comparisons and hashing are safer invalidation triggers.
**Action:** Implement automated cache invalidation logic inside the caching method or property setter rather than manually calling invalidation alongside the update logic.
