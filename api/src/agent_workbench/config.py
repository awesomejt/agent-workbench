from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    database_url: str  # required — fails fast if DATABASE_URL is not set
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "dev-insecure-change-me"
    prometheus_enabled: bool = False

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        if v not in {"local", "dev", "stage", "prod"}:
            raise ValueError("APP_ENV must be local, dev, stage, or prod")
        return v

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        env = (info.data.get("app_env") or "")
        if env == "prod" and v == "dev-insecure-change-me":
            raise ValueError("SECRET_KEY must be set to a secure value in prod")
        return v
