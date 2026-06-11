## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Standard Library Preference for Caching
**Learning:** External dependencies like `cachetools` should not be introduced without explicit approval, as they can cause immediate application crashes if unmanaged. The standard library provides adequate tools (e.g., `collections.OrderedDict`) for implementing bounded caches like LRU without new dependencies.
**Action:** Always prefer standard library implementations (like `OrderedDict` for LRU caches) over third-party packages to ensure code reliability and avoid dependency management issues, unless specifically requested or approved.
