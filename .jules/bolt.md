## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - In-Memory Caching for Redundant DB Lookups
**Learning:** Redundant database lookups (like checking if a user exists before every tool invocation) can become a significant performance bottleneck, especially when the database client's `execute()` method is synchronous and blocks the asyncio event loop.
**Action:** Introduce an in-memory caching pattern (e.g., a global `set`) to skip redundant checks. For the initial check, extract the blocking DB call into a synchronous helper and execute it via `asyncio.get_running_loop().run_in_executor()` to preserve asynchronous flow and ensure the cache is only updated upon successful execution or expected errors.
