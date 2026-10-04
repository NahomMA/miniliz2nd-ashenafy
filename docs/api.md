# API contract (draft v1)

Base URL: `EXPO_PUBLIC_API_URL` (HTTPS). All bodies are JSON.
Auth: `Authorization: Bearer <jwt>` on everything except `/health`, `/auth/register`, `/auth/login`.
Errors: `{"error": {"message": str, "code": str, "field"?: str}}` with status 400, 401, 404, 409 or 500.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | no | `{"ok": true}` |
| POST | `/auth/register` | no | create account |
| POST | `/auth/login` | no | get token |
| GET | `/auth/me` | yes | current user |
| POST | `/calculator/assess` | yes | calculate from a profile, no LLM; also used for what-if sliders |
| POST | `/assessments` | yes | start a conversation |
| POST | `/assessments/<id>/chat` | yes | send one message |
| GET | `/assessments` | yes | history list |
| GET | `/assessments/<id>` | yes | one saved assessment |

## Auth
`POST /auth/register` and `POST /auth/login`
- Request: `{"email": str, "password": str}` (register also takes `"name": str`; password min 8 chars)
- Response 200/201: `{"token": str, "user": {"id": int, "email": str, "name": str}}`
- Errors: 400 `validation`, 401 `invalid_credentials` (same message for wrong email or password), 409 `email_taken`

`GET /auth/me` returns `{"user": {...}}`. 401 `invalid_token` when missing or expired.

## Calculator
`POST /calculator/assess`
- Request: `{"profile": {...}}` (fields in `docs/calculator-spec.md`)
- Response 200: Assessment object
- Errors: 400 `validation` with `field` naming the bad input, 401 `invalid_token`

## Assessments
`POST /assessments`
- Request: `{}`
- Response 201: `{"id": int, "reply": str, "profile": null, "assessment": null, "done": false}`
  (`reply` is the assistant's greeting and first question)

`POST /assessments/<id>/chat`
- Request: `{"message": str}` (1 to 1000 chars)
- Response 200:
```json
{
  "reply": "Thanks, Maria. ...",
  "profile": null,
  "assessment": null,
  "done": false
}
```
- `profile` and `assessment` are null until the calculation has run. Then `profile` holds the collected answers,
  `assessment` is the Assessment object below and `done` is true. The chat stays open for follow-up questions after `done`.
- Errors: 400 `validation`, 404 `not_found` (also when the assessment belongs to another user)

What-if: send the changed profile to `POST /calculator/assess`. Nothing is saved.

`GET /assessments` returns `{"items": [{"id", "created_at", "total_need", "gap", "done"}]}`, newest first.

`GET /assessments/<id>` returns `{"id", "created_at", "profile", "assessment", "messages": [{"role", "text"}]}`.

## Assessment object
```json
{
  "total_need": 1633900,
  "resources": 80000,
  "gap": 1553900,
  "components": [
    {"key": "income", "label": "Income replacement", "amount": 1275000, "reason": "15 years of your $85,000 income, until your youngest turns 18."}
  ],
  "offsets": [
    {"key": "existing_coverage", "label": "Coverage you already have", "amount": 50000, "reason": "..."}
  ],
  "projection": {"years": [{"year": 0, "remaining_need": 1633900}], "suggested_term_years": 20},
  "comparison": {
    "term": {"fits_when": ["..."], "tradeoffs": ["..."]},
    "permanent": {"fits_when": ["..."], "tradeoffs": ["..."]}
  },
  "assumptions": [{"key": "final_expenses", "value": 8300, "source": "...", "as_of": "..."}],
  "explanation": "Plain-language summary from the assistant."
}
```
All amounts are whole US dollars (integers). The app formats them. The app renders numbers from this object only,
never from `reply` text.
