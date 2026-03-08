## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2024-05-24 - Efficient Token Count Caching for Static Summaries
**Learning:** When calculating total conversation tokens, repeatedly counting tokens for the static `compact_summary` wastes CPU cycles. Since `compact_summary` only changes during compaction, its token count can be safely cached. However, manual external cache invalidation is brittle.
**Action:** Introduced an internal cache invalidation mechanism within `ConversationState` using a `_last_summary` tuple field `(summary_text, model_name)`. This ensures `summary_tokens` is only recalculated when the summary content or the target LLM model changes, optimizing performance during repeated `get_history` calls while maintaining correctness automatically.
