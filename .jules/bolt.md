## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-02-19 - Caching Token Count Internally
**Learning:** Manual cache invalidation of `summary_tokens` by relying on external operations like resetting `_last_summary` elsewhere in the code is fragile and error-prone.
**Action:** When caching derived data (like token counts for static strings), implement automated cache invalidation logic internally within the caching class/method (e.g., by comparing a tuple of `(compact_summary, model)`) to avoid brittle external state synchronization.
