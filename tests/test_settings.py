from __future__ import annotations

import pytest

import report_engine.settings as settings_module
from report_engine.settings import Settings, SettingsError


def test_requires_postgres_dsn(monkeypatch) -> None:
    monkeypatch.setattr(settings_module, "load_dotenv", lambda **_: None)
    monkeypatch.delenv("PG_DSN", raising=False)

    with pytest.raises(SettingsError, match="PG_DSN is required"):
        Settings.from_environment(require_llm=False)


def test_offline_mode_does_not_require_llm_settings(monkeypatch) -> None:
    monkeypatch.setattr(settings_module, "load_dotenv", lambda **_: None)
    monkeypatch.setenv("PG_DSN", "postgresql://fixture")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    settings = Settings.from_environment(require_llm=False)

    assert settings.pg_dsn == "postgresql://fixture"
    assert settings.llm_base_url is None
    assert settings.llm_api_key is None
    assert settings.llm_model is None


def test_real_mode_requires_all_llm_settings(monkeypatch) -> None:
    monkeypatch.setattr(settings_module, "load_dotenv", lambda **_: None)
    monkeypatch.setenv("PG_DSN", "postgresql://fixture")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    with pytest.raises(
        SettingsError,
        match=(
            "Missing required settings: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL"
        ),
    ):
        Settings.from_environment(require_llm=True)


def test_real_mode_loads_trimmed_llm_settings(monkeypatch) -> None:
    monkeypatch.setattr(settings_module, "load_dotenv", lambda **_: None)
    monkeypatch.setenv("PG_DSN", " postgresql://fixture ")
    monkeypatch.setenv("LLM_BASE_URL", " https://provider.example/v1/ ")
    monkeypatch.setenv("LLM_API_KEY", " test-key ")
    monkeypatch.setenv("LLM_MODEL", " test-model ")

    settings = Settings.from_environment(require_llm=True)

    assert settings == Settings(
        pg_dsn="postgresql://fixture",
        llm_base_url="https://provider.example/v1/",
        llm_api_key="test-key",
        llm_model="test-model",
    )
