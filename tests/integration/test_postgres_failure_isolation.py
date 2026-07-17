from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from report_engine.cli import app
from report_engine.data import postgres


pytestmark = pytest.mark.integration


def test_failed_section_query_does_not_abort_later_sections(
    tmp_path,
    monkeypatch,
) -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    monkeypatch.setenv("PG_DSN", dsn)

    source = Path(__file__).parents[2] / "examples" / "report-config.metrics.json"
    raw = json.loads(source.read_text(encoding="utf-8"))
    raw["sections"] = [
        {"id": "metrics", "enabled": True},
        {"id": "trend", "enabled": True},
    ]
    config = tmp_path / "report-config.failure-isolation.json"
    config.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(postgres, "METRICS_SQL", "SELECT 1 / 0")

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
    meta = json.loads((target / "meta.json").read_text(encoding="utf-8"))
    assert meta["generation"] == {
        "requested": 2,
        "complete": 1,
        "noData": 0,
        "failed": 1,
    }
    assert meta["failures"] == [
        {
            "sectionId": "metrics",
            "stage": "query",
            "message": "Metrics data query failed",
        }
    ]
    assert (target / "charts" / "daily-sentiment-trend.png").is_file()
