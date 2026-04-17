## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2026-04-17 - Caching Redundant Database Lookups
**Learning:** Functions that frequently hit the database simply to verify existence (like `ensure_user_exists`) can create substantial latency in transaction-heavy paths. The Supabase Python client's `execute()` method is also synchronous by default, which can block the event loop in async contexts.
**Action:** Use an in-memory `set` to track known entities. This provides a lightning-fast O(1) local cache to skip redundant network I/O, dramatically speeding up subsequent validations for the same entity.
