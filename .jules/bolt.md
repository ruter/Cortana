## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-04-20 - Non-Blocking DB Calls & In-Memory Caching in Async Functions
**Learning:** Using synchronous database client methods (like Supabase's execute()) directly inside an async event loop blocks the event loop and slows down the application. We can optimize repetitive DB lookups (like user existence checks) by adding an in-memory cache and offloading the necessary DB writes to `asyncio.get_running_loop().run_in_executor()` to keep the application responsive.
**Action:** Identify repetitive synchronous DB checks within async functions. Add an in-memory `set` or `dict` to cache results, and use `run_in_executor` to offload the synchronous DB network bound calls to prevent event loop blocking.

## 2025-04-20 - Ensure Error States Are Handled When Caching
**Learning:** When refactoring functions to use a cache (like tracking `_known_users`), ensure that errors during the initial check aren't silently swallowed. If an exception prevents the operation from succeeding (e.g., database is down), caching the user unconditionally will create a corrupted state that persists until the app restarts.
**Action:** When caching, return a success boolean from the underlying operation and only update the cache if the operation succeeded or failed in an expected way (e.g., duplicate constraint).
