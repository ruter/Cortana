## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Supabase Synchronous Client Blocking Event Loop
**Learning:** The Supabase Python client's `.execute()` method is synchronous by default. When called inside asynchronous functions (like tool endpoints), it can block the asyncio event loop and degrade overall performance, especially for frequent checks like ensuring user existence.
**Action:** Move synchronous database calls to helper functions and wrap them in `asyncio.get_running_loop().run_in_executor()` to prevent blocking the event loop. Combine this with in-memory caching (e.g., using a `set`) for repetitive queries to completely eliminate redundant network requests.
