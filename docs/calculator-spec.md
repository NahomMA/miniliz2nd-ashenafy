# Calculator spec (draft v1)

Owner: `back-end/mcp_server/calculator.py`. Exposed as MCP tools. Pure functions, whole dollars, today's dollars.

## Profile
| Field | Type | Required | Default when the user is not sure |
|---|---|---|---|
| `age` | int 18 to 80 | yes | |
| `annual_income` | int >= 0 | yes | |
| `dependents` | list of `{age}` | yes (may be empty) | |
| `income_years_to_replace` | int 0 to 40 | no | years until the youngest dependent turns 18, minimum 5; 5 if no children |
| `mortgage_balance` | int >= 0 | no | 0 |
| `mortgage_years_left` | int 0 to 40 | no | 30 if there is a balance |
| `other_debts` | int >= 0 | no | 0 |
| `fund_education` | bool | no | true if any dependent is under 22 |
| `savings` | int >= 0 | no | 0 |
| `existing_coverage` | int >= 0 | no | 0 |

## Assumptions (`data/assumptions.json`)
| Key | Value | Source | Status |
|---|---|---|---|
| `final_expenses` | 8,300 | NFDA General Price List Study (2023), national median funeral with viewing and burial. Excludes cemetery and marker costs. https://nfda.org/news/media-center/nfda-news-releases | ok, checked 2026-10-03 |
| `college_cost_per_year` | 11,950 | College Board, Trends in College Pricing and Student Aid 2025, average published tuition and fees, public four-year in-state, 2025-26. https://research.collegeboard.org/trends/college-pricing/highlights | ok, checked 2026-10-03 |
| `college_years` | 4 | convention | ok |
| `college_end_age` | 22 | convention | ok |

Both dollar values were checked against the sources on 2026-10-03. Tuition and fees only; room and board are not included, and the app says so.

Stated simplification: no inflation or investment return is applied. We assume the two roughly offset, and say so in the
"how we calculated this" view.

## Tool 1: `calculate_coverage_need(profile, overrides=None)`
```
income      = annual_income * income_years_to_replace
mortgage    = mortgage_balance
debts       = other_debts
education   = sum over dependents of college_cost_per_year * clamp(college_end_age - age, 0, college_years)   (0 if fund_education is false)
final       = final_expenses
total_need  = income + mortgage + debts + education + final
resources   = savings + existing_coverage
gap         = max(0, total_need - resources)
```
Returns `total_need`, `resources`, `gap`, `components[]`, `offsets[]`, `assumptions[]`. Each component has a `reason`
built from a template with the user's own values. Components with amount 0 are omitted.

## Tool 2: `project_need_over_time(profile)`
For each year `t` from 0 to 40:
```
income(t)    = annual_income * max(0, income_years_to_replace - t)
mortgage(t)  = mortgage_balance * max(0, mortgage_years_left - t) / mortgage_years_left     (straight line)
debts(t)     = other_debts if t < 5 else 0
education(t) = sum over dependents of college_cost_per_year * clamp(college_end_age - (age + t), 0, college_years)
remaining(t) = income(t) + mortgage(t) + debts(t) + education(t) + final_expenses
```
`covered_year` = first `t` where `remaining(t) <= resources`. `suggested_term_years` = `covered_year` rounded up to the
next of 10, 15, 20, 25, 30. If `covered_year` is over 30 or the need never falls (no time-bound needs), return
`suggested_term_years: null` with a reason.

## Tool 3: `compare_term_vs_permanent(profile, projection)`
No prices. Returns `term` and `permanent`, each with `fits_when[]` and `tradeoffs[]`, selected by rules:
- need falls to resources within 30 years: term bullet names the year and what ends then (mortgage, youngest finishing school)
- a dependent who will need lifelong support, or the user states a goal to leave money regardless of timing: permanent bullet
- always: one neutral sentence each on what the type is, in the deck's wording style (defined period vs designed to last longer)
Generic definitions come from `glossary://terms`.

## Tool 4: `what_if(profile, changes)`
Applies `changes` to a copy of the profile, runs tools 1 and 2, returns the same shape plus `delta` against the original total.

## Validation
Bad input returns `{"error": "message", "field": "name"}`: negative amounts, age out of range, missing income,
dependent age below 0 or above 120.

## Test persona: Maria
Input: age 34, income 85,000, dependents aged 3 and 6, mortgage 240,000 with 25 years left, other debts 15,000,
fund education yes, savings 30,000, existing coverage 50,000 (through work). Income years not given.

| Component | Working | Amount |
|---|---|---|
| Income replacement | 85,000 x 15 (youngest is 3, so 15 years to 18) | 1,275,000 |
| Mortgage | balance | 240,000 |
| Other debts | | 15,000 |
| Education | 2 children x 4 years x 11,950 | 95,600 |
| Final expenses | | 8,300 |
| **Total need** | | **1,633,900** |
| Resources | 30,000 + 50,000 | 80,000 |
| **Gap** | | **1,553,900** |

Projection checks (resources 80,000):
- t=15: 0 + 96,000 + 0 + (47,800 + 11,950) + 8,300 = 164,050 (not covered)
- t=18: 0 + 67,200 + 0 + 11,950 + 8,300 = 87,450 (not covered)
- t=19: 0 + 57,600 + 0 + 0 + 8,300 = 65,900 (covered) so `covered_year` 19, `suggested_term_years` 20

What-if check: `income_years_to_replace: 10` gives total 1,208,900, gap 1,128,900, delta -425,000.

Other tests: no dependents, already fully covered (gap 0), `fund_education: false`, each validation error.
If the assumption values change after verification, recompute this table and the tests together.
