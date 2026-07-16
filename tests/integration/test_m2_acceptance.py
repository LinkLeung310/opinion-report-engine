from __future__ import annotations

import json
import os
from pathlib import Path
import re

from PIL import Image
import psycopg
import pytest
from pypdf import PdfReader
from typer.testing import CliRunner

import report_engine.cli as cli_module
from report_engine.config import Language, ReportConfig, ReportType, SectionId
from report_engine.llm.stub import StubNarrator


pytestmark = pytest.mark.integration

REPOSITORY_ROOT = Path(__file__).parents[2]
EXAMPLE = REPOSITORY_ROOT / "examples" / "report-config.all-sections.en.json"
HAN_TEXT = re.compile(r"[\u3400-\u9fff]+")
ENGLISH_HEADINGS = {
    SectionId.VERDICT: "Executive verdict",
    SectionId.METRICS: "Monitoring overview",
    SectionId.TREND: "Volume trend",
    SectionId.VIEWPOINTS: "Main viewpoints",
    SectionId.PLATFORMS: "Platform performance",
    SectionId.SEVERITY: "Negative severity",
    SectionId.RISK: "Risk assessment",
    SectionId.SENTIMENT_EVOLUTION: "Sentiment evolution",
    SectionId.KEYWORDS: "Keywords and topics",
    SectionId.ENGAGEMENT: "Engagement",
    SectionId.MEDIA_SOCIAL: "Media and social comparison",
    SectionId.TIMELINE: "Event timeline",
    SectionId.TOP_CONTENT: "Representative content",
    SectionId.NEGATIVE_THEMES: "Negative issue themes",
    SectionId.SPREAD_PATH: "Observable platform sequence",
    SectionId.RESPONSE: "Response comparison",
    SectionId.BENCHMARK: "Historical benchmark",
    SectionId.BIZ_IMPACT: "Business impact",
    SectionId.RECOMMENDATIONS: "Recommended actions",
}
EXPECTED_CHARTS = {
    "daily-sentiment-trend.png",
    "engagement-composition.png",
    "event-timeline.png",
    "historical-benchmark-comparison.png",
    "keyword-coverage.png",
    "media-social-comparison.png",
    "negative-theme-coverage.png",
    "platform-performance.png",
    "platform-time-matrix.png",
    "response-window-comparison.png",
    "risk-signal-index.png",
    "sentiment-evolution.png",
    "sentiment-overview.png",
    "severity-distribution.png",
    "top-content-signals.png",
}


def fixture_dsn() -> str:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    return dsn


def load_example() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def run_cli(
    raw: dict,
    tmp_path: Path,
    monkeypatch,
) -> tuple[Path, StubNarrator, dict, str]:
    dsn = fixture_dsn()
    config_path = tmp_path / "report-config.json"
    config_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    narrator = StubNarrator()
    monkeypatch.setenv("PG_DSN", dsn)
    monkeypatch.setattr(cli_module, "StubNarrator", lambda: narrator)

    result = CliRunner().invoke(
        cli_module.app,
        [
            "generate",
            "--config",
            str(config_path),
            "--out",
            str(tmp_path / "out"),
            "--stub-llm",
        ],
    )

    assert result.exit_code == 0, result.output
    bundles = tuple((tmp_path / "out").iterdir())
    assert len(bundles) == 1
    target = bundles[0]
    meta = json.loads((target / "meta.json").read_text(encoding="utf-8"))
    markdown = (target / "report.md").read_text(encoding="utf-8")
    return target, narrator, meta, markdown


def markdown_headings(markdown: str) -> tuple[str, ...]:
    return tuple(line for line in markdown.splitlines() if line.startswith("## "))


def assert_a4_pdf(target: Path, expected_title: str, expected_images: int) -> None:
    reader = PdfReader(target / "report.pdf")
    assert reader.metadata.title == expected_title
    assert reader.pages
    for page in reader.pages:
        assert float(page.mediabox.width) == pytest.approx(595.28, abs=0.5)
        assert float(page.mediabox.height) == pytest.approx(841.89, abs=0.5)
    assert sum(len(page.images) for page in reader.pages) == expected_images


def assert_han_text_comes_from_fixture_sources(markdown: str, topic_tag: str) -> None:
    with psycopg.connect(fixture_dsn()) as connection:
        rows = connection.execute(
            "SELECT title, summary, platform FROM articles WHERE %s = ANY(tags)",
            (topic_tag,),
        ).fetchall()
    source_corpus = "\n".join(str(value) for row in rows for value in row)
    unsupported = sorted(
        {match for match in HAN_TEXT.findall(markdown) if match not in source_corpus}
    )
    assert unsupported == []


