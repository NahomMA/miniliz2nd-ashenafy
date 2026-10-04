"""MCP server for the life insurance needs calculator.

Tools wrap `calculator`; resources expose the reference data behind every number.
Run over stdio:  python -m mcp_server.server
"""
from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from . import calculator

mcp = FastMCP(
    "life-needs-calculator",
    instructions=(
        "Deterministic life insurance needs calculator. Call these tools for every number; "
        "never estimate amounts yourself. Amounts are whole US dollars in today's dollars."
    ),
)


class Dependent(BaseModel):
    age: int = Field(description="Age in years")


class Profile(BaseModel):
    """What the user has shared. Omit anything they did not say; the calculator applies documented defaults."""

    age: int | None = Field(None, description="User's age in years (18 to 80). Required.")
    annual_income: int | None = Field(None, description="Yearly income before tax, in dollars. Required.")
    dependents: list[Dependent] = Field(default_factory=list, description="People who rely on the user's income")
    income_years_to_replace: int | None = Field(
        None, description="Years of income to replace. Default: until the youngest child turns 18, minimum 5."
    )
    mortgage_balance: int | None = Field(None, description="Remaining mortgage balance in dollars")
    mortgage_years_left: int | None = Field(None, description="Years left on the mortgage")
    other_debts: int | None = Field(None, description="Car loans, credit cards, student loans and similar, in dollars")
    fund_education: bool | None = Field(None, description="Whether to include college costs for dependents")
    savings: int | None = Field(None, description="Savings the family could use, in dollars")
    existing_coverage: int | None = Field(None, description="Life insurance already in place, in dollars")
    lifelong_dependent: bool | None = Field(None, description="True if someone will depend on the user for life")
    legacy_goal: bool | None = Field(None, description="True if the user wants to leave money regardless of timing")

    def as_input(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


@mcp.tool()
def calculate_coverage_need(profile: Profile) -> dict[str, Any]:
    """Total coverage need, what the user already has, the gap, and a breakdown with a reason per component."""
    return calculator.coverage_need(profile.as_input())


@mcp.tool()
def project_need_over_time(profile: Profile) -> dict[str, Any]:
    """Remaining need for each future year, and the term length after which existing resources cover it."""
    return calculator.project_need(profile.as_input())


@mcp.tool()
def compare_term_vs_permanent(profile: Profile) -> dict[str, Any]:
    """Tradeoffs between term and permanent coverage tied to this user's situation. Educational, no prices."""
    return calculator.compare_term_vs_permanent(profile.as_input())


@mcp.tool()
def full_assessment(profile: Profile) -> dict[str, Any]:
    """Complete result in one call: breakdown, projection and comparison. Use this to present the final assessment."""
    return calculator.full_assessment(profile.as_input())


@mcp.tool()
def what_if(profile: Profile, changes: dict[str, Any]) -> dict[str, Any]:
    """Recalculate with some profile fields changed. Returns the full assessment plus `delta` in total need."""
    return calculator.what_if(profile.as_input(), changes)


@mcp.resource("assumptions://defaults", mime_type="application/json")
def assumptions() -> str:
    """Default values used by the calculator, each with its published source."""
    return json.dumps(calculator.ASSUMPTIONS)


@mcp.resource("glossary://terms", mime_type="application/json")
def glossary() -> str:
    """Plain-language definitions of life insurance terms."""
    return json.dumps(calculator.GLOSSARY)


if __name__ == "__main__":
    mcp.run(transport="stdio")
