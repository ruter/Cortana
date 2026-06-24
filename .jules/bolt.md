## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2025-02-19 - Supabase Sync execution & Caching
**Learning:** The Supabase Python client's `.execute()` method is fundamentally synchronous and blocks the asyncio event loop if called directly in async functions like `ensure_user_exists`. Offloading to `run_in_executor` effectively resolves this block. Furthermore, combining offloading with an in-memory cache for repeated idempotent checks dramatically reduces simulated network latency (from 0.25s for 5 calls to 0.05s).
**Action:** When working with the Supabase python client in `async` contexts, always wrap `.execute()` operations that do not have their own native `async` implementations in `asyncio.get_running_loop().run_in_executor`. Also implement global `set` caching for redundant existence checks.
