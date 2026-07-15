from __future__ import annotations

import pytest

from report_engine.settings import Settings, SettingsError


def test_requires_postgres_dsn(monkeypatch) -> None:
    monkeypatch.delenv("PG_DSN", raising=False)

    with pytest.raises(SettingsError, match="PG_DSN is required"):
        Settings.from_environment(require_llm=False)


def test_offline_mode_does_not_require_llm_settings(monkeypatch) -> None:
    monkeypatch.setenv("PG_DSN", "postgresql://fixture")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    settings = Settings.from_environment(require_llm=False)

    assert settings.pg_dsn == "postgresql://fixture"
    assert settings.llm_api_key is None
    assert settings.llm_model is None
