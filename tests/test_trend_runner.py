from __future__ import annotations

from datetime import date
from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.registry import default_registry
from report_engine.sections.trend import DailyTrendPoint, TrendSnapshot
from report_engine.sections.trend_runner import TrendSectionRunner
from tests.test_config import sample_config


def snapshot(has_data: bool = True) -> TrendSnapshot:
    counts = (2, 3, 1) if has_data else (0, 0, 0)
    return TrendSnapshot(
        tuple(DailyTrendPoint(date(2026, 3, 17 + index), count, 0, 0, count) for index, count in enumerate(counts)),
        "trend.v1",
    )


class FakeRepository:
    def __init__(self, result):
        self.result = result

    def fetch(self, _scope):
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class FakeChartBuilder:
    def __init__(self, error=None):
        self.error = error
        self.calls = 0

    def build(self, _snapshot, output_directory: Path):
        self.calls += 1
        if self.error:
            raise self.error
        return output_directory / "daily-sentiment-trend.png"


def scope():
    return ReportPlanner(default_registry()).build(
        ReportConfig.model_validate(sample_config())
    ).scope


def test_success_charts_then_calls_narrator_once() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = TrendSectionRunner(FakeRepository(snapshot()), chart, narrator).run(
        scope(), Language.ZH, Path("charts")
    )
    assert result.status is SectionStatus.COMPLETE
    assert chart.calls == 1 and len(narrator.requests) == 1
    assert result.charts == ("daily-sentiment-trend.png",)
    assert "热度趋势" in result.markdown and "33.3%" in result.markdown


def test_no_data_skips_chart_and_narrator() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = TrendSectionRunner(FakeRepository(snapshot(False)), chart, narrator).run(
        scope(), Language.ZH, Path("charts")
    )
    assert result.status is SectionStatus.NO_DATA
    assert chart.calls == 0 and narrator.requests == []


def test_query_chart_and_narrator_failures_are_safe() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    query = TrendSectionRunner(
        FakeRepository(RuntimeError("secret")), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert query.failure.stage is FailureStage.QUERY and narrator.requests == []

    chart_failure = TrendSectionRunner(
        FakeRepository(snapshot()),
        FakeChartBuilder(RuntimeError("secret")),
        narrator,
    ).run(scope(), Language.ZH, Path("charts"))
    assert chart_failure.failure.stage is FailureStage.CHART and narrator.requests == []

    failing = StubNarrator([SectionId.TREND])
    llm = TrendSectionRunner(
        FakeRepository(snapshot()), FakeChartBuilder(), failing
    ).run(scope(), Language.ZH, Path("charts"))
    assert llm.failure.stage is FailureStage.LLM and len(failing.requests) == 1
    assert llm.charts == ("daily-sentiment-trend.png",)
