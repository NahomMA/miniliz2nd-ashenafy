---
name: flask-endpoint
description: Add or change a Flask API endpoint, model or auth code in back-end/app, porting patterns from prev_projects/csis-web. Use for any route, JWT auth, SQLite model, error handling or backend test work.
---

# Flask endpoint

## Layout (already built; extend, do not restructure)
```
back-end/
  wsgi.py                  app = create_app()
  app/__init__.py          create_app(settings): extensions, blueprints, error handlers, create_all, demo seed
  app/config.py            Settings (frozen dataclass, from_env)
  app/errors.py            ApiError(message, status_code, code, extra_data), ApiError.invalid(field, msg), handlers
  app/security.py          argon2 hashing, TokenService (JWT HS256, sub/iat/exp)
  app/auth.py              @authentication_required, passes `auth_user` as first argument (csis-web contract)
  app/models.py            db (Flask-SQLAlchemy 3, SQLAlchemy 2 typed models), User, Assessment
  app/schemas.py           request dataclasses with `from_request()`, `json_body(*required_fields)`
  app/routes/auth.py       /auth/register, /auth/login, /auth/me
  app/routes/calculator.py /calculator/assess
  app/routes/assessments.py /assessments (start, chat, history, detail)
  app/services/            calculator_gateway.py (MCP)
  app/ai/                  chat layer (see the bedrock-chat skill)
  tests/                   conftest.py (app, client, auth fixtures), test_api.py
```
Shared services live in `app.extensions`: `settings`, `tokens`, `calculator`, `chat`.

## Reference only
The csis-web backend under the previous-projects folder shows the earlier approach. Write fresh code in the style
above; do not paste from it.

## Rules
1. One blueprint per file, registered in `_register_routes`. `@bp.post` / `@bp.get` goes above `@authentication_required` (route outermost).
2. Protected handlers receive the user: `def handler(auth_user, ...)`. Every query on user data filters by `auth_user.id`; another user's record is a 404.
3. Errors: `raise ApiError("message", 400, "code", extra_data)` or `ApiError.invalid(field, "message")`. Never return HTML or a bare string. Shape: `{"error": {"message", "code", ...extra_data}}`.
4. Success shape: plain JSON object, lists wrapped as `{"items": [...]}`.
5. Parse the body with a dataclass in `schemas.py` (`X.from_request()`); handlers contain no validation code.
6. Passwords: argon2 only, never logged or returned. Login failure is identical for wrong email and wrong password.
7. Config only through `Settings`. A `SECRET_KEY` under 32 chars fails at startup; a missing key is allowed in development only (temporary key, warning).
8. SQLite + Flask-SQLAlchemy, typed `Mapped[...]` columns, `db.create_all()` at startup. No Alembic.
9. CORS: bearer header only, no cookies.
10. Update `docs/api.md` and `docs/postman_collection.json` in the same change.

## Test for every endpoint
`tests/test_api.py` (or `test_<area>.py`) using the `client`, `auth` and `script` (fake model turns) fixtures: one success case,
one 401 without token, one 400 validation case. Run `pytest -q` before reporting done.

## Done when
`pytest -q` passes, and a curl of the new endpoint against the running server returns the documented shape.
