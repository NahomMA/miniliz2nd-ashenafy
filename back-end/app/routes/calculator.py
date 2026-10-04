"""Direct access to the calculator (no LLM). Used by the what-if sliders."""
from __future__ import annotations

from flask import Blueprint, current_app

from ..auth import authentication_required
from ..errors import ApiError
from ..models import User
from ..schemas import json_body

bp = Blueprint("calculator", __name__, url_prefix="/calculator")


@bp.post("/assess")
@authentication_required
def assess(auth_user: User):
    profile = json_body("profile")["profile"]
    if not isinstance(profile, dict):
        raise ApiError.invalid("profile", "profile must be an object.")
    result = current_app.extensions["calculator"].call("full_assessment", {"profile": profile})
    if "error" in result:
        raise ApiError.invalid(result.get("field") or "profile", result["error"])
    return result
