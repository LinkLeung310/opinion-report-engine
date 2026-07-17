from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

import report_engine.settings as settings_module
from report_engine.cli import app


CONFIG = Path(__file__).parents[1] / "examples" / "report-config.metrics.json"


def test_cli_real_mode_reports_missing_llm_settings_before_database_use(
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings_module, "load_dotenv", lambda **_: None)
    monkeypatch.setenv("PG_DSN", "postgresql://must-not-be-used")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    result = CliRunner().invoke(app, ["generate", "--config", str(CONFIG)])

    assert result.exit_code == 2
    assert (
        "Configuration error: Missing required settings: "
        "LLM_BASE_URL, LLM_API_KEY, LLM_MODEL"
    ) in result.output


def test_cli_real_mode_rejects_an_unsafe_base_url_without_exposing_key(
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings_module, "load_dotenv", lambda **_: None)
    monkeypatch.setenv("PG_DSN", "postgresql://must-not-be-used")
    monkeypatch.setenv("LLM_BASE_URL", "https://user:password@example.test/v1")
    monkeypatch.setenv("LLM_API_KEY", "secret-test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    result = CliRunner().invoke(app, ["generate", "--config", str(CONFIG)])

    assert result.exit_code == 2
    assert "base_url must not contain embedded credentials" in result.output
    assert "secret-test-key" not in result.output
