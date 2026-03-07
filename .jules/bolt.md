## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Concurrent I/O state corruption during compaction
**Learning:** In a conversation caching system using asynchronous lock management alongside LLM summarization logic, setting the internal cache state using `recent_messages = state.messages[-keep_recent*2:]` completely loses all transient messages received while waiting for the network-bound `_generate_summary` LLM call. Also if compaction is concurrently requested it triggers multiple expensive LLM calls if there is no guard lock state field.
**Action:** When truncating cache history in concurrent environments, compute the slice based on exactly what was consumed (`state.messages = state.messages[num_summarized:]`) instead of what is remaining, and explicitly implement an `is_compacting` flag guard clause to skip repeated or redundant async tasks that can bottleneck performance or overwrite states.
