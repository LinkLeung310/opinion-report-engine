from __future__ import annotations

from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.platforms import PlatformsSnapshot
from report_engine.sections.platforms_runner import PlatformsSectionRunner
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config
from tests.test_platforms import fixture_snapshot


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
        return output_directory / "platform-performance.png"


def scope():
    return ReportPlanner(default_registry()).build(
        ReportConfig.model_validate(sample_config())
    ).scope


def test_success_charts_then_calls_narrator_once() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = PlatformsSectionRunner(
        FakeRepository(fixture_snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert chart.calls == 1 and len(narrator.requests) == 1
    assert result.charts == ("platform-performance.png",)
    assert "微博、B站均为 4 篇" in result.markdown
    assert "15,715" in result.markdown


def test_no_data_skips_chart_and_narrator() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    empty = PlatformsSnapshot((), "platforms.v1")
    result = PlatformsSectionRunner(FakeRepository(empty), chart, narrator).run(
        scope(), Language.ZH, Path("charts")
    )

    assert result.status is SectionStatus.NO_DATA
    assert chart.calls == 0 and narrator.requests == []


def test_query_chart_and_narrator_failures_are_safe() -> None:
    narrator = StubNarrator()
    query = PlatformsSectionRunner(
        FakeRepository(RuntimeError("secret")), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert query.failure.stage is FailureStage.QUERY and narrator.requests == []

    chart_failure = PlatformsSectionRunner(
        FakeRepository(fixture_snapshot()),
        FakeChartBuilder(RuntimeError("secret")),
        narrator,
    ).run(scope(), Language.ZH, Path("charts"))
    assert chart_failure.failure.stage is FailureStage.CHART
    assert narrator.requests == []

    failing = StubNarrator([SectionId.PLATFORMS])
    llm = PlatformsSectionRunner(
        FakeRepository(fixture_snapshot()), FakeChartBuilder(), failing
    ).run(scope(), Language.ZH, Path("charts"))
    assert llm.failure.stage is FailureStage.LLM and len(failing.requests) == 1
    assert llm.charts == ("platform-performance.png",)
