"""Environment-backed runtime settings without secret defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


class SettingsError(ValueError):
    """Raised when required runtime configuration is missing."""


@dataclass(frozen=True)
class Settings:
    pg_dsn: str
    llm_base_url: str | None
    llm_api_key: str | None
    llm_model: str | None

    @classmethod
    def from_environment(cls, *, require_llm: bool) -> "Settings":
        load_dotenv(override=False)
        pg_dsn = os.getenv("PG_DSN", "").strip()
        if not pg_dsn:
            raise SettingsError("PG_DSN is required")

        llm_base_url = cls._optional("LLM_BASE_URL")
        llm_api_key = cls._optional("LLM_API_KEY")
        llm_model = cls._optional("LLM_MODEL")
        if require_llm:
            missing = [
                name
                for name, value in (
                    ("LLM_BASE_URL", llm_base_url),
                    ("LLM_API_KEY", llm_api_key),
                    ("LLM_MODEL", llm_model),
                )
                if value is None
            ]
            if missing:
                raise SettingsError(f"Missing required settings: {', '.join(missing)}")

        return cls(
            pg_dsn=pg_dsn,
            llm_base_url=llm_base_url,
            llm_api_key=llm_api_key,
            llm_model=llm_model,
        )

    @staticmethod
    def _optional(name: str) -> str | None:
        value = os.getenv(name, "").strip()
        return value or None
