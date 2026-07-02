## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-07-02 - Supabase Blocking Calls
**Learning:** Synchronous Supabase `.execute()` calls block the main asyncio event loop, causing severe latency during routine tool executions.
**Action:** Extract synchronous operations into dedicated helper functions and offload them using `asyncio.get_running_loop().run_in_executor`. Implement global in-memory caching to skip redundant database validations and eliminate recurring overhead.
