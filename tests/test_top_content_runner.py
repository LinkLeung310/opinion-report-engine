from __future__ import annotations

from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.registry import default_registry
from report_engine.sections.top_content import TopContentSnapshot
from report_engine.sections.top_content_runner import TopContentSectionRunner
from tests.test_config import sample_config
from tests.test_top_content import empty_snapshot, fixture_snapshot


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
        return output_directory / "top-content-signals.png"


class InvalidNarrator:
    def __init__(self, markdown: str):
        self.markdown = markdown
        self.requests = []

    def narrate(self, request):
        self.requests.append(request)
        return self.markdown


class BrokenSnapshot:
    has_articles = True

    def to_fact_set(self):
        raise ValueError("synthetic calculation failure")

    def to_evidence_set(self):
        raise AssertionError("must stop after fact failure")


def scope():
    return ReportPlanner(default_registry()).build(
        ReportConfig.model_validate(sample_config())
    ).scope


def no_signal_snapshot() -> TopContentSnapshot:
    return TopContentSnapshot(2, 0, 0, 0, (), "top-content.v1")


def test_success_charts_then_calls_narrator_once_with_ordered_evidence() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = TopContentSectionRunner(
        FakeRepository(fixture_snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert chart.calls == 1 and len(narrator.requests) == 1
    assert result.evidence.record_ids == (
        "bili-007",
        "bili-005",
        "bili-010",
        "bili-003",
    )
    assert result.charts == ("top-content-signals.png",)
    assert "入选 4 篇去重代表内容" in result.markdown
    assert "双信号 2 篇" in result.markdown
    assert "16,890（占全部存储互动 64.5%）" in result.markdown
    assert "[Evidence: bili-003]" in result.markdown
    assert "不能据此推断触达、支持度、业务后果、伤害或因果影响" in result.markdown


def test_no_data_and_no_signal_paths_skip_chart_and_narrator() -> None:
    for snapshot, expected_status, expected_text in (
        (empty_snapshot(), SectionStatus.NO_DATA, "暂无可用于代表性内容分析"),
        (no_signal_snapshot(), SectionStatus.COMPLETE, "无符合条件信号结论"),
    ):
        narrator, chart = StubNarrator(), FakeChartBuilder()
        result = TopContentSectionRunner(
            FakeRepository(snapshot), chart, narrator
        ).run(scope(), Language.ZH, Path("charts"))
        assert result.status is expected_status
        assert expected_text in result.markdown
        assert chart.calls == 0 and narrator.requests == []


def test_english_narration_preserves_explicit_signal_limits() -> None:
    narrator = StubNarrator()
    result = TopContentSectionRunner(
        FakeRepository(fixture_snapshot()), FakeChartBuilder(), narrator
    ).run(scope(), Language.EN, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert "## Representative content" in result.markdown
    assert "dual-signal representatives" in result.markdown
    assert "supplied structured fields" in result.markdown
    assert "not applicable" in result.markdown


def test_query_calculation_chart_and_narrator_failures_are_safe() -> None:
    narrator = StubNarrator()
    query = TopContentSectionRunner(
        FakeRepository(RuntimeError("secret")), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert query.failure.stage is FailureStage.QUERY and narrator.requests == []

    calculation = TopContentSectionRunner(
        FakeRepository(BrokenSnapshot()), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert calculation.failure.stage is FailureStage.CALCULATION

    chart = TopContentSectionRunner(
        FakeRepository(fixture_snapshot()),
        FakeChartBuilder(RuntimeError("secret")),
        narrator,
    ).run(scope(), Language.ZH, Path("charts"))
    assert chart.failure.stage is FailureStage.CHART

    failing = StubNarrator([SectionId.TOP_CONTENT])
    llm = TopContentSectionRunner(
        FakeRepository(fixture_snapshot()), FakeChartBuilder(), failing
    ).run(scope(), Language.ZH, Path("charts"))
    assert llm.failure.stage is FailureStage.LLM and len(failing.requests) == 1
    assert llm.charts == ("top-content-signals.png",)
    assert "secret" not in llm.markdown


def test_reordered_modified_or_unapproved_evidence_fails_validation() -> None:
    snapshot = fixture_snapshot()
    valid = TopContentSectionRunner(
        FakeRepository(snapshot), FakeChartBuilder(), StubNarrator()
    ).run(scope(), Language.ZH, Path("charts"))
    valid_lines = [
        line for line in valid.markdown.splitlines() if "[Evidence:" in line
    ]
    first = snapshot.to_evidence_set().records[0]
    invalid_markdown = (
        "\n".join(reversed(valid_lines)),
        valid.markdown.replace(first.summary, "改写摘要"),
        valid.markdown.replace("双信号代表", "自定义影响代表", 1),
        valid.markdown.replace("10,020", "10,021", 1),
        valid.markdown + "\n[Evidence: invented] 未批准记录",
    )
    for markdown in invalid_markdown:
        result = TopContentSectionRunner(
            FakeRepository(snapshot),
            FakeChartBuilder(),
            InvalidNarrator(markdown),
        ).run(scope(), Language.ZH, Path("charts"))
        assert result.status is SectionStatus.FAILED
        assert result.failure.stage is FailureStage.LLM
        assert "invented" not in result.markdown
