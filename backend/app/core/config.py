from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


class Settings(BaseSettings):
    _backend_dir = Path(__file__).resolve().parents[2]  # backend/
    _env_path = _backend_dir / ".env"

    # Ensure .env is loaded even when running uvicorn from a different CWD.
    load_dotenv(dotenv_path=_env_path, override=False)

    model_config = SettingsConfigDict(extra="ignore")

    app_name: str = "Health Care Bot MVP"
    # Comma-separated. Include 127.0.0.1 + localhost — browsers treat them as different origins.
    cors_origins: str = Field(
        default="http://localhost:4200,http://127.0.0.1:4200",
        validation_alias="CORS_ORIGINS",
    )

    database_url: str = "sqlite:///./health_bot.db"

    openrouter_api_key: str | None = Field(default=None, validation_alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openrouter/free", validation_alias="OPENROUTER_MODEL")
    openrouter_multimodal_model: str | None = Field(default=None, validation_alias="OPENROUTER_MULTIMODAL_MODEL")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", validation_alias="OPENROUTER_BASE_URL")
    openrouter_timeout_s: float = Field(default=20.0, validation_alias="OPENROUTER_TIMEOUT_S")

    # Optional few-shot examples for triage style (JSON/JSONL built from dataset)
    triage_examples_path: str | None = Field(default=None, validation_alias="TRIAGE_EXAMPLES_PATH")
    triage_examples_limit: int = Field(default=6, validation_alias="TRIAGE_EXAMPLES_LIMIT")

    # Data-driven triage rules (JSON). Default: backend/app/data/triage_rules.json
    triage_rules_path: str | None = Field(default=None, validation_alias="TRIAGE_RULES_PATH")

    # --- Appointment booking / email ---
    smtp_host: str | None = Field(default=None, validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, validation_alias="SMTP_USER")
    smtp_pass: str | None = Field(default=None, validation_alias="SMTP_PASS")
    smtp_from: str | None = Field(default=None, validation_alias="SMTP_FROM")
    public_base_url: str = Field(default="http://localhost:8000", validation_alias="PUBLIC_BASE_URL")
    appointment_token_secret: str = Field(default="dev-secret-change-me", validation_alias="APPOINTMENT_TOKEN_SECRET")


settings = Settings()

