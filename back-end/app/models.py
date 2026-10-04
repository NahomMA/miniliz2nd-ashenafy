"""Database models."""
from __future__ import annotations

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .security import hash_password, verify_password


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    @classmethod
    def create(cls, email: str, name: str, password: str) -> User:
        return cls(email=email, name=name, password_hash=hash_password(password))

    @classmethod
    def find_by_email(cls, email: str) -> User | None:
        return db.session.scalar(db.select(cls).filter_by(email=email))

    def check_password(self, password: str) -> bool:
        return verify_password(self.password_hash, password)

    def to_dict(self) -> dict:
        return {"id": self.id, "email": self.email, "name": self.name}


class Assessment(db.Model):
    """One conversation and, once calculated, its result."""

    __tablename__ = "assessments"
    AI, SCRIPTED = "ai", "scripted"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    mode: Mapped[str] = mapped_column(String(10), default=AI)
    state: Mapped[dict] = mapped_column(JSON, default=dict)
    transcript: Mapped[list] = mapped_column(JSON, default=list)
    llm_messages: Mapped[list] = mapped_column(JSON, default=list)
    profile: Mapped[dict | None] = mapped_column(JSON, default=None)
    result: Mapped[dict | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    def __init__(self, **kwargs):
        defaults = {"mode": self.AI, "state": {}, "transcript": [], "llm_messages": []}
        super().__init__(**{**defaults, **kwargs})

    @classmethod
    def for_user(cls, user: User) -> list[Assessment]:
        return list(db.session.scalars(db.select(cls).filter_by(user_id=user.id).order_by(cls.id.desc())))

    @property
    def done(self) -> bool:
        return self.result is not None

    def turn(self, reply: str) -> dict:
        return {"id": self.id, "reply": reply, "profile": self.profile, "assessment": self.result, "done": self.done}

    def summary(self) -> dict:
        totals = {k: self.result[k] for k in ("total_need", "gap")} if self.result else {"total_need": None, "gap": None}
        return {"id": self.id, "created_at": self.created_at.isoformat(), "done": self.done, **totals}

    def detail(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "profile": self.profile,
            "assessment": self.result,
            "messages": self.transcript,
            "done": self.done,
        }
