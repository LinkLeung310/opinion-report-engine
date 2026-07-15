from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.registry import default_registry
from report_engine.sections.sentiment_evolution import (
    DailySentimentPoint,
    SentimentEvolutionSnapshot,
)
from report_engine.sections.sentiment_evolution_runner import (
    SentimentEvolutionSectionRunner,
)
from tests.test_config import sample_config


def snapshot(counts=((2, 2, 2), (0, 0, 0), (0, 0, 2))):
    return SentimentEvolutionSnapshot(
        tuple(
            DailySentimentPoint(
                date(2026, 3, 17) + timedelta(days=index),
                sum(sentiments),
                sentiments[0],
                sentiments[1],
                sentiments[2],
            )
            for index, sentiments in enumerate(counts)
        ),
        "sentiment-evolution.v1",
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
        return output_directory / "sentiment-evolution.png"


class BrokenFactsSnapshot:
    has_data = True

    def to_fact_set(self):
        raise ArithmeticError("secret")


def scope():
    return ReportPlanner(default_registry()).build(
        ReportConfig.model_validate(sample_config())
    ).scope


def test_success_charts_then_calls_narrator_once_without_evidence() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = SentimentEvolutionSectionRunner(
        FakeRepository(snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert chart.calls == 1 and len(narrator.requests) == 1
    assert not narrator.requests[0].evidence.records
    assert result.charts == ("sentiment-evolution.png",)
    assert "负面占比 100.0%" in result.markdown
    assert "共 2 篇" in result.markdown
    assert "热度回升" in result.markdown


def test_no_data_skips_chart_and_narrator() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = SentimentEvolutionSectionRunner(
        FakeRepository(snapshot(((0, 0, 0),) * 3)), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.NO_DATA
    assert chart.calls == 0 and narrator.requests == []


def test_single_populated_phase_is_complete_but_does_not_invent_a_trend() -> None:
    narrator = StubNarrator()
    result = SentimentEvolutionSectionRunner(
        FakeRepository(snapshot(((0, 0, 0), (0, 1, 1), (0, 0, 0)))),
        FakeChartBuilder(),
        narrator,
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert "不足以进行阶段比较" in result.markdown
    assert "百分点" not in result.markdown


def test_query_calculation_chart_and_narrator_failures_are_safe() -> None:
    narrator = StubNarrator()
    query = SentimentEvolutionSectionRunner(
        FakeRepository(RuntimeError("secret")), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert query.failure.stage is FailureStage.QUERY and narrator.requests == []

    calculation = SentimentEvolutionSectionRunner(
        FakeRepository(BrokenFactsSnapshot()), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert calculation.failure.stage is FailureStage.CALCULATION

    chart = SentimentEvolutionSectionRunner(
        FakeRepository(snapshot()),
        FakeChartBuilder(RuntimeError("secret")),
        narrator,
    ).run(scope(), Language.ZH, Path("charts"))
    assert chart.failure.stage is FailureStage.CHART

    failing = StubNarrator([SectionId.SENTIMENT_EVOLUTION])
    llm = SentimentEvolutionSectionRunner(
        FakeRepository(snapshot()), FakeChartBuilder(), failing
    ).run(scope(), Language.ZH, Path("charts"))
    assert llm.failure.stage is FailureStage.LLM and len(failing.requests) == 1
    assert llm.charts == ("sentiment-evolution.png",)
