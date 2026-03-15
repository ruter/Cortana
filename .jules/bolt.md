## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2026-03-15 - Blocking Event Loop with Synchronous Supabase Calls
**Learning:** The Supabase Python client's `execute()` method is synchronous by default. When called inside asynchronous functions without offloading, it can block the event loop. In operations that happen repeatedly (like checking if a user exists before every tool call), this creates a significant performance bottleneck.
**Action:** Use an in-memory cache (like a Python `set`) to store validation results that don't change often, bypassing the synchronous database call entirely after the first time.
