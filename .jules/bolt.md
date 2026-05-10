## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-03-01 - Optimizing Supabase Database Execution
**Learning:** The Supabase Python client `execute()` method is synchronous and can block the `asyncio` event loop when called frequently within `async def` methods, especially during repetitive tasks like user checks. Caching results in memory using a simple global `set` drastically reduces overhead.
**Action:** Offload synchronous network calls using `run_in_executor` and cache repetitive synchronous database lookups in a global `set` when acceptable.
