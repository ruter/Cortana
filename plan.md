1. Add an in-memory cache for `ensure_user_exists` in `src/tools.py`.
   - I'll define a global set `_known_users`.
   - I'll modify `ensure_user_exists` to first check `_known_users`.
   - I'll use `run_in_executor` to perform the database check and insertion asynchronously to prevent blocking the event loop.
   - I'll add the `user_id` to `_known_users` upon successful execution or when a duplicate error confirms the user already exists.
2. Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
3. Submit the change with `submit` using title '⚡ Bolt: Cache known users in ensure_user_exists'.
