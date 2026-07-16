from __future__ import annotations

from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.registry import default_registry
from report_engine.sections.timeline_runner import TimelineSectionRunner
from tests.test_config import sample_config
from tests.test_timeline import empty_timeline, fixture_snapshot, no_response_snapshot


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
        return output_directory / "event-timeline.png"


class InvalidNarrator:
    def __init__(self, markdown: str):
        self.markdown = markdown
        self.requests = []

    def narrate(self, request):
        self.requests.append(request)
        return self.markdown


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


def test_success_charts_and_calls_narrator_once_with_ordered_evidence() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = TimelineSectionRunner(
        FakeRepository(fixture_snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert chart.calls == 1 and len(narrator.requests) == 1
    assert result.evidence.record_ids == (
        "bili-001",
        "bili-006",
        "bili-007",
        "bili-012",
    )
    assert result.charts == ("event-timeline.png",)
    assert "监测期内共 12 篇收录内容" in result.markdown
    assert "首末收录跨 7 个自然日" in result.markdown
    assert "[Evidence: bili-007]" in result.markdown
    assert "存储互动计数快照：10,020" in result.markdown
    assert "不证明因果" in result.markdown


def test_no_data_skips_chart_and_narrator() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = TimelineSectionRunner(
        FakeRepository(empty_timeline()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.NO_DATA
    assert chart.calls == 0 and narrator.requests == []


def test_missing_response_tag_is_precise_and_english_is_supported() -> None:
    for language, expected in (
        (Language.ZH, "这不等于没有发生回应"),
        (Language.EN, "does not establish that no response occurred"),
    ):
        narrator, chart = StubNarrator(), FakeChartBuilder()
        result = TimelineSectionRunner(
            FakeRepository(no_response_snapshot()), chart, narrator
        ).run(scope(), language, Path("charts"))
        assert result.status is SectionStatus.COMPLETE
        assert expected in result.markdown
        assert "official-response" in result.markdown


def test_query_calculation_chart_and_narrator_failures_are_safe() -> None:
    narrator = StubNarrator()
    query = TimelineSectionRunner(
        FakeRepository(RuntimeError("secret")), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert query.failure.stage is FailureStage.QUERY and narrator.requests == []

    calculation = TimelineSectionRunner(
        FakeRepository(BrokenSnapshot()), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert calculation.failure.stage is FailureStage.CALCULATION

    chart = TimelineSectionRunner(
        FakeRepository(fixture_snapshot()),
        FakeChartBuilder(RuntimeError("secret")),
        narrator,
    ).run(scope(), Language.ZH, Path("charts"))
    assert chart.failure.stage is FailureStage.CHART

    failing = StubNarrator([SectionId.TIMELINE])
    llm = TimelineSectionRunner(
        FakeRepository(fixture_snapshot()), FakeChartBuilder(), failing
    ).run(scope(), Language.ZH, Path("charts"))
    assert llm.failure.stage is FailureStage.LLM and len(failing.requests) == 1
    assert llm.charts == ("event-timeline.png",)


def test_reordered_modified_or_unapproved_evidence_fails_validation() -> None:
    snapshot = fixture_snapshot()
    valid = TimelineSectionRunner(
        FakeRepository(snapshot), FakeChartBuilder(), StubNarrator()
    ).run(scope(), Language.ZH, Path("charts"))
    valid_lines = [
        line for line in valid.markdown.splitlines() if "[Evidence:" in line
    ]
    first = snapshot.to_evidence_set().records[0]
    invalid_markdown = (
        "\n".join(reversed(valid_lines)),
        valid.markdown.replace(first.summary, "改写摘要"),
        valid.markdown.replace("首次收录", "自定义阶段", 1),
        valid.markdown + "\n[Evidence: invented] 未批准记录",
    )
    for markdown in invalid_markdown:
        result = TimelineSectionRunner(
            FakeRepository(snapshot),
            FakeChartBuilder(),
            InvalidNarrator(markdown),
        ).run(scope(), Language.ZH, Path("charts"))
        assert result.status is SectionStatus.FAILED
        assert result.failure.stage is FailureStage.LLM
        assert "invented" not in result.markdown
