## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-02-19 - Threading for Synchronous Libraries
**Learning:** Using `loop.run_in_executor` to offload synchronous external library calls (like Supabase `execute()`) is a powerful pattern to prevent blocking the async event loop without adding new dependencies.
**Action:** When identifying performance bottlenecks in async functions, check for synchronous I/O or library calls and offload them to a thread pool if an async alternative is unavailable.
