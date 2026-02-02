## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Conversation Summary Token Recalculation
**Learning:** `ConversationCache` was recalculating tokens for `compact_summary` (which can be large) on every request, causing unnecessary CPU overhead. Caching this value yielded significant savings.
**Action:** When working with expensive properties (like token counts) on persistent objects, ensure they are cached and invalidated correctly upon change.
