"""Probe the calculator with unusual profiles and print the headline results.

Usage (from back-end/):  uv run python scripts/edge_cases.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp_server import calculator  # noqa: E402

BASE = {"age": 34, "annual_income": 85_000}
CASES = {
    "nothing saved, two kids, mortgage": {**BASE, "dependents": [{"age": 3}, {"age": 6}], "mortgage_balance": 240_000, "mortgage_years_left": 25},
    "no dependents, no debts": BASE,
    "no income (stay-at-home parent)": {"age": 34, "annual_income": 0, "dependents": [{"age": 3}], "mortgage_balance": 100_000},
    "adult dependent only (spouse)": {**BASE, "dependents": [{"age": 40}]},
    "child already in college (19)": {**BASE, "dependents": [{"age": 19}]},
    "already over-covered": {**BASE, "existing_coverage": 5_000_000},
    "mortgage with zero years left": {**BASE, "mortgage_balance": 50_000, "mortgage_years_left": 0},
    "zero income years chosen": {**BASE, "income_years_to_replace": 0},
    "oldest allowed (80) with a child": {"age": 80, "annual_income": 20_000, "dependents": [{"age": 10}]},
    "dependents given as plain numbers": {**BASE, "dependents": [3, 6]},
    "decimal amounts": {**BASE, "annual_income": 85_000.75, "savings": 1_000.4},
    "lifelong dependent": {**BASE, "dependents": [{"age": 30}], "lifelong_dependent": True},
    "INVALID under 18": {"age": 16, "annual_income": 10_000},
    "INVALID negative debt": {**BASE, "other_debts": -5},
    "INVALID text for a number": {**BASE, "savings": "lots"},
    "INVALID absurdly large": {**BASE, "annual_income": 10**12},
    "INVALID missing income": {"age": 34},
}


def main() -> None:
    for name, profile in CASES.items():
        result = calculator.full_assessment(profile)
        if "error" in result:
            print(f"{name:38} -> error on {result['field']}: {result['error']}")
            continue
        projection = result["projection"]
        print(
            f"{name:38} -> need {result['total_need']:>9,} gap {result['gap']:>9,} "
            f"covered_year {projection['covered_year']} term {projection['suggested_term_years']} | {projection['reason']}"
        )


if __name__ == "__main__":
    main()
