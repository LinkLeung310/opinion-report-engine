from __future__ import annotations

from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.registry import default_registry
from report_engine.sections.severity_runner import SeveritySectionRunner
from tests.test_config import sample_config
from tests.test_severity import empty_snapshot, fixture_snapshot


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
        return output_directory / "severity-distribution.png"


class InvalidCitationNarrator:
    def narrate(self, _request):
        return "## 负面严重程度\n\n- [Evidence: invented] 未经批准的内容。"


class BrokenSnapshot:
    has_data = True

    def to_fact_set(self):
        raise ValueError("synthetic calculation failure")

    def to_evidence_set(self):
        raise AssertionError("must stop after fact failure")


def scope():
    return ReportPlanner(default_registry()).build(
        ReportConfig.model_validate(sample_config())
    ).scope


def test_success_charts_then_calls_narrator_once_with_approved_evidence() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = SeveritySectionRunner(
        FakeRepository(fixture_snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert chart.calls == 1 and len(narrator.requests) == 1
    assert narrator.requests[0].evidence.record_ids == (
        "bili-007",
        "bili-005",
        "bili-003",
    )
    assert result.evidence.record_ids == narrator.requests[0].evidence.record_ids
    assert result.charts == ("severity-distribution.png",)
    assert "高/危内容 4 篇，占 57.1%" in result.markdown
    assert "[Evidence: bili-007]" in result.markdown


def test_no_data_is_a_valid_finding_and_skips_chart_and_narrator() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = SeveritySectionRunner(
        FakeRepository(empty_snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.NO_DATA
    assert "监测范围内未发现负面内容" in result.markdown
    assert chart.calls == 0 and narrator.requests == []


def test_query_calculation_chart_and_narrator_failures_are_safe() -> None:
    narrator = StubNarrator()
    query = SeveritySectionRunner(
        FakeRepository(RuntimeError("secret")), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert query.failure.stage is FailureStage.QUERY and narrator.requests == []

    calculation = SeveritySectionRunner(
        FakeRepository(BrokenSnapshot()), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert calculation.failure.stage is FailureStage.CALCULATION
    assert narrator.requests == []

    chart_failure = SeveritySectionRunner(
        FakeRepository(fixture_snapshot()),
        FakeChartBuilder(RuntimeError("secret")),
        narrator,
    ).run(scope(), Language.ZH, Path("charts"))
    assert chart_failure.failure.stage is FailureStage.CHART
    assert narrator.requests == []

    failing = StubNarrator([SectionId.SEVERITY])
    llm = SeveritySectionRunner(
        FakeRepository(fixture_snapshot()), FakeChartBuilder(), failing
    ).run(scope(), Language.ZH, Path("charts"))
    assert llm.failure.stage is FailureStage.LLM and len(failing.requests) == 1
    assert llm.charts == ("severity-distribution.png",)


def test_unknown_evidence_citation_fails_the_section() -> None:
    result = SeveritySectionRunner(
        FakeRepository(fixture_snapshot()),
        FakeChartBuilder(),
        InvalidCitationNarrator(),
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.FAILED
    assert result.failure.stage is FailureStage.LLM
    assert "invented" not in result.markdown
