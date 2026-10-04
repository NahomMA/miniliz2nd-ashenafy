"""Registration, login and the current user."""
from __future__ import annotations

from flask import Blueprint, current_app
from sqlalchemy.exc import IntegrityError

from ..auth import authentication_required
from ..errors import ApiError
from ..models import User, db
from ..schemas import Credentials, Registration
from ..security import verify_password

bp = Blueprint("auth", __name__, url_prefix="/auth")


def _session(user: User) -> dict:
    return {"token": current_app.extensions["tokens"].issue(user.id), "user": user.to_dict()}


@bp.post("/register")
def register():
    form = Registration.from_request()
    db.session.add(user := User.create(form.email, form.name, form.password))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ApiError("An account with this email already exists.", 409, "email_taken", {"field": "email"}) from None
    return _session(user), 201


@bp.post("/login")
def login():
    form = Credentials.from_request()
    user = User.find_by_email(form.email)
    if not verify_password(user.password_hash if user else None, form.password):
        raise ApiError("Email or password is incorrect.", 401, "invalid_credentials")
    return _session(user)


@bp.get("/me")
@authentication_required
def me(auth_user: User):
    return {"user": auth_user.to_dict()}
