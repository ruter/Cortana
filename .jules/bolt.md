## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-03-05 - Optimize LLM Conversation Token Counting & Persistence
**Learning:** `ConversationState.calculate_tokens` recalculates the token limit of `compact_summary` on every message add, causing unnecessary CPU overhead. Moreover, persisting cache to disk with `indent=2` creates larger, slower I/O operations than necessary.
**Action:** Cache static token calculations (like `summary_tokens`) on the state object using an internal tuple invalidation check (`_last_summary`), and always use unindented JSON for internal state persistence.
