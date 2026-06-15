## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-23 - Event Loop Blocking with Synchronous DB Clients
**Learning:** The Supabase Python client's `execute()` method is synchronous. When called repeatedly inside async code paths (like checking if a user exists on every tool call), it creates a major performance bottleneck by blocking the asyncio event loop.
**Action:** Introduce simple in-memory caching (like a `set` for known IDs) to skip redundant checks, and always wrap unavoidable synchronous database calls in `asyncio.get_running_loop().run_in_executor(None, ...)` to keep the event loop free.
