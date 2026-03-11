## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2024-05-18 - [Add In-Memory Cache for Redundant Database Lookups]
**Learning:** `ensure_user_exists` was performing a synchronous database check for every user action (like adding a todo or checking availability), which blocked the main thread and introduced unnecessary latency.
**Action:** Adding a simple in-memory `set` cache (`_known_users`) eliminates O(N) redundant synchronous Supabase queries for active users, demonstrating that even lightweight operations should be cached if called frequently per-request.
