## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2024-06-03 - [Optimize Token Counting in ConversationCache]
**Learning:** Found that recounting tokens for identical `compact_summary` strings in `ConversationState.calculate_tokens` on every new message addition caused unnecessary overhead for long conversations.
**Action:** When caching derived data like token counts for static strings, implement automated cache invalidation logic internally within the caching class/method rather than recalculating it on every call.
