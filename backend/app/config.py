from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "LegalLens"
    APP_VERSION: str = "3.0"
    DEBUG: bool = False
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/legallens"
    DATABASE_ECHO: bool = False

    # Authentication
    SECRET_KEY: str = Field(
        default="",
        min_length=32,
        description="Secret key for JWT signing - MUST be set in production",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate SECRET_KEY is properly set."""
        if not v or len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters. "
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        # Check for default/weak values
        weak_keys = [
            "change-this",
            "secret",
            "password",
            "12345",
            "default",
        ]
        if any(weak in v.lower() for weak in weak_keys):
            raise ValueError(
                "SECRET_KEY appears to be a default/weak value. "
                "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        return v

    # File Storage
    STORAGE_PROVIDER: Literal["local", "s3", "r2"] = "local"
    STORAGE_LOCAL_PATH: str = "./uploads"

    # S3/R2 Configuration
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "legallens-documents"
    S3_ENDPOINT_URL: str = ""  # For Cloudflare R2

    # File Retention
    FILE_RETENTION_DAYS: int = 7

    # LLM Configuration
    LLM_PROVIDER: Literal["openai", "anthropic", "local"] = "local"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 2000

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60


settings = Settings()
