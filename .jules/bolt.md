## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-02-19 - Supabase Sync/Async Impedance Mismatch
**Learning:** The Supabase Python client's `.execute()` method is synchronous by default. When called inside standard application `async def` methods (like tools or helpers), it completely blocks the asyncio event loop, causing severe latency for concurrent requests.
**Action:** When working with synchronous database clients in this async codebase, either offload the query to `loop.run_in_executor()` or cache the result aggressively in memory (e.g., using a module-level `set()`) to prevent event loop blocking.
