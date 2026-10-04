<div align="center">

## What it does

Liv, the app's AI guide, asks about dependents, income, debts and existing coverage, one question at a time.
LifeSize then shows a coverage goal, why each part of it is there, how the need shrinks over time, and how term
and permanent coverage fit that person's situation. Every number can be adjusted and traced to a published source.

**The assistant talks. Tested code calculates. The assistant explains.** The model never produces a number.

## Screens
<p align="center">
<img src="docs/screenshots/1-login.png" width="170" alt="Sign in" title="Sign in">
<img src="docs/screenshots/2-chat.png" width="170" alt="Liv asks one question at a time" title="Liv asks one question at a time">
<img src="docs/screenshots/4-results.png" width="170" alt="The goal and why" title="The goal and why">
<img src="docs/screenshots/5-what-if.png" width="170" alt="What-if and need over time" title="What-if and need over time">
<img src="docs/screenshots/6-term-or-permanent.png" width="170" alt="Term or permanent" title="Term or permanent">
</p>

## Architecture
<p align="center">
<img src="assets/lifesize-architecture.png" width="900" alt="LifeSize system architecture: Expo app, Flask API on AWS EC2, Amazon Bedrock Nova Lite and Nova Pro behind a Bedrock Guardrail, MCP calculator server and SQLite">
</p>

## Where to look

| To see                                                      | Open                                                               |
| ----------------------------------------------------------- | ------------------------------------------------------------------ |
| The math (DIME method, projection, term logic)              | `back-end/mcp_server/calculator.py`                              |
| The MCP tools and resources the model can call              | `back-end/mcp_server/server.py`                                  |
| How a chat turn runs: guardrails, tool loop, fallback       | `back-end/app/ai/service.py`                                     |
| Everything the models are told                              | `back-end/app/ai/prompts.py`                                     |
| Input and output checks                                     | `back-end/app/ai/guardrails.py`                                  |
| Auth: argon2, JWT, the`authentication_required` decorator | `back-end/app/security.py`, `back-end/app/auth.py`             |
| The results screen                                          | `front-end/src/app/results.tsx`                                  |
| The single API client and token storage                     | `front-end/src/lib/api.ts`, `front-end/src/lib/token-store.ts` |
| Tests, including the hand-worked persona                    | `back-end/tests/`                                                |
| The API contract and calculator spec                        | `docs/api.md`, `docs/calculator-spec.md`                       |

## Security and safety

- **Accounts:** argon2 password hashing, short-lived JWT (HS256), token kept in the device's encrypted store, HTTPS only.
- **Data:** only email, password hash and the answers typed. SSN-shaped numbers are removed before storage or any model call.
- **AI guardrails in layers:**
  1. an input scope check that blocks off-topic and prompt-injection messages before the main model sees them
  2. a scope-first system prompt
  3. a managed Amazon Bedrock Guardrail (investment advice, prompt attacks, hate, PII)
  4. an output check that rejects any dollar amount that did not come from the calculator
- **Decided in code, not by the model:** users under 18 are turned away kindly, and a message suggesting self-harm
  gets a fixed reply with the 988 Suicide and Crisis Lifeline.
- **Resilience:** if the model or MCP is unavailable, a scripted interview and the in-process calculator finish the assessment.
- **Advice boundary:** educational estimate only. No products, carriers or prices.

## Run it

```bash
# API (needs AWS_BEARER_TOKEN_BEDROCK in .env; see .env.example)
cd back-end && uv sync && uv run flask --app wsgi run --port 5000
uv run pytest -q                              # 44 tests
uv run python scripts/guardrail_check.py      # red-team against the live models
uv run python scripts/edge_cases.py           # unusual profiles through the calculator

# App
cd front-end && npm install && npx expo start
```

Demo login: `demo@codelinc.app` / `Demo2026!`

## Deploy

One EC2 instance, Docker Compose, automatic HTTPS (Caddy):

1. Launch Ubuntu in `us-east-2`, open ports 22, 80 and 443, paste `deploy/setup.sh` as user data.
2. On the instance: add the Bedrock key to `/opt/rightsize/deploy/.env`, then
   `cd /opt/rightsize/deploy && sudo docker compose up -d --build`.
3. Build the APK: `cd front-end && npx eas-cli build -p android --profile preview` (the API address is set in `eas.json`).

## How it was built

Spec first: an API contract, a calculator spec with a persona worked by hand, and a task list (`docs/`).
Assumptions are cited in `back-end/mcp_server/data/assumptions.json` (NFDA, College Board).
The mascot and app icon are original, generated by `front-end/scripts/make-assets.py`.

## Costs and licensing

All libraries are open source. Running costs are Amazon Bedrock usage (Nova Pro, Nova Lite, Guardrails) and one small EC2 instance.
