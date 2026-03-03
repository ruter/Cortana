## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Dataclasses and Asyncio Locks
**Learning:** `asyncio.Lock` objects cannot be fields in a `dataclass` because they are not serializable and `dataclasses.asdict` fails. Also, initializing them in `__post_init__` is safer and cleaner.
**Action:** Always initialize `asyncio.Lock` and other non-data objects in `__post_init__` for dataclasses, and exclude them from logical data representation.

## 2025-02-19 - Concurrent List Modification
**Learning:** Overwriting a list with a slice (e.g., `state.messages = recent_messages`) during an async operation can lead to data loss if new items are appended concurrently.
**Action:** Use slicing to remove specific items from the head of the list (e.g., `state.messages = state.messages[n:]`) to preserve concurrent appends.
