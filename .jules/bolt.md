## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2023-10-27 - Supabase Python Client Blocks Asyncio Event Loop
**Learning:** The Supabase Python client's `.execute()` method is synchronous by default. When called inside an `async def` application function, it will block the entire `asyncio` event loop.
**Action:** When a synchronous Supabase call (or any blocking I/O) is required inside an async function, extract the blocking call into a synchronous helper and invoke it using `asyncio.get_running_loop().run_in_executor()`. Additionally, if the data can be cached (like `user_id` existence checks), implement an in-memory mechanism (like `_known_users: set`) to avoid the redundant call altogether.
