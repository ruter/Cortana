## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2026-05-28 - Caching Internal State Serialization
**Learning:** When persisting cache state (like ), saving the cached value without its invalidation state (like ) defeats the purpose, as the next load will force recalculation because the invalidation state defaults to None. However, it's safer not to persist the derived metric at all and calculate it lazily, avoiding stale cache issues.
**Action:** Only persist internal cache-invalidation fields if all required contextual data (e.g. model name) is available, otherwise allow derived metric to default to None and recalculate lazily upon load.

## 2025-02-19 - Caching Internal State Serialization
**Learning:** When persisting cache state (like `summary_tokens`), saving the cached value without its invalidation state (like `_last_summary`) defeats the purpose, as the next load will force recalculation because the invalidation state defaults to None. However, it's safer not to persist the derived metric at all and calculate it lazily, avoiding stale cache issues.
**Action:** Only persist internal cache-invalidation fields if all required contextual data (e.g. model name) is available, otherwise allow derived metric to default to None and recalculate lazily upon load.
