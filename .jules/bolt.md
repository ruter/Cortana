## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2024-06-18 - [Optimize DB Calls]
**Learning:** [Synchronous database calls in `src/tools.py` can block the `asyncio` event loop and execute repetitively for every user-related action.]
**Action:** [Use an in-memory cache to skip redundant checks and wrap network-bound operations with `asyncio.get_running_loop().run_in_executor()` to maximize async performance.]
