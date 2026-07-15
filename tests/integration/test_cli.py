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


def test_cli_generates_verdict_before_metrics_in_configured_order(
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
        {"id": "verdict", "enabled": True},
        {"id": "metrics", "enabled": True},
    ]
    config = tmp_path / "report-config.verdict-metrics.json"
    config.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

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
    markdown = (target / "report.md").read_text(encoding="utf-8")
    assert markdown.index("## 核心结论") < markdown.index("## 全网数据概览")
    assert "代码判定当前风险等级为高" in markdown
    meta = json.loads((target / "meta.json").read_text(encoding="utf-8"))
    assert meta["generatedAt"].endswith("+08:00")
    assert meta["generation"] == {
        "requested": 2,
        "complete": 2,
        "noData": 0,
        "failed": 0,
    }
    assert meta["charts"] == 1


def test_cli_generates_all_review_slices_in_configured_order(
    tmp_path,
    monkeypatch,
) -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    monkeypatch.setenv("PG_DSN", dsn)
    source = Path(__file__).parents[2] / "examples" / "report-config.m1-slices.json"
    raw = json.loads(source.read_text(encoding="utf-8"))
    config = tmp_path / "report-config.trend.json"
    config.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

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
    markdown = (target / "report.md").read_text(encoding="utf-8")
    assert (
        markdown.index("## 全网数据概览")
        < markdown.index("## 热度趋势")
        < markdown.index("## 主要观点")
        < markdown.index("## 平台表现")
        < markdown.index("## 负面严重程度")
        < markdown.index("## 风险评估")
        < markdown.index("## 情感演变")
        < markdown.index("## 关键词与话题")
        < markdown.index("## 互动传播")
        < markdown.index("## 媒体与社媒对比")
    )
    assert (target / "charts" / "daily-sentiment-trend.png").is_file()
    assert (target / "charts" / "platform-performance.png").is_file()
    assert (target / "charts" / "severity-distribution.png").is_file()
    assert (target / "charts" / "risk-signal-index.png").is_file()
    assert (target / "charts" / "sentiment-evolution.png").is_file()
    assert (target / "charts" / "keyword-coverage.png").is_file()
    assert (target / "charts" / "engagement-composition.png").is_file()
    assert (target / "charts" / "media-social-comparison.png").is_file()
    assert "高/危内容 4 篇，占 57.1%" in markdown
    assert "不是完整主题普查" in markdown
    assert "[Evidence: bili-001]" in markdown
    assert "[Evidence: bili-008]" in markdown
    assert "[Evidence: bili-002]" in markdown
    assert "[Evidence: bili-010]" in markdown
    assert "[Evidence: bili-006]" in markdown
    assert "[Evidence: bili-007]" in markdown
    assert "[Evidence: bili-005]" in markdown
    assert "[Evidence: bili-003]" in markdown
    assert "等权诊断指数为 76.0%" in markdown
    assert "不代表事件发生概率" in markdown
    assert "高管关联、谣言核验" in markdown
    assert "后期（3/22-3/23）共 2 篇，负面占比 100.0%" in markdown
    assert "情感构成变化不等于讨论量上升或热度回升" in markdown
    assert "6 项并列最高，均覆盖 2 篇" in markdown
    assert "不等同于语义主题聚类或公众支持度" in markdown
    assert "共记录原始互动 26,170" in markdown
    assert "评论与转发合计 9,325（35.6%）" in markdown
    assert "bili-007 单篇最高，为 10,020，占总互动的 38.3%" in markdown
    assert "前 3 篇合计占 59.1%" in markdown
    assert "不代表互动率、真实触达或支持度" in markdown
    assert "媒体内容 3 篇（25.0%）" in markdown
    assert "社交内容 9 篇（75.0%）" in markdown
    assert "社交减媒体为 +33.3 个百分点" in markdown
    assert "分类直接来自数据库 source_type 字段" in markdown
    meta = json.loads((target / "meta.json").read_text(encoding="utf-8"))
    assert meta["generation"]["complete"] == 11
    assert meta["generation"]["failed"] == 0
    assert meta["charts"] == 9


@pytest.mark.parametrize(
    ("filename", "report_type", "headings", "charts"),
    (
        (
            "report-config.csuite.json",
            "csuite",
            (
                "## 核心结论",
                "## 全网数据概览",
                "## 热度趋势",
                "## 主要观点",
                "## 平台表现",
                "## 负面严重程度",
                "## 风险评估",
            ),
            5,
        ),
        (
            "report-config.pr.json",
            "pr",
            (
                "## 核心结论",
                "## 全网数据概览",
                "## 热度趋势",
                "## 主要观点",
                "## 平台表现",
                "## 负面严重程度",
                "## 风险评估",
                "## 情感演变",
                "## 关键词与话题",
                "## 互动传播",
                "## 媒体与社媒对比",
            ),
            9,
        ),
    ),
)
def test_assignment_default_configs_generate_complete_ordered_bundles(
    tmp_path,
    monkeypatch,
    filename: str,
    report_type: str,
    headings: tuple[str, ...],
    charts: int,
) -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    monkeypatch.setenv("PG_DSN", dsn)
    config = Path(__file__).parents[2] / "examples" / filename

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
    markdown = (target / "report.md").read_text(encoding="utf-8")
    positions = tuple(markdown.index(heading) for heading in headings)
    assert positions == tuple(sorted(positions))
    meta = json.loads((target / "meta.json").read_text(encoding="utf-8"))
    assert meta["reportType"] == report_type
    assert meta["sections"] == len(headings)
    assert meta["generation"] == {
        "requested": len(headings),
        "complete": len(headings),
        "noData": 0,
        "failed": 0,
    }
    assert meta["charts"] == charts
    assert len(list((target / "charts").glob("*.png"))) == charts
    assert (target / "report.pdf").read_bytes().startswith(b"%PDF-")
