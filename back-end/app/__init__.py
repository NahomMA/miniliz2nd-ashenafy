"""Application factory."""
from __future__ import annotations

import logging
from datetime import timedelta

from flask import Flask
from flask_cors import CORS

from .ai.bedrock import BedrockChatModel
from .ai.service import ChatService
from .config import Settings
from .errors import register_error_handlers
from .models import User, db
from .security import TokenService
from .services.calculator_gateway import CalculatorGateway

MAX_BODY_BYTES = 64 * 1024


def create_app(settings: Settings | None = None) -> Flask:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = settings or Settings.from_env()

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        MAX_CONTENT_LENGTH=MAX_BODY_BYTES,
    )
    app.json.sort_keys = False
    app.extensions["settings"] = settings
    app.extensions["tokens"] = TokenService(settings.secret_key, timedelta(hours=settings.token_ttl_hours))
    app.extensions["calculator"] = calculator = CalculatorGateway()
    model = BedrockChatModel(
        settings.bedrock_model_id, settings.aws_region, settings.bedrock_guardrail_id, settings.bedrock_guardrail_version
    )
    scope_model = BedrockChatModel(settings.bedrock_scope_model_id, settings.aws_region) if settings.bedrock_scope_model_id else None
    app.extensions["chat"] = ChatService(model, calculator, scope_model)

    db.init_app(app)
    CORS(app, origins=settings.cors_origins)
    register_error_handlers(app)
    _register_routes(app)

    with app.app_context():
        db.create_all()
        if settings.seed_demo_user:
            _seed_demo_user(settings)
    return app


def _register_routes(app: Flask) -> None:
    from .routes import assessments, auth, calculator

    for blueprint in (auth.bp, calculator.bp, assessments.bp):
        app.register_blueprint(blueprint)

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.after_request
    def secure_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response


def _seed_demo_user(settings: Settings) -> None:
    if User.find_by_email(settings.demo_email) is None:
        db.session.add(User.create(settings.demo_email, "Maria Demo", settings.demo_password))
        db.session.commit()