def test_all_section_english_example_generates_the_complete_m2_bundle(
    tmp_path,
    monkeypatch,
) -> None:
    raw = load_example()
    config = ReportConfig.model_validate(raw)
    inputs = {section.id: section.input for section in config.sections}

    assert config.report_type is ReportType.PR
    assert config.language is Language.EN
    assert tuple(section.id for section in config.sections) == tuple(SectionId)
    assert all(section.enabled for section in config.sections)
    assert inputs[SectionId.RESPONSE] == {"responseDate": "2026-03-19"}
    assert inputs[SectionId.BENCHMARK] == {
        "comparisonTag": "legacy-feed-controls"
    }
    assert inputs[SectionId.BIZ_IMPACT] == {
        "notes": (
            "Customer-support volume and conversion changes require internal "
            "verification."
        )
    }

    target, narrator, meta, markdown = run_cli(raw, tmp_path, monkeypatch)

    assert tuple(request.section_id for request in narrator.requests) == tuple(SectionId)
    assert markdown_headings(markdown) == tuple(
        f"## {ENGLISH_HEADINGS[section_id]}" for section_id in SectionId
    )
    assert meta["title"] == (
        "Recommendation controls change Public Opinion Analysis Report"
    )
    assert meta["language"] == "en"
    assert meta["reportType"] == "pr"
    assert meta["sections"] == 19
    assert meta["generation"] == {
        "requested": 19,
        "complete": 19,
        "noData": 0,
        "failed": 0,
    }
    assert meta["failures"] == []
    assert meta["stats"] == {
        "articles": 12,
        "negativeRatio": "58.3%",
        "peakDay": "3/20",
    }
    charts = {path.name for path in (target / "charts").glob("*.png")}
    assert charts == EXPECTED_CHARTS
    assert meta["charts"] == len(EXPECTED_CHARTS)
    for chart in (target / "charts").glob("*.png"):
        with Image.open(chart) as image:
            assert image.info["dpi"][0] == pytest.approx(150, abs=0.1)
    assert markdown.count("](charts/") == len(EXPECTED_CHARTS)
    assert_a4_pdf(target, meta["title"], len(EXPECTED_CHARTS))
    assert_han_text_comes_from_fixture_sources(markdown, config.topic.tag)


def test_reordered_mixed_combination_preserves_order_and_special_inputs(
    tmp_path,
    monkeypatch,
) -> None:
    raw = load_example()
    by_id = {section["id"]: section for section in raw["sections"]}
    section_ids = (
        SectionId.BIZ_IMPACT,
        SectionId.METRICS,
        SectionId.RESPONSE,
        SectionId.BENCHMARK,
        SectionId.RECOMMENDATIONS,
    )
    raw["sections"] = [by_id[section_id.value] for section_id in section_ids]

    target, narrator, meta, markdown = run_cli(raw, tmp_path, monkeypatch)

    assert tuple(request.section_id for request in narrator.requests) == section_ids
    assert markdown_headings(markdown) == tuple(
        f"## {ENGLISH_HEADINGS[section_id]}" for section_id in section_ids
    )
    assert meta["generation"] == {
        "requested": 5,
        "complete": 5,
        "noData": 0,
        "failed": 0,
    }
    assert meta["charts"] == 3
    assert {path.name for path in (target / "charts").glob("*.png")} == {
        "sentiment-overview.png",
        "response-window-comparison.png",
        "historical-benchmark-comparison.png",
    }


def test_empty_english_scope_is_all_no_data_without_model_cost(
    tmp_path,
    monkeypatch,
) -> None:
    raw = load_example()
    raw["topic"] = {
        "tag": "no-fixture-topic",
        "displayName": "No fixture topic",
        "eventTitle": "No fixture topic",
    }

    target, narrator, meta, markdown = run_cli(raw, tmp_path, monkeypatch)

    assert narrator.requests == []
    assert markdown_headings(markdown) == tuple(
        f"## {ENGLISH_HEADINGS[section_id]}" for section_id in SectionId
    )
    assert meta["generation"] == {
        "requested": 19,
        "complete": 0,
        "noData": 19,
        "failed": 0,
    }
    assert meta["stats"] == {
        "articles": 0,
        "negativeRatio": "Unavailable",
        "peakDay": "Unavailable",
    }
    assert tuple((target / "charts").iterdir()) == ()
    assert not HAN_TEXT.search(markdown)
    assert_a4_pdf(target, meta["title"], 0)


def test_invalid_special_input_fails_only_that_english_section(
    tmp_path,
    monkeypatch,
) -> None:
    raw = load_example()
    by_id = {section["id"]: section for section in raw["sections"]}
    by_id[SectionId.RESPONSE.value]["input"] = {"responseDate": None}
    section_ids = (SectionId.METRICS, SectionId.RESPONSE, SectionId.TREND)
    raw["sections"] = [by_id[section_id.value] for section_id in section_ids]

    target, narrator, meta, markdown = run_cli(raw, tmp_path, monkeypatch)

    assert tuple(request.section_id for request in narrator.requests) == (
        SectionId.METRICS,
        SectionId.TREND,
    )
    assert markdown_headings(markdown) == tuple(
        f"## {ENGLISH_HEADINGS[section_id]}" for section_id in section_ids
    )
    assert "This section could not be generated" in markdown
    assert meta["generation"] == {
        "requested": 3,
        "complete": 2,
        "noData": 0,
        "failed": 1,
    }
    assert meta["failures"] == [
        {
            "sectionId": "response",
            "stage": "input",
            "message": "Missing required section input: responseDate",
        }
    ]
    assert meta["charts"] == 2
    assert {path.name for path in (target / "charts").glob("*.png")} == {
        "sentiment-overview.png",
        "daily-sentiment-trend.png",
    }
    assert not HAN_TEXT.search(markdown)
