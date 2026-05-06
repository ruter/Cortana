## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Caching Derived Token Metrics
**Learning:** The token counting operation relying on LiteLLM is blocking and CPU-intensive. Re-evaluating the token count of stable text strings (like `compact_summary` in `ConversationState`) repetitively can degrade performance unnecessarily in high-throughput areas like caching history retrieval.
**Action:** When working with derived metrics that are expensive to compute (like token counts for large texts), cache the result internally within the state object using a fast-validation invalidation check (e.g. comparing the source text string and model). Ensure robust backward compatibility by defaulting cached metrics missing in legacy persistence.
