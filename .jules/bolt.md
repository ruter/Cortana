## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2024-04-19 - Synchronous Database Client Blocks Event Loop
**Learning:** The Supabase Python client's `.execute()` method is fundamentally synchronous. When called repeatedly inside an `async def` tool (like `ensure_user_exists`), it blocks the asyncio event loop. Using an in-memory global `set` cache is a very low-effort, safe, and massive performance win for operations like "ensure exists" that shouldn't change status mid-session.
**Action:** When working with the Supabase Python client in async environments, always consider caching read-heavy or initialization queries in-memory to prevent event loop blocking.
