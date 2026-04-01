## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2026-04-01 - Redundant Synchronous Database Lookups
**Learning:** In highly transactional bot flows, repeatedly executing synchronous database queries (like Supabase `.execute()` for ensuring user existence) creates significant event loop blocking.
**Action:** Introduce simple in-memory global caches (like `set`) to short-circuit redundant checks, and ensure any necessary synchronous database checks are wrapped in `asyncio.get_running_loop().run_in_executor()` to prevent blocking.
