"""Request authentication.

Same contract as the csis-web decorator: the signed-in user is passed as the first argument.
Differences: stateless (no token table), and every failure is a 401 `invalid_token`.
"""
from __future__ import annotations

from functools import wraps

from flask import current_app, request

from .errors import ApiError
from .models import User, db


def authentication_required(view):
    @wraps(view)
    def decorator(*args, **kwargs):
        scheme, _, token = request.headers.get("Authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise ApiError("Sign in to continue.", 401, "invalid_token")
        auth_user = db.session.get(User, current_app.extensions["tokens"].verify(token.strip()))
        if auth_user is None:
            raise ApiError("Invalid access token.", 401, "invalid_token")
        return view(auth_user, *args, **kwargs)

    return decorator
