from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from report_engine.cli import app


pytestmark = pytest.mark.integration


def test_cli_generates_a_complete_metrics_bundle(tmp_path, monkeypatch) -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    monkeypatch.setenv("PG_DSN", dsn)
    config = Path(__file__).parents[2] / "examples" / "report-config.metrics.json"

    result = CliRunner().invoke(
        app,
        [
            "generate",
            "--config",
            str(config),
            "--out",
            str(tmp_path / "out"),
            "--stub-llm",
        ],
    )

    assert result.exit_code == 0, result.output
    target = tmp_path / "out" / "bilibili-dislike-2026-03-23-v1"
    assert (target / "report.md").is_file()
    assert (target / "report.pdf").is_file()
    assert (target / "charts" / "sentiment-overview.png").is_file()
    meta = json.loads((target / "meta.json").read_text(encoding="utf-8"))
    assert meta["stats"] == {
        "articles": 12,
        "negativeRatio": "58.3%",
        "peakDay": "3/20",
    }
