TODO
====

- [x] Fix `AuthService._generate_session_token` to use UTC datetimes for JWT claims.
- [x] Re-run `python -m py_compile services\\auth_service.py` after the token fix.

- [x] Update `LoginLogDAO` to use the `username` column everywhere (create, queries, docs).
- [x] Adjust `AuthService`/session logging to pass usernames instead of emails and remove stale references.
- [x] Re-run `python -m compileall .` to ensure no syntax errors after the refactor.
- [x] Add a `update_player` helper in `PlayerService` that wraps generic DAO updates.
- [x] Switch `GameServer.save_game` to call the new service helper and surface failures.
- [x] Re-run `python -m compileall .` to make sure the save flow change has no syntax errors.
- [x] Fix `handle_token_verify` to use `PlayerService.get_player` and return the correct username field.
- [x] Ensure token verification updates `GameState` auth fields so auto-login works.
- [x] Re-run `python -m compileall .` after the session restore fix.
