"""Life insurance needs calculator (DIME method).

Pure functions: no I/O beyond loading the bundled reference data, no network, no LLM.
All amounts are whole US dollars in today's dollars. Spec: docs/calculator-spec.md.
"""
from __future__ import annotations

import functools
import json
from pathlib import Path

DATA = Path(__file__).parent / "data"
ASSUMPTIONS: dict = json.loads((DATA / "assumptions.json").read_text())
GLOSSARY: dict = json.loads((DATA / "glossary.json").read_text())

TERM_LENGTHS = (10, 15, 20, 25, 30)
HORIZON_YEARS = 40
ADULT_AGE = 18
MIN_INCOME_YEARS = 5
SHORT_DEBT_YEARS = 5

LABELS = {
    "income": "Income replacement",
    "mortgage": "Mortgage",
    "debts": "Other debts",
    "education": "Education",
    "final": "Final expenses",
    "savings": "Savings",
    "existing_coverage": "Coverage you already have",
}


class ProfileError(ValueError):
    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field


def _safe(fn):
    """Return validation problems as data so a tool call never raises."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ProfileError as exc:
            return {"error": str(exc), "field": exc.field}

    return wrapper


def usd(amount: int) -> str:
    return f"${amount:,}"


def _int(source: dict, field: str, lo: int, hi: int, default: int | None = None) -> int:
    value = source.get(field)
    if value is None:
        if default is None:
            raise ProfileError(field, f"{field} is required")
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProfileError(field, f"{field} must be a number")
    if not lo <= value <= hi:
        raise ProfileError(field, f"{field} must be between {lo:,} and {hi:,}")
    return round(value)


def normalize(profile: dict, overrides: dict | None = None) -> dict:
    """Validate a raw profile and fill defaults. Raises ProfileError."""
    money = 10**9
    ages = []
    for dep in profile.get("dependents") or []:
        ages.append(_int(dep if isinstance(dep, dict) else {"age": dep}, "age", 0, 120))
    children = [a for a in ages if a < ADULT_AGE]
    default_years = max(MIN_INCOME_YEARS, ADULT_AGE - min(children)) if children else MIN_INCOME_YEARS
    mortgage = _int(profile, "mortgage_balance", 0, money, 0)
    assumptions = {k: v["value"] for k, v in ASSUMPTIONS.items()} | (overrides or {})
    fund = profile.get("fund_education")
    return {
        "age": _int(profile, "age", 18, 80),
        "annual_income": _int(profile, "annual_income", 0, money),
        "dependent_ages": ages,
        "income_years": _int(profile, "income_years_to_replace", 0, 40, default_years),
        "income_years_defaulted": profile.get("income_years_to_replace") is None and bool(children),
        "mortgage_balance": mortgage,
        "mortgage_years_left": _int(profile, "mortgage_years_left", 0, 40, 30 if mortgage else 0),
        "other_debts": _int(profile, "other_debts", 0, money, 0),
        "fund_education": any(a < assumptions["college_end_age"] for a in ages) if fund is None else bool(fund),
        "savings": _int(profile, "savings", 0, money, 0),
        "existing_coverage": _int(profile, "existing_coverage", 0, money, 0),
        "lifelong_dependent": bool(profile.get("lifelong_dependent")),
        "legacy_goal": bool(profile.get("legacy_goal")),
        "assumptions": assumptions,
    }


def _college_years_left(p: dict, age: int) -> int:
    a = p["assumptions"]
    return max(0, min(a["college_years"], a["college_end_age"] - age))


def _need_at(p: dict, t: int) -> dict[str, int]:
    """Remaining need by component, t years from now."""
    a = p["assumptions"]
    years_left = p["mortgage_years_left"]
    if years_left:
        mortgage = round(p["mortgage_balance"] * max(0, years_left - t) / years_left)
    else:
        mortgage = p["mortgage_balance"] if t == 0 else 0
    education = 0
    if p["fund_education"]:
        education = a["college_cost_per_year"] * sum(_college_years_left(p, age + t) for age in p["dependent_ages"])
    return {
        "income": p["annual_income"] * max(0, p["income_years"] - t),
        "mortgage": mortgage,
        "debts": p["other_debts"] if t < SHORT_DEBT_YEARS else 0,
        "education": education,
        "final": a["final_expenses"],
    }


def _reasons(p: dict) -> dict[str, str]:
    a = p["assumptions"]
    students = sum(1 for age in p["dependent_ages"] if _college_years_left(p, age))
    until = ", until your youngest turns 18" if p["income_years_defaulted"] else ""
    return {
        "income": f"{p['income_years']} years of your {usd(p['annual_income'])} income{until}.",
        "mortgage": "Pays off the remaining mortgage so your family can stay in their home.",
        "debts": "Clears other debts so they are not passed on.",
        "education": f"Tuition and fees for {students} {'child' if students == 1 else 'children'} "
        f"at {usd(a['college_cost_per_year'])} a year.",
        "final": "Typical funeral and final costs, based on the national median.",
        "savings": "Money already set aside that your family could use.",
        "existing_coverage": "Life insurance already in place, such as through work.",
    }


def _resources(p: dict) -> int:
    return p["savings"] + p["existing_coverage"]


def _assessment(p: dict) -> dict:
    reasons, need = _reasons(p), _need_at(p, 0)
    row = lambda key, amount: {"key": key, "label": LABELS[key], "amount": amount, "reason": reasons[key]}
    total, resources = sum(need.values()), _resources(p)
    used = {"final_expenses"} | ({"college_cost_per_year"} if need["education"] else set())
    return {
        "total_need": total,
        "resources": resources,
        "gap": max(0, total - resources),
        "fully_covered": resources >= total,
        "components": [row(k, v) for k, v in need.items() if v],
        "offsets": [row(k, p[k]) for k in ("savings", "existing_coverage") if p[k]],
        "assumptions": [
            {"key": k, "value": p["assumptions"][k], **{f: ASSUMPTIONS[k][f] for f in ("label", "source", "url", "as_of")}}
            for k in ASSUMPTIONS
            if k in used
        ],
        "method": "DIME: debt, income, mortgage, education, plus final expenses. Today's dollars, no inflation or investment return applied.",
    }


def _projection(p: dict) -> dict:
    resources = _resources(p)
    years = [{"year": t, "remaining_need": sum(_need_at(p, t).values())} for t in range(HORIZON_YEARS + 1)]
    covered = next((y["year"] for y in years if y["remaining_need"] <= resources), None)
    term = next((n for n in TERM_LENGTHS if covered is not None and n >= covered), None)
    if covered == 0:
        reason = "What you already have covers the need today."
    elif term:
        reason = f"Your remaining need falls to what you already have in about {covered} years."
    else:
        reason = "Your need does not fall to what you already have within 30 years, so a fixed term may not cover it all."
    return {"years": years, "covered_year": covered, "suggested_term_years": term if covered else None, "reason": reason}


def _comparison(p: dict, projection: dict) -> dict:
    need, term = _need_at(p, 0), projection["suggested_term_years"]
    endings = [
        text
        for key, text in (
            ("income", "the income-replacement years end"),
            ("education", "your children finish school"),
            ("mortgage", "the mortgage is paid down"),
        )
        if need[key]
    ]
    term_fits = [f"Most of your need is time-bound: it shrinks as {', '.join(endings)}."] if endings else []
    if term:
        term_fits.append(f"A {term}-year period lines up with when your need falls to what you already have.")
    permanent_fits = [f"A small need lasts at any age: final expenses of about {usd(need['final'])}."]
    if p["lifelong_dependent"]:
        permanent_fits.append("Someone will depend on you for life, so part of your need has no end date.")
    if p["legacy_goal"]:
        permanent_fits.append("You want to leave money behind whenever it happens, which a fixed period cannot promise.")
    if not (p["lifelong_dependent"] or p["legacy_goal"]):
        permanent_fits.append("Nothing you shared points to a large need that lasts for life.")
    return {
        "term": {
            "what": GLOSSARY["term"],
            "fits_when": term_fits or ["You did not share a need with a clear end date."],
            "tradeoffs": ["Coverage ends when the period ends. If you still need it then, you would have to arrange new coverage."],
        },
        "permanent": {
            "what": GLOSSARY["permanent"],
            "fits_when": permanent_fits,
            "tradeoffs": ["It typically costs more than term coverage for the same amount, because it is built to last longer."],
        },
        "note": "Educational comparison only. Features and availability differ by product.",
    }


@_safe
def coverage_need(profile: dict, overrides: dict | None = None) -> dict:
    """Total need, resources, gap and a per-component breakdown with reasons."""
    return _assessment(normalize(profile, overrides))


@_safe
def project_need(profile: dict) -> dict:
    """Remaining need for each future year and the term length that covers it."""
    return _projection(normalize(profile))


@_safe
def compare_term_vs_permanent(profile: dict) -> dict:
    """Tradeoffs between term and permanent coverage for this profile. No prices."""
    p = normalize(profile)
    return _comparison(p, _projection(p))


@_safe
def full_assessment(profile: dict, overrides: dict | None = None) -> dict:
    """Breakdown, projection and comparison in one object (the shape the app renders)."""
    p = normalize(profile, overrides)
    projection = _projection(p)
    return _assessment(p) | {"projection": projection, "comparison": _comparison(p, projection)}


@_safe
def what_if(profile: dict, changes: dict) -> dict:
    """Recalculate with some answers changed; `delta` is the change in total need."""
    base = _assessment(normalize(profile))
    result = full_assessment({**profile, **changes})
    return result if "error" in result else result | {"delta": result["total_need"] - base["total_need"]}
