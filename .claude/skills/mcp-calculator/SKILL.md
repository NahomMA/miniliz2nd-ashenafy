---
name: mcp-calculator
description: Build or change the MCP server that owns all life-insurance math (tools) and reference data (resources) in back-end/mcp_server. Use when adding or editing a calculation, an assumption, a glossary term, or the Flask-to-MCP bridge.
---

# MCP calculator server

All numbers the user sees come from here. The LLM never calculates.

## Layout
```
back-end/mcp_server/
  calculator.py        pure functions, no I/O, no MCP imports. Source of truth.
  server.py            FastMCP wrapper: registers tools and resources
  data/assumptions.json   every default value with a `source` and `as_of`
  data/glossary.json      plain-language definitions
back-end/app/services/calculator_gateway.py   CalculatorGateway: MCP client used by Flask, in-process fallback
back-end/tests/test_calculator.py
```

## Tools (keep to these five)
| Tool | Input | Output |
|---|---|---|
| `calculate_coverage_need` | profile (see below) | `total_need`, `gap`, `components[]` each with `key`, `label`, `amount`, `reason` |
| `project_need_over_time` | profile | `years[]` with remaining need per year, `suggested_term_years` |
| `compare_term_vs_permanent` | profile | `term` and `permanent` each with `fits_when[]`, `tradeoffs[]` tied to this profile |
| `full_assessment` | profile | breakdown + `projection` + `comparison` in one object (what the app renders) |
| `what_if` | profile, changes dict | same shape as `full_assessment`, plus `delta` |

Profile fields: `age`, `annual_income`, `dependents[]` (`age`), `income_years_to_replace`, `mortgage_balance`,
`other_debts`, `fund_education` (bool), `savings`, `existing_coverage`, `mortgage_years_left`, `lifelong_dependent`, `legacy_goal`.

Method is DIME: Debt + Income replacement + Mortgage + Education + final expenses, minus savings and existing coverage.
`gap` is never negative; if covered, return `gap: 0` and a `reason` saying so.

## Resources
- `assumptions://defaults` returns assumptions.json
- `glossary://terms` returns glossary.json

## Rules
1. Math lives in `calculator.py` only. `server.py` functions are one-line wrappers with good docstrings
   (the docstring becomes the tool description the LLM reads).
2. Every tool returns structured JSON with a `reason` string per component. The LLM rephrases reasons, it does not invent them.
3. No value in assumptions.json without `source` (URL or publication) and `as_of`. If no source is found,
   make it a required user input instead of a default. Never guess a number.
4. No premiums, quotes or product names. We have no real rate data.
5. Validate inputs: negatives, missing income, ages out of range return a clear error dict, not an exception.
6. Every calculator function gets a pytest case, including the demo persona "Maria" with expected totals.

## Server pattern
`server.py` uses `FastMCP` from `mcp.server.fastmcp` (SDK pinned to `mcp<2`). Tool inputs are the Pydantic `Profile`
model, whose field descriptions become the schema the LLM reads. All fields are optional there; range checks and
friendly errors live in `calculator.normalize`. A new tool = one function in `calculator.py`, one wrapper in
`server.py`, one entry in `LOCAL_TOOLS` in the gateway, one test.

## Gateway (`app/services/calculator_gateway.py`)
- `tools()` returns `ToolSpec(name, description, input_schema)` from the server, cached. Convert to Bedrock `toolSpec` in the AI layer.
- `call(name, arguments)` opens a short stdio session and returns the tool's dict.
- On any MCP failure it logs a warning and runs the same function from `LOCAL_TOOLS`. The demo must not break.
- Flask reaches it as `current_app.extensions["calculator"]`.

## Dev bonus
The server is registered for Claude Code in `.mcp.json` as `life-calc`.

## Done when
`uv run pytest -q` passes, including `tests/test_gateway.py` (MCP result equals the pure function, fallback works).
