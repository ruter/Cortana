## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-02-19 - Cache Poisoning Risk in Async Database Execution
**Learning:** When refactoring a synchronous database call to use `run_in_executor` and introducing an in-memory cache to skip redundant checks, catching all exceptions and blindly updating the cache on the main thread causes "cache poisoning". If the database call fails transiently, the cache will erroneously register the task as complete, permanently breaking subsequent attempts in that session.
**Action:** When implementing local caching for database checks, the cache update must occur **within** the `run_in_executor` thread pool *after* the database operation successfully completes, and exceptions must be correctly handled to prevent false positives in the cache state.
