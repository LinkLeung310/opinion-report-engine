from __future__ import annotations

from datetime import date
from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.metrics import MetricsSnapshot
from report_engine.sections.metrics_runner import MetricsSectionRunner
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


def snapshot(article_count: int = 12) -> MetricsSnapshot:
    return MetricsSnapshot(
        article_count=article_count,
        positive_articles=2 if article_count else 0,
        neutral_articles=3 if article_count else 0,
        negative_articles=7 if article_count else 0,
        platform_count=4 if article_count else 0,
        likes=15_460 if article_count else 0,
        comments=4_705 if article_count else 0,
        shares=4_620 if article_count else 0,
        favorites=1_385 if article_count else 0,
        peak_day=date(2026, 3, 20) if article_count else None,
        peak_article_count=3 if article_count else 0,
        query_id="metrics.v1",
    )


class FakeRepository:
    def __init__(self, result: MetricsSnapshot | Exception) -> None:
        self.result = result

    def fetch(self, _scope):
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class FakeChartBuilder:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls = 0

    def build(
        self,
        _snapshot,
        output_directory: Path,
        _language: Language = Language.ZH,
    ) -> Path:
        self.calls += 1
        if self.error:
            raise self.error
        return output_directory / "sentiment-overview.png"


def scope():
    config = ReportConfig.model_validate(sample_config())
    return ReportPlanner(default_registry()).build(config).scope


def test_success_calls_the_narrator_once_with_approved_facts() -> None:
    narrator = StubNarrator()
    chart_builder = FakeChartBuilder()
    runner = MetricsSectionRunner(FakeRepository(snapshot()), chart_builder, narrator)

    result = runner.run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert len(narrator.requests) == 1
    assert chart_builder.calls == 1
    assert result.charts == ("sentiment-overview.png",)
    assert narrator.requests[0].facts.get("negativeRatio").formatted_value == "58.3%"
    assert "58.3%" in result.markdown
    assert "全网数据概览" in result.markdown
    assert "negativeRatio" not in result.markdown


def test_no_data_is_visible_and_does_not_call_the_narrator() -> None:
    narrator = StubNarrator()
    chart_builder = FakeChartBuilder()
    runner = MetricsSectionRunner(
        FakeRepository(snapshot(article_count=0)),
        chart_builder,
        narrator,
    )

    result = runner.run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.NO_DATA
    assert "暂无相关数据" in result.markdown
    assert chart_builder.calls == 0
    assert narrator.requests == []


def test_query_failure_is_safe_and_does_not_stop_the_report_protocol() -> None:
    narrator = StubNarrator()
    repository_error = RuntimeError("postgresql://user:secret@internal.example/report")
    chart_builder = FakeChartBuilder()
    runner = MetricsSectionRunner(FakeRepository(repository_error), chart_builder, narrator)

    result = runner.run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.FAILED
    assert result.failure.stage is FailureStage.QUERY
    assert result.failure.message == "Metrics data query failed"
    assert "secret" not in result.markdown
    assert chart_builder.calls == 0
    assert narrator.requests == []


def test_narrator_failure_is_safe_and_never_retries_at_section_level() -> None:
    narrator = StubNarrator(fail_sections=[SectionId.METRICS])
    chart_builder = FakeChartBuilder()
    runner = MetricsSectionRunner(FakeRepository(snapshot()), chart_builder, narrator)

    result = runner.run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.FAILED
    assert result.failure.stage is FailureStage.LLM
    assert result.failure.message == "Metrics narration failed"
    assert "secret" not in result.markdown
    assert len(narrator.requests) == 1
    assert result.charts == ("sentiment-overview.png",)


def test_chart_failure_stops_before_the_narrator_and_is_safe() -> None:
    narrator = StubNarrator()
    chart_builder = FakeChartBuilder(error=RuntimeError("C:\\private\\secret"))
    runner = MetricsSectionRunner(FakeRepository(snapshot()), chart_builder, narrator)

    result = runner.run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.FAILED
    assert result.failure.stage is FailureStage.CHART
    assert result.failure.message == "Metrics chart rendering failed"
    assert "secret" not in result.markdown
    assert narrator.requests == []
