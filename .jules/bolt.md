## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2024-05-18 - Database Call Optimization
**Learning:** Repetitive database calls within the same session or for the same resource, such as `ensure_user_exists` checking if a user exists on every transaction tool call, create measurable latency bottlenecks.
**Action:** Implement in-memory caches (like `_known_user_ids = set()`) to track verified existing records and immediately return, preventing redundant database queries across multiple tool invocations for the same user.
