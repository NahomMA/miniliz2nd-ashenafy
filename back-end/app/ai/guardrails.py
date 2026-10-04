"""Checks applied to text going into and coming out of the model."""
from __future__ import annotations

import re
from typing import Any

SSN = re.compile(r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b")
NUMBER = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(k|thousand|m|mil|million)?\b", re.I)
DOLLAR_AMOUNT = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?\s*(?:k|thousand|m|mil|million)?\b", re.I)
REASONING = re.compile(r"<(thinking|reasoning)>.*?</\1>\s*", re.S | re.I)
MULTIPLIERS = {"k": 1_000, "thousand": 1_000, "m": 1_000_000, "mil": 1_000_000, "million": 1_000_000}


def redact(text: str) -> str:
    """Remove anything shaped like a Social Security number before it is stored or sent to the model."""
    return SSN.sub("[removed]", text)


def visible(reply: str) -> str:
    """The reply without any reasoning block some models emit."""
    return REASONING.sub("", reply).strip()


def last_question(text: str) -> str:
    """The final question in an assistant message, used to steer the user back on topic."""
    questions = re.findall(r"[^.!?\n]*\?", text)
    return questions[-1].strip() if questions else ""


def parse_amounts(text: str) -> list[int]:
    """Whole numbers in the text, understanding forms like 85k, $240,000 and 1.2 million."""
    return [
        round(float(digits.replace(",", "")) * MULTIPLIERS.get(unit.lower(), 1))
        for digits, unit in NUMBER.findall(text)
        if digits.strip(",")
    ]


def numbers_in(value: Any) -> set[int]:
    """Every integer anywhere inside a JSON-like structure."""
    if isinstance(value, bool):
        return set()
    if isinstance(value, int):
        return {value, abs(value)}
    if isinstance(value, dict):
        return set().union(*(numbers_in(v) for v in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(numbers_in(v) for v in value)) if value else set()
    return set()


def unsupported_amounts(reply: str, allowed: set[int]) -> list[str]:
    """Dollar amounts in the reply that did not come from a tool result or from the user."""
    return [m.group(0) for m in DOLLAR_AMOUNT.finditer(reply) if parse_amounts(m.group(0))[0] not in allowed]
