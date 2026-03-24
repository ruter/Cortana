## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Caching Synchronous Operations in Async Context
**Learning:** The Supabase client performs synchronous operations that can block the event loop. In operations executed frequently (like checking if a user exists), these blockages severely reduce overall concurrency and throughput.
**Action:** Implement memory caching (like a global `set`) to bypass redundant checks and offload unavoidable synchronous calls using `asyncio.get_running_loop().run_in_executor()`.
