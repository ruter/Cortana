## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Cache Pattern for Redundant DB Checks
**Learning:** `ensure_user_exists` is called on multiple tool operations (`add_todo`, `add_calendar_event`, etc). Checking user existence synchronously with Supabase for every tool execution introduces redundant latency and blocks the async loop. A simple in-memory `set` is highly effective and thread-safe for tracking users who have already been validated/created.
**Action:** When a synchronous database check is repeatedly invoked on the same entity during the lifecycle of an application, use a localized in-memory cache to bypass the check, while offloading the initial check to `run_in_executor`.
