## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2026-04-23 - Useless state persistence overhead
**Learning:** Serializing the output of a cached operation without serializing its invalidation key results in useless state persistence overhead, as the cache will always be cold on load.
**Action:** Only serialize cache outputs if their corresponding invalidation keys or states are also serialized and verified on load, otherwise recalculate lazily.
