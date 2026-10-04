"""Expected values are worked by hand in docs/calculator-spec.md."""
import pytest

from mcp_server import calculator as calc

MARIA = {
    "age": 34,
    "annual_income": 85_000,
    "dependents": [{"age": 3}, {"age": 6}],
    "mortgage_balance": 240_000,
    "mortgage_years_left": 25,
    "other_debts": 15_000,
    "savings": 30_000,
    "existing_coverage": 50_000,
}


def amounts(result):
    return {c["key"]: c["amount"] for c in result["components"]}


def test_maria_breakdown():
    r = calc.coverage_need(MARIA)
    assert amounts(r) == {"income": 1_275_000, "mortgage": 240_000, "debts": 15_000, "education": 95_600, "final": 8_300}
    assert (r["total_need"], r["resources"], r["gap"]) == (1_633_900, 80_000, 1_553_900)
    assert "until your youngest turns 18" in r["components"][0]["reason"]
    assert all(a["source"] for a in r["assumptions"])


def test_maria_projection():
    r = calc.project_need(MARIA)
    remaining = {y["year"]: y["remaining_need"] for y in r["years"]}
    assert (remaining[0], remaining[15], remaining[18], remaining[19]) == (1_633_900, 164_050, 87_450, 65_900)
    assert (r["covered_year"], r["suggested_term_years"]) == (19, 20)


def test_maria_what_if_ten_years():
    r = calc.what_if(MARIA, {"income_years_to_replace": 10})
    assert (r["total_need"], r["gap"], r["delta"]) == (1_208_900, 1_128_900, -425_000)


def test_maria_comparison_is_specific_and_price_free():
    r = calc.compare_term_vs_permanent(MARIA)
    assert "20-year" in " ".join(r["term"]["fits_when"])
    assert "$8,300" in r["permanent"]["fits_when"][0]
    assert "premium" not in str(r).lower()


def test_full_assessment_shape():
    r = calc.full_assessment(MARIA)
    assert {"total_need", "gap", "components", "offsets", "assumptions", "projection", "comparison"} <= r.keys()


def test_no_dependents_uses_minimum_income_years():
    r = calc.coverage_need({"age": 28, "annual_income": 60_000, "dependents": []})
    assert amounts(r) == {"income": 300_000, "final": 8_300}


def test_fully_covered_has_zero_gap_and_no_term():
    profile = {"age": 50, "annual_income": 40_000, "existing_coverage": 500_000}
    r = calc.full_assessment(profile)
    assert r["gap"] == 0 and r["fully_covered"]
    assert r["projection"]["covered_year"] == 0 and r["projection"]["suggested_term_years"] is None


def test_education_can_be_excluded():
    assert "education" not in amounts(calc.coverage_need({**MARIA, "fund_education": False}))


def test_lifelong_dependent_changes_permanent_view():
    r = calc.compare_term_vs_permanent({**MARIA, "lifelong_dependent": True})
    assert any("for life" in s for s in r["permanent"]["fits_when"])


@pytest.mark.parametrize(
    "changes, field",
    [
        ({"annual_income": None}, "annual_income"),
        ({"annual_income": -1}, "annual_income"),
        ({"age": 12}, "age"),
        ({"savings": "lots"}, "savings"),
        ({"dependents": [{"age": -2}]}, "age"),
    ],
)
def test_invalid_input_returns_error(changes, field):
    assert calc.coverage_need({**MARIA, **changes})["field"] == field
    assert "error" in calc.what_if(MARIA, changes)


def test_term_is_suggested_even_with_nothing_saved():
    profile = {**MARIA, "savings": 0, "existing_coverage": 0}
    r = calc.full_assessment(profile)
    assert (r["projection"]["covered_year"], r["projection"]["suggested_term_years"]) == (25, 25)
    assert "only final expenses remain" in r["projection"]["reason"]
    assert "time-bound needs end" in " ".join(r["comparison"]["term"]["fits_when"])


def test_short_need_gets_the_shortest_term_and_final_expenses_alone_get_none():
    assert calc.project_need({"age": 30, "annual_income": 50_000})["suggested_term_years"] == 10
    only_final = calc.project_need({"age": 30, "annual_income": 50_000, "income_years_to_replace": 0})
    assert (only_final["covered_year"], only_final["suggested_term_years"]) == (0, None)
    assert "final expenses" in only_final["reason"]
