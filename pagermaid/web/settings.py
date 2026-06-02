from __future__ import annotations

from typing import Any, List

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WebSettings(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    enabled: bool = False
    login_enabled: bool = False
    secret_key: str = "secret_key"
    host: str = "127.0.0.1"
    port: int = Field(default=3333, ge=1, le=65535)
    allowed_origins: List[str] = Field(default_factory=lambda: ["*"])

    # Defined now, used later when dangerous web operations are isolated.
    enable_shell: bool = False
    enable_eval: bool = False

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def normalize_allowed_origins(cls, value: Any) -> List[str]:
        if value is None:
            return ["*"]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return list(value)

    @classmethod
    def from_legacy_config(cls) -> WebSettings:
        from pagermaid.config import Config

        return cls(
            enabled=bool(Config.WEB_ENABLE),
            login_enabled=bool(Config.WEB_LOGIN),
            secret_key=Config.WEB_SECRET_KEY,
            host=Config.WEB_HOST,
            port=Config.WEB_PORT,
            allowed_origins=Config.WEB_ORIGINS,
        )
