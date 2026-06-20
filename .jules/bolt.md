## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Synchronous Database Operations and Caching
**Learning:** Supabase Python client's `execute()` method is synchronous. If executed repeatedly within async functions (e.g. `ensure_user_exists`), it can block the event loop. Furthermore, repeated existence checks are a common performance bottleneck across operations.
**Action:** Offload synchronous Supabase `execute()` calls to thread pools via `asyncio.get_running_loop().run_in_executor`, and use an in-memory cache like `_known_users = set()` to avoid redundant sync database operations entirely.
