"""Conversations that lead to a coverage assessment."""
from __future__ import annotations

from flask import Blueprint, current_app

from ..auth import authentication_required
from ..errors import ApiError
from ..models import Assessment, User, db
from ..schemas import ChatMessage

bp = Blueprint("assessments", __name__, url_prefix="/assessments")


def _owned(auth_user: User, assessment_id: int) -> Assessment:
    assessment = db.session.get(Assessment, assessment_id)
    if assessment is None or assessment.user_id != auth_user.id:
        raise ApiError("Assessment not found.", 404, "not_found")
    return assessment


@bp.post("")
@authentication_required
def start(auth_user: User):
    assessment = current_app.extensions["chat"].start(auth_user)
    db.session.add(assessment)
    db.session.commit()
    return assessment.turn(assessment.transcript[0]["text"]), 201


@bp.post("/<int:assessment_id>/chat")
@authentication_required
def chat(auth_user: User, assessment_id: int):
    assessment = _owned(auth_user, assessment_id)
    reply = current_app.extensions["chat"].reply(assessment, ChatMessage.from_request().message)
    db.session.commit()
    return assessment.turn(reply)


@bp.get("")
@authentication_required
def history(auth_user: User):
    return {"items": [a.summary() for a in Assessment.for_user(auth_user)]}


@bp.get("/<int:assessment_id>")
@authentication_required
def detail(auth_user: User, assessment_id: int):
    return _owned(auth_user, assessment_id).detail()
