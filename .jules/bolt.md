## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-02-19 - Cache and Async Offloading for Database Existence Checks
**Learning:** Checking for user existence on almost every database transaction causes unnecessary latency and event loop blocking (if the DB client is synchronous by default, like `supabase.Client.execute()`).
**Action:** Use a fast in-memory `set` cache (`_known_users`) to track known entities combined with `asyncio.get_running_loop().run_in_executor` to offload the synchronous database calls during cache misses, avoiding blocking the main thread while preventing redundant remote queries entirely.
