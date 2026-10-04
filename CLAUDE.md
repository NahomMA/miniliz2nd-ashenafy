# codeLinc 11: Life Insurance Needs Analyzer

Hackathon entry (Lincoln Financial + AWS). **Submission due Sun Oct 4 2026, 10:30 ET.** 5-minute live demo on a phone.
Goal: win. One feature done excellently that cannot break on stage.

## Product
A conversational mobile app that walks a user through dependents, income, debts and existing coverage,
then shows a personalized coverage need with a clear, calm explanation of the math.

**Core rule: the LLM talks, MCP tools calculate, the LLM explains.**
Claude never produces a number itself. Every figure shown to the user comes from an MCP tool result.

## Architecture
```
Expo app (front-end/)  --HTTPS + JWT-->  Flask API (back-end/)  --Converse + tool use-->  Amazon Bedrock (Claude)
                                              |
                                              +--MCP client-->  MCP server (back-end/mcp_server/)
                                                                 tools: calculator.py (pure, unit-tested)
                                                                 resources: assumptions, glossary
```
- back-end/: Flask, SQLite, PyJWT + argon2, boto3. No Postgres, Alembic, Redis, websockets, LangChain.
- front-end/: Expo (TypeScript, expo-router). Token in expo-secure-store.
- API contract lives in `docs/api.md`. Change an endpoint, update the doc in the same edit.

## Scope (build in this order, cut from the bottom)
1. MUST: login, chat intake, profile extraction, calculation, results screen with breakdown and explanation
2. MUST: "why this number" (each component with a one-line reason)
3. SHOULD: term vs permanent card tailored to the user
4. SHOULD: what-if sliders (recalculate through the tool, no LLM call)
5. NICE: saved assessment history
Anything not on this list: do not build it. Ask first.
Login and registration are low value to judges. Keep them minimal.

## Rules for Claude
- Use the skills in `.claude/skills/` for any backend endpoint, Bedrock, MCP or Expo screen work.
- `prev_projects/` is read-only reference (csis-web). Port patterns, never edit or commit it. It contains private keys.
- Stay inside this project directory. Never read, write, list, search or `cd` anywhere else on the machine, by any route (absolute paths, `..`, `~`, `$HOME`, scripts). The guard hook enforces this; do not work around it.
- Never read, print or commit `.env`. Code loads it with python-dotenv. Variable names go in `.env.example`.
- Do not spawn subagents or workflows. Work directly. The user is on a tight budget.
- Keep changes small. Run the tests or a curl smoke check after each backend change.
- No financial numbers without a cited source. Assumptions live in `back-end/mcp_server/data/assumptions.json` with a `source` field.
- No Lincoln logos or copied Lincoln text in the app (third-party rights). Colors inspired by the brand are fine.
- No new features after 08:00 Sunday. Only fixes, README and rehearsal.

## Product guardrails (also demo talking points)
- Educational estimate, not financial advice. Disclaimer on the results screen.
- No specific product, carrier or premium recommendations.
- Never ask for or store SSN, health details or account numbers.
- Tone: calm, plain language, no fear language ("if you die" becomes "if something happened to you").
- If Bedrock or MCP fails, the backend falls back to a scripted intake and a direct calculator call. The demo must not break.

## Demo checklist (before submission)
- [ ] Seeded demo user and persona ("Maria", 34, two kids) work end to end
- [ ] Backend reachable over HTTPS from the phone
- [ ] APK built with EAS and installed on a phone
- [ ] `pytest` passes
- [ ] README: description, architecture diagram, security section, demo credentials, any licensing costs
- [ ] Repo contains no secrets (`git log -p | grep -i bearer` is empty)
- [ ] Demo rehearsed twice under 5:00

## Code standards (production quality, no exceptions)
- Small modules with one job. Classes where there is state or a clear role (`Settings`, `TokenService`, `CalculatorGateway`); plain functions otherwise.
- Full type hints, a one-line docstring per module and public function, no dead code, no commented-out code, no TODOs left behind.
- Validate at the boundary (request schemas, calculator `normalize`), trust data inside.
- Errors are data the client can act on: `ApiError(message, status, code, field)`. Never leak stack traces or secrets.
- Every behavior has a test. A change is done only when `pytest -q` passes.
- Write fresh code. csis-web is a reference for ideas only; do not paste its code.
- Dependencies: managed with uv (`pyproject.toml` + `uv.lock`; add with `uv add <pkg>`); `mcp` stays on `<2` (v2 renamed the server API).

## Commands (run from back-end/)
- Tests: `uv run pytest -q`
- API: `uv run flask --app wsgi run --port 5000`
- MCP server alone: `uv run python -m mcp_server.server`
- Bedrock check: `uv run python scripts/bedrock_check.py`
