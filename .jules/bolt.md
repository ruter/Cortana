## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.
## 2024-05-18 - [Token Count Memoization]
**Learning:** Token counting operations using `litellm` inside tight loops or high-frequency additions (like `calculate_tokens` in `ConversationCache`) can introduce significant synchronous CPU overhead, blocking the asyncio event loop.
**Action:** When a base string (like `compact_summary`) is relatively static, memoize the token count within the state class using automated invalidation (checking if the base string or model changed) rather than recalculating it on every invocation.
