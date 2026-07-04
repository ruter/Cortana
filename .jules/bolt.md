## 2025-02-19 - Dependency Management in Optimization
**Learning:** Even if a library is in `requirements.txt`, using `run_in_executor` with the standard library is preferred by some reviewers for file I/O to minimize dependencies and maintain simplicity.
**Action:** Prefer standard library solutions (like `run_in_executor`) for async I/O over external libraries unless the external library offers significant additional value.

## 2025-02-19 - Caching Synchronous DB Lookups in Async Context
**Learning:** In highly concurrent async environments, synchronous database lookups (like checking if a user exists) block the event loop, causing significant latency for other operations. Simply offloading via `run_in_executor` helps, but the operation is frequently repeated and mostly idempotent.
**Action:** When a static database validation rule applies globally across user sessions (like `ensure_user_exists`), combine `run_in_executor` with a local in-memory cache (like `set`) to immediately return for subsequent operations and completely bypass the IO/thread-pool overhead, ensuring the async event loop stays completely clear.
