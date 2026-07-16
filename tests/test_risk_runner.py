from __future__ import annotations

from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.registry import default_registry
from report_engine.sections.risk import RiskSnapshot
from report_engine.sections.risk_runner import RiskSectionRunner
from tests.test_config import sample_config
from tests.test_risk import empty_snapshot, fixture_snapshot


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

    def build(
        self,
        _snapshot,
        output_directory: Path,
        _language: Language = Language.ZH,
    ):
        self.calls += 1
        if self.error:
            raise self.error
        return output_directory / "risk-signal-index.png"


class BrokenSnapshot:
    has_data = True

    def to_fact_set(self):
        raise ValueError("synthetic calculation failure")


def scope():
    return ReportPlanner(default_registry()).build(
        ReportConfig.model_validate(sample_config())
    ).scope


def zero_negative_snapshot() -> RiskSnapshot:
    return RiskSnapshot(
        article_count=2,
        negative_articles=0,
        high_critical_negative_articles=0,
        platform_count=1,
        negative_platform_count=0,
        calendar_days=7,
        negative_active_days=0,
        total_engagement=100,
        negative_engagement=0,
        query_id="risk.v1",
    )


def test_success_charts_then_calls_narrator_once_without_article_evidence() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = RiskSectionRunner(
        FakeRepository(fixture_snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert chart.calls == 1 and len(narrator.requests) == 1
    assert narrator.requests[0].evidence.records == ()
    assert result.charts == ("risk-signal-index.png",)
    assert "等权诊断指数为 76.0%" in result.markdown
    assert "不代表事件发生概率" in result.markdown
    assert "高管关联、谣言核验" in result.markdown


def test_no_data_skips_chart_and_narrator() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = RiskSectionRunner(
        FakeRepository(empty_snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.NO_DATA
    assert chart.calls == 0 and narrator.requests == []


def test_zero_negative_scope_remains_complete_with_explicit_zero_signals() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = RiskSectionRunner(
        FakeRepository(zero_negative_snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert chart.calls == 1 and len(narrator.requests) == 1
    assert "等权诊断指数为 0.0%" in result.markdown
    assert "互动放大压力为 0.0%（低）" in result.markdown


def test_query_calculation_chart_and_narrator_failures_are_safe() -> None:
    narrator = StubNarrator()
    query = RiskSectionRunner(
        FakeRepository(RuntimeError("secret")), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert query.failure.stage is FailureStage.QUERY and narrator.requests == []

    calculation = RiskSectionRunner(
        FakeRepository(BrokenSnapshot()), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert calculation.failure.stage is FailureStage.CALCULATION
    assert narrator.requests == []

    chart_failure = RiskSectionRunner(
        FakeRepository(fixture_snapshot()),
        FakeChartBuilder(RuntimeError("secret")),
        narrator,
    ).run(scope(), Language.ZH, Path("charts"))
    assert chart_failure.failure.stage is FailureStage.CHART
    assert narrator.requests == []

    failing = StubNarrator([SectionId.RISK])
    llm = RiskSectionRunner(
        FakeRepository(fixture_snapshot()), FakeChartBuilder(), failing
    ).run(scope(), Language.ZH, Path("charts"))
    assert llm.failure.stage is FailureStage.LLM and len(failing.requests) == 1
    assert llm.charts == ("risk-signal-index.png",)
