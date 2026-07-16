from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.registry import default_registry
from report_engine.sections.response import ResponseObservation, ResponseSnapshot
from report_engine.sections.response_runner import ResponseSectionRunner
from tests.test_config import sample_config
from tests.test_response import fixture_snapshot


class FakeRepository:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def fetch(self, query_scope, response_date):
        self.calls.append((query_scope, response_date))
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
        return output_directory / "response-window-comparison.png"


class BrokenSnapshot:
    has_comparison_data = True

    def to_fact_set(self):
        raise ValueError("synthetic calculation failure")


def scope():
    return ReportPlanner(default_registry()).build(
        ReportConfig.model_validate(sample_config())
    ).scope


def input_value(value="2026-03-19"):
    return {"responseDate": value}


def no_comparison_snapshot(with_scoped_records: bool) -> ResponseSnapshot:
    fixture = fixture_snapshot()
    observations = (
        (
            ResponseObservation(date(2026, 3, 19), "positive", True),
            ResponseObservation(date(2026, 3, 23), "negative", False),
        )
        if with_scoped_records
        else ()
    )
    return ResponseSnapshot(fixture.window, observations, fixture.query_id)


def one_sided_snapshot() -> ResponseSnapshot:
    fixture = fixture_snapshot()
    return ResponseSnapshot(
        fixture.window,
        (ResponseObservation(date(2026, 3, 20), "negative", False),),
        fixture.query_id,
    )


def test_success_calls_repository_chart_and_narrator_once() -> None:
    repository = FakeRepository(fixture_snapshot())
    chart, narrator = FakeChartBuilder(), StubNarrator()
    result = ResponseSectionRunner(repository, chart, narrator).run(
        scope(), Language.ZH, Path("charts"), input_value()
    )

    assert result.status is SectionStatus.COMPLETE
    assert repository.calls[0][1] == date(2026, 3, 19)
    assert chart.calls == 1 and len(narrator.requests) == 1
    assert narrator.requests[0].evidence.records == ()
    assert result.charts == ("response-window-comparison.png",)
    assert "回应前等长 2 日窗口（3/17-3/18）收录 4 篇" in result.markdown
    assert "正面、中性、负面占比差依次为 +25.0 个百分点" in result.markdown
    assert "回应日整体排除" in result.markdown
    assert "不建立因果关系、反事实，也不证明回应效果" in result.markdown


def test_english_narration_preserves_observational_limit() -> None:
    result = ResponseSectionRunner(
        FakeRepository(fixture_snapshot()), FakeChartBuilder(), StubNarrator()
    ).run(scope(), Language.EN, Path("charts"), input_value())

    assert result.status is SectionStatus.COMPLETE
    assert "## Response comparison" in result.markdown
    assert "matched 2-day pre-response window (3/17-3/18)" in result.markdown
    assert "entire response date is excluded" in result.markdown
    assert "do not establish causality, a counterfactual" in result.markdown


@pytest.mark.parametrize(
    "section_input",
    (None, {}, input_value("2026-3-19"), input_value("2026-03-17")),
)
def test_missing_malformed_and_boundary_input_fail_before_query(section_input) -> None:
    repository, chart, narrator = (
        FakeRepository(fixture_snapshot()),
        FakeChartBuilder(),
        StubNarrator(),
    )
    result = ResponseSectionRunner(repository, chart, narrator).run(
        scope(), Language.ZH, Path("charts"), section_input
    )

    assert result.status is SectionStatus.FAILED
    assert result.failure.stage is FailureStage.INPUT
    assert "responseDate" in result.failure.message
    assert repository.calls == [] and chart.calls == 0 and narrator.requests == []


@pytest.mark.parametrize("with_scoped_records", (False, True))
def test_no_comparison_data_retains_facts_and_skips_chart_and_narrator(
    with_scoped_records: bool,
) -> None:
    snapshot = no_comparison_snapshot(with_scoped_records)
    chart, narrator = FakeChartBuilder(), StubNarrator()
    result = ResponseSectionRunner(
        FakeRepository(snapshot), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"), input_value())

    assert result.status is SectionStatus.NO_DATA
    assert result.facts.get("comparisonArticles").raw_value == 0
    assert chart.calls == 0 and narrator.requests == []
    expected = "等长的回应前后窗口内暂无记录" if with_scoped_records else "暂无相关数据"
    assert expected in result.markdown


def test_one_zero_side_remains_complete_and_marks_denominators_unavailable() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = ResponseSectionRunner(
        FakeRepository(one_sided_snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"), input_value())

    assert result.status is SectionStatus.COMPLETE
    assert chart.calls == 1 and len(narrator.requests) == 1
    assert result.facts.get("preNegativeShare").raw_value is None
    assert "不可用" in result.markdown


def test_query_calculation_chart_and_narrator_failures_are_safe() -> None:
    narrator = StubNarrator()
    query = ResponseSectionRunner(
        FakeRepository(RuntimeError("secret")), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"), input_value())
    assert query.failure.stage is FailureStage.QUERY and narrator.requests == []

    calculation = ResponseSectionRunner(
        FakeRepository(BrokenSnapshot()), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"), input_value())
    assert calculation.failure.stage is FailureStage.CALCULATION

    chart = ResponseSectionRunner(
        FakeRepository(fixture_snapshot()),
        FakeChartBuilder(RuntimeError("secret")),
        narrator,
    ).run(scope(), Language.ZH, Path("charts"), input_value())
    assert chart.failure.stage is FailureStage.CHART

    failing = StubNarrator([SectionId.RESPONSE])
    llm = ResponseSectionRunner(
        FakeRepository(fixture_snapshot()), FakeChartBuilder(), failing
    ).run(scope(), Language.ZH, Path("charts"), input_value())
    assert llm.failure.stage is FailureStage.LLM and len(failing.requests) == 1
    assert llm.charts == ("response-window-comparison.png",)
    assert "secret" not in llm.markdown
