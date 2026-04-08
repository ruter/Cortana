## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Internal Cache Invalidation for Derived Data
**Learning:** When caching derived data (like token counts for static strings such as `compact_summary` in `ConversationState`), manual external state synchronization is brittle. Additionally, when persisting this data via serialization, internal cache-invalidation fields (like `_last_summary`) may not have access to full contextual data (like the model name) upon deserialization.
**Action:** Implement automated cache invalidation logic internally within the caching class/method (e.g., storing a tuple of `(summary, model)` in `_last_summary` and checking it in `calculate_tokens`). During deserialization, allow internal invalidation fields to default to `None` so they recalculate lazily, safely ensuring backward compatibility and correctness without throwing errors.
