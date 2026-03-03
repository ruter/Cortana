## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Internal Automated Cache Invalidation
**Learning:** When caching derived data (like token counts for static strings), implement automated cache invalidation logic internally within the caching class/method (e.g., by checking if the base string has changed) rather than relying on external manual state synchronization, which is brittle.
**Action:** Use an internal "last known value" field (like `_last_summary`) to compare against the source data when updating cache derivations automatically.
