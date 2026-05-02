## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Supabase Sync Operations Blocking Event Loop
**Learning:** The Supabase Python client's `execute()` method is synchronous by default. When called directly inside asynchronous functions (like `ensure_user_exists`), it can block the asyncio event loop, causing performance bottlenecks, especially if called frequently (like checking user existence on every action).
**Action:** Extract synchronous Supabase calls into a separate helper function and invoke them using `asyncio.get_running_loop().run_in_executor()`. Additionally, use an in-memory cache (like a `set` for known users) to skip redundant synchronous lookups altogether during repetitive operations.
