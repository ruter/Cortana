## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2024-04-02 - Redundant Caching Invalidations
**Learning:** When using transient in-memory cache validation fields like `_last_summary` that are not serialized in standard dictionary formats, standard deserialization will default it to `None`. This means the cache validation `_last_summary != (compact_summary, model)` will "miss" on the first access after loading from storage, naturally reconstructing the cache value making explicit serialization of the memoized field itself (`summary_tokens`) technically redundant but a safe and harmless practice for transient caches.
**Action:** When implementing transient cache memoizations, avoid polluting the persistent data stores with cache fields unless necessary. A transient cache invalidation failure safely defaults to recalculation.
