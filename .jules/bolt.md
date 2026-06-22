## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Supabase Synchronous Blockers
**Learning:** The Supabase Python client's `.execute()` method is fundamentally synchronous. When used naively inside high-frequency `async def` methods (like verifying user existence before every tool call), it creates severe I/O bottlenecks that block the entire `asyncio` event loop.
**Action:** When working with Supabase calls in a highly concurrent `asyncio` environment, always either wrap them in `loop.run_in_executor()` or implement strong in-memory caching mechanisms (like an unbounded `set` for ID validation) to completely bypass the database on subsequent calls.
