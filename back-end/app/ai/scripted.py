"""Scripted interview and templated explanation.

Used when the model is unavailable, so a conversation can always finish with a real assessment.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .guardrails import parse_amounts

NOTHING = re.compile(r"\b(no|none|nope|nothing|zero|n/a)\b", re.I)
NOT_SURE = re.compile(r"\b(not sure|don'?t know|unsure|no idea|skip)\b", re.I)
RETRY = "Could you give me a number? A rough estimate is fine."
ADULTS_ONLY = (
    "LifeSize is designed for adults aged 18 to 80, because a person generally needs to be an adult to take out "
    "their own life insurance policy. A parent or guardian is welcome to use it for the family. How old are you?"
)
ADULT_AGES = range(18, 81)
INTRO = "Let me ask a few quick questions instead. "


@dataclass(frozen=True)
class Step:
    field: str
    question: str
    required: bool = False
    only_if: str | None = None


STEPS = (
    Step("age", "How old are you?", required=True),
    Step("dependents", "How old are the children or others who depend on you? For example: 3 and 6. Say none if no one does."),
    Step("annual_income", "About how much do you earn in a year, before tax?", required=True),
    Step("mortgage_balance", "Do you have a mortgage? If so, roughly how much is left? Say none if not."),
    Step("mortgage_years_left", "About how many years are left on the mortgage?", only_if="mortgage_balance"),
    Step("other_debts", "Any other debts, like a car loan or credit cards? A rough total is fine."),
    Step("savings", "About how much do you have in savings that your family could use?"),
    Step("existing_coverage", "Last one: do you already have life insurance, for example through work? If so, how much?"),
)


class ScriptedInterview:
    """State is `{"step": int, "answers": dict}` and is stored on the assessment between turns."""

    @staticmethod
    def new_state() -> dict:
        return {"step": 0, "answers": {}}

    @staticmethod
    def question(state: dict) -> str:
        return STEPS[state["step"]].question

    def answer(self, state: dict, message: str) -> tuple[dict, str | None]:
        """Record an answer. Returns the new state and the next question, or None when the interview is complete."""
        step, answers = STEPS[state["step"]], dict(state["answers"])
        amounts = parse_amounts(message)
        if step.field == "age" and amounts and amounts[0] not in ADULT_AGES:
            return state, ADULTS_ONLY
        if step.field == "dependents":
            answers["dependents"] = [{"age": a} for a in amounts if a <= 120]
        elif amounts:
            answers[step.field] = amounts[0]
        elif NOTHING.search(message) and not step.required:
            answers[step.field] = 0
        elif step.required or not NOT_SURE.search(message):
            return state, RETRY
        index = state["step"] + 1
        while index < len(STEPS) and STEPS[index].only_if and not answers.get(STEPS[index].only_if):
            index += 1
        if index == len(STEPS):
            return {"step": index, "answers": answers}, None
        return {"step": index, "answers": answers}, STEPS[index].question


def summarize(result: dict) -> str:
    """Plain-language explanation built only from calculator output."""
    lines = [f"A coverage goal of ${result['total_need']:,} would help keep your family on track."]
    if result["fully_covered"]:
        lines.append(f"The ${result['resources']:,} you already have covers that goal.")
    elif result["resources"]:
        lines.append(f"You already have ${result['resources']:,} toward it, so ${result['gap']:,} remains.")
    lines.append("Here is how it adds up:")
    lines += [f"• {c['label']}: ${c['amount']:,}. {c['reason']}" for c in result["components"]]
    if term := result["projection"]["suggested_term_years"]:
        lines.append(f"Your need shrinks over time, so a {term}-year period lines up with it.")
    lines.append("You can adjust any of these on the results screen.")
    return "\n".join(lines)
