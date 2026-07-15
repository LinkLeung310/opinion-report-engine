from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.application.service import ReportApplicationService
from report_engine.charts.metrics import MetricsChartBuilder
from report_engine.config import ReportConfig, SectionId
from report_engine.llm.stub import StubNarrator
from report_engine.rendering.assembler import ReportAssembler
from report_engine.sections.metrics import MetricsSnapshot
from report_engine.sections.metrics_runner import MetricsSectionRunner
from report_engine.sections.registry import default_registry
from report_engine.storage.bundle import BundlePublisher
from tests.test_config import sample_config


class FakeMetricsRepository:
    def fetch(self, _scope) -> MetricsSnapshot:
        return MetricsSnapshot(
            article_count=12,
            positive_articles=2,
            neutral_articles=3,
            negative_articles=7,
            platform_count=4,
            likes=15_460,
            comments=4_705,
            shares=4_620,
            favorites=1_385,
            peak_day=date(2026, 3, 20),
            peak_article_count=3,
            query_id="metrics.v1",
        )


class FakePdfRenderer:
    def render(self, markdown: str, chart_directory: Path) -> bytes:
        assert "58.3%" in markdown
        assert (chart_directory / "sentiment-overview.png").is_file()
        return b"%PDF-1.4\ndeterministic fixture"


def metrics_only_config() -> ReportConfig:
    raw = sample_config()
    raw["topic"] = {
        "tag": "bilibili-dislike",
        "displayName": "B站猜你不喜欢算法调整",
        "eventTitle": "B站猜你不喜欢算法调整事件",
    }
    raw["sections"] = [{"id": "metrics", "enabled": True}]
    return ReportConfig.model_validate(raw)


def build_service(narrator: StubNarrator) -> ReportApplicationService:
    metrics_runner = MetricsSectionRunner(
        repository=FakeMetricsRepository(),
        chart_builder=MetricsChartBuilder(),
        narrator=narrator,
    )
    return ReportApplicationService(
        planner=ReportPlanner(default_registry()),
        section_runners={SectionId.METRICS: metrics_runner},
        assembler=ReportAssembler(),
        pdf_renderer=FakePdfRenderer(),
        publisher=BundlePublisher(),
        clock=lambda: datetime(2026, 7, 15, 2, 0, tzinfo=UTC),
    )


def test_generates_and_publishes_one_complete_metrics_bundle(tmp_path) -> None:
    narrator = StubNarrator()

    result = build_service(narrator).generate(metrics_only_config(), tmp_path / "out")

    target = tmp_path / "out" / "bilibili-dislike-2026-03-23-v1"
    assert result.report_id == target.name
    assert len(narrator.requests) == 1
    assert (target / "report.md").is_file()
    assert (target / "report.pdf").is_file()
    assert (target / "charts" / "sentiment-overview.png").is_file()
    meta = json.loads((target / "meta.json").read_text(encoding="utf-8"))
    assert meta["stats"]["articles"] == 12
    assert meta["stats"]["negativeRatio"] == "58.3%"


def test_allocates_a_new_human_readable_version_without_overwriting(tmp_path) -> None:
    service = build_service(StubNarrator())
    output_root = tmp_path / "out"

    first = service.generate(metrics_only_config(), output_root)
    second = service.generate(metrics_only_config(), output_root)

    assert first.report_id == "bilibili-dislike-2026-03-23-v1"
    assert second.report_id == "bilibili-dislike-2026-03-23-v2"
    assert (output_root / first.report_id).is_dir()
    assert (output_root / second.report_id).is_dir()


def test_unimplemented_sections_become_visible_failures_instead_of_crashing(tmp_path) -> None:
    raw = sample_config()
    raw["sections"] = [
        {"id": "metrics", "enabled": True},
        {"id": "trend", "enabled": True},
    ]

    result = build_service(StubNarrator()).generate(
        ReportConfig.model_validate(raw),
        tmp_path / "out",
    )

    assert result.meta["generation"] == {
        "requested": 2,
        "complete": 1,
        "noData": 0,
        "failed": 1,
    }
    assert result.meta["failures"] == [
        {
            "sectionId": "trend",
            "stage": "input",
            "message": "Section is not implemented",
        }
    ]
