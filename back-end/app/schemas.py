"""Request bodies, validated on construction."""
from __future__ import annotations

import re
from dataclasses import dataclass

from flask import request

from .errors import ApiError

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_MIN, PASSWORD_MAX = 8, 128
MESSAGE_MAX = 1000


def json_body(*required_fields: str) -> dict:
    """The JSON object in the request, with required fields checked (as csis-web's verify_required_fields)."""
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ApiError("Please provide valid JSON data.")
    if missing := [f for f in required_fields if body.get(f) in (None, "")]:
        raise ApiError("Missing required fields.", extra_data={"required": missing, "field": missing[0]})
    return body


def _text(body: dict, field: str, max_length: int) -> str:
    value = body[field]
    if not isinstance(value, str) or not value.strip():
        raise ApiError.invalid(field, f"{field} must be text.")
    if len(value) > max_length:
        raise ApiError.invalid(field, f"{field} is too long (max {max_length} characters).")
    return value


@dataclass(frozen=True)
class Credentials:
    email: str
    password: str

    @classmethod
    def from_request(cls) -> Credentials:
        body = json_body("email", "password")
        return cls(_text(body, "email", 254).strip().lower(), _text(body, "password", PASSWORD_MAX))


@dataclass(frozen=True)
class Registration:
    email: str
    password: str
    name: str

    @classmethod
    def from_request(cls) -> Registration:
        body = json_body("email", "password", "name")
        creds = Credentials.from_request()
        if not EMAIL.match(creds.email):
            raise ApiError.invalid("email", "Enter a valid email address.")
        if len(creds.password) < PASSWORD_MIN:
            raise ApiError.invalid("password", f"Password must be at least {PASSWORD_MIN} characters.")
        return cls(creds.email, creds.password, _text(body, "name", 80).strip())


@dataclass(frozen=True)
class ChatMessage:
    message: str

    @classmethod
    def from_request(cls) -> ChatMessage:
        return cls(_text(json_body("message"), "message", MESSAGE_MAX).strip())
