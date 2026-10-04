"""Application settings, read once from the environment."""
from __future__ import annotations

import logging
import os
import secrets
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv

log = logging.getLogger(__name__)
MIN_SECRET_LENGTH = 32


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_url: str = "sqlite:///app.db"
    environment: str = "development"
    token_ttl_hours: int = 24
    cors_origins: str = "*"
    seed_demo_user: bool = True
    demo_email: str = "demo@codelinc.app"
    demo_password: str = "Demo2026!"
    aws_region: str = "us-east-2"
    bedrock_model_id: str = "us.amazon.nova-pro-v1:0"
    bedrock_scope_model_id: str = "us.amazon.nova-lite-v1:0"
    bedrock_guardrail_id: str = "2mjbvbps2zrd"  # created by scripts.create_guardrail; set to "" to disable
    bedrock_guardrail_version: str = "2"

    def __post_init__(self) -> None:
        if len(self.secret_key) < MIN_SECRET_LENGTH:
            raise ValueError(f"SECRET_KEY must be at least {MIN_SECRET_LENGTH} characters")

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv(find_dotenv(usecwd=True))
        environment = os.getenv("APP_ENV", "development")
        secret = os.getenv("SECRET_KEY", "")
        if not secret:
            if environment == "production":
                raise ValueError("SECRET_KEY is required in production")
            secret = secrets.token_urlsafe(48)
            log.warning("SECRET_KEY not set: using a temporary key. Tokens stop working when the server restarts.")
        return cls(
            secret_key=secret,
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            environment=environment,
            token_ttl_hours=int(os.getenv("TOKEN_TTL_HOURS", cls.token_ttl_hours)),
            cors_origins=os.getenv("CORS_ORIGINS", cls.cors_origins),
            seed_demo_user=os.getenv("SEED_DEMO_USER", "true").lower() == "true",
            demo_email=os.getenv("DEMO_EMAIL", cls.demo_email),
            demo_password=os.getenv("DEMO_PASSWORD", cls.demo_password),
            aws_region=os.getenv("AWS_REGION", cls.aws_region),
            bedrock_model_id=os.getenv("BEDROCK_MODEL_ID", cls.bedrock_model_id),
            bedrock_scope_model_id=os.getenv("BEDROCK_SCOPE_MODEL_ID", cls.bedrock_scope_model_id),
            bedrock_guardrail_id=os.getenv("BEDROCK_GUARDRAIL_ID", cls.bedrock_guardrail_id),
            bedrock_guardrail_version=os.getenv("BEDROCK_GUARDRAIL_VERSION", cls.bedrock_guardrail_version),
        )
