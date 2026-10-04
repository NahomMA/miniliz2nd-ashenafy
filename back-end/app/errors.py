"""One error type and one JSON error shape for the whole API.

Same design as the csis-web backend (`ApiError(message, status_code, extra_data)` plus two handlers),
rewritten with a machine-readable `code` and no stack traces in responses.
"""
from __future__ import annotations

import logging

from flask import Flask, jsonify
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

log = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "validation", extra_data: dict | None = None):
        super().__init__(message)
        self.message, self.status_code, self.code, self.extra_data = message, status_code, code, extra_data or {}

    @classmethod
    def invalid(cls, field: str, message: str) -> ApiError:
        return cls(message, extra_data={"field": field})

    def to_response(self):
        return jsonify(error={"message": self.message, "code": self.code, **self.extra_data}), self.status_code


def handle_api_error(exc: ApiError):
    return exc.to_response()


def handle_exceptions(exc: Exception):
    if isinstance(exc, HTTPException):
        code = (exc.name or "error").lower().replace(" ", "_")
        return ApiError(exc.description or exc.name, exc.code or 500, code).to_response()
    if isinstance(exc, IntegrityError):
        return ApiError("Duplicate record found.", 409, "duplicate").to_response()
    log.exception("Unhandled exception")
    return ApiError("Something went wrong on our side.", 500, "server_error").to_response()


def register_error_handlers(app: Flask) -> None:
    app.register_error_handler(ApiError, handle_api_error)
    app.register_error_handler(Exception, handle_exceptions)
