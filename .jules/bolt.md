## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-02-19 - Supabase Sync DB Operations
**Learning:** By default, Supabase Python client `execute()` commands are synchronous and will block the asyncio event loop if not offloaded. Additionally, combining an offloaded DB task with a simple in-memory cache effectively eliminates redundant I/O bottlenecks in highly repetitive workflows.
**Action:** Use an in-memory structure (like a `set`) to short-circuit redundant checks, and always wrap the actual Supabase database call in `asyncio.get_running_loop().run_in_executor` to avoid freezing async routines.
