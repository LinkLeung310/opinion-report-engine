from __future__ import annotations

from datetime import date
from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.registry import default_registry
from report_engine.sections.spread_path import SpreadPathSnapshot
from report_engine.sections.spread_path_runner import SpreadPathSectionRunner
from tests.test_config import sample_config
from tests.test_spread_path import fixture_snapshot, record


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
        return output_directory / "platform-time-matrix.png"


class InvalidNarrator:
    def __init__(self, markdown: str):
        self.markdown = markdown
        self.requests = []

    def narrate(self, request):
        self.requests.append(request)
        return self.markdown


class BrokenSnapshot:
    def to_fact_set(self):
        raise ValueError("synthetic calculation failure")

    def to_evidence_set(self):
        raise AssertionError("must stop after fact failure")


def scope():
    return ReportPlanner(default_registry()).build(
        ReportConfig.model_validate(sample_config())
    ).scope


def empty_snapshot() -> SpreadPathSnapshot:
    return SpreadPathSnapshot(
        date(2026, 3, 17), date(2026, 3, 23), (), "Asia/Shanghai", "spread-path.v1"
    )


def single_platform_snapshot() -> SpreadPathSnapshot:
    return SpreadPathSnapshot(
        date(2026, 3, 17),
        date(2026, 3, 23),
        (
            record("one", "单平台", 0, 9),
            record("two", "单平台", 2, 9, sentiment="negative"),
        ),
        "Asia/Shanghai",
        "spread-path.v1",
    )


def test_success_charts_then_calls_narrator_once_with_first_record_order() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = SpreadPathSectionRunner(
        FakeRepository(fixture_snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert chart.calls == 1 and len(narrator.requests) == 1
    assert result.evidence.record_ids == (
        "bili-001",
        "bili-002",
        "bili-003",
        "bili-004",
    )
    assert result.charts == ("platform-time-matrix.png",)
    assert "4 个首次收录波次" in result.markdown
    assert "首收录间隔 32.0 小时" in result.markdown
    assert "波次 1｜B站｜首次 2026-03-17 09:00" in result.markdown
    assert "[Evidence: bili-004]" in result.markdown
    assert "不代表事件起源、传播链、受众迁移或平台间因果影响" in result.markdown


def test_no_data_and_single_platform_skip_chart_and_narrator() -> None:
    cases = (
        (empty_snapshot(), SectionStatus.NO_DATA, "暂无可用于观察平台迁移"),
        (single_platform_snapshot(), SectionStatus.COMPLETE, "完整的单平台结论"),
    )
    for snapshot, expected_status, expected_text in cases:
        narrator, chart = StubNarrator(), FakeChartBuilder()
        result = SpreadPathSectionRunner(
            FakeRepository(snapshot), chart, narrator
        ).run(scope(), Language.ZH, Path("charts"))
        assert result.status is expected_status
        assert expected_text in result.markdown
        assert result.facts is not None
        assert result.evidence.records == ()
        assert chart.calls == 0 and narrator.requests == []


def test_english_narration_preserves_observable_order_limit() -> None:
    result = SpreadPathSectionRunner(
        FakeRepository(fixture_snapshot()), FakeChartBuilder(), StubNarrator()
    ).run(scope(), Language.EN, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert "## Observable platform sequence" in result.markdown
    assert "wave 1 | B站 | first 2026-03-17 09:00" in result.markdown
    assert "no repost, quote, parent, referral, or source-edge fields" in result.markdown
    assert "not event origin, a transmission chain" in result.markdown


def test_query_calculation_chart_and_narrator_failures_are_safe() -> None:
    narrator = StubNarrator()
    query = SpreadPathSectionRunner(
        FakeRepository(RuntimeError("secret")), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert query.failure.stage is FailureStage.QUERY and narrator.requests == []

    calculation = SpreadPathSectionRunner(
        FakeRepository(BrokenSnapshot()), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert calculation.failure.stage is FailureStage.CALCULATION

    chart = SpreadPathSectionRunner(
        FakeRepository(fixture_snapshot()),
        FakeChartBuilder(RuntimeError("secret")),
        narrator,
    ).run(scope(), Language.ZH, Path("charts"))
    assert chart.failure.stage is FailureStage.CHART

    failing = StubNarrator([SectionId.SPREAD_PATH])
    llm = SpreadPathSectionRunner(
        FakeRepository(fixture_snapshot()), FakeChartBuilder(), failing
    ).run(scope(), Language.ZH, Path("charts"))
    assert llm.failure.stage is FailureStage.LLM and len(failing.requests) == 1
    assert llm.charts == ("platform-time-matrix.png",)
    assert "secret" not in llm.markdown


def test_reordered_modified_or_unapproved_evidence_fails_validation() -> None:
    snapshot = fixture_snapshot()
    valid = SpreadPathSectionRunner(
        FakeRepository(snapshot), FakeChartBuilder(), StubNarrator()
    ).run(scope(), Language.ZH, Path("charts"))
    evidence_lines = [line for line in valid.markdown.splitlines() if "[Evidence:" in line]
    first = snapshot.to_evidence_set().records[0]
    invalid_markdown = (
        valid.markdown.replace("\n".join(evidence_lines), "\n".join(reversed(evidence_lines))),
        valid.markdown.replace(first.summary, "改写摘要"),
        valid.markdown.replace("波次 1｜B站", "波次 2｜B站", 1),
        valid.markdown.replace("4 篇（负面 2 篇）", "5 篇（负面 2 篇）", 1),
        valid.markdown + "\n[Evidence: invented] 未批准记录",
    )
    for markdown in invalid_markdown:
        result = SpreadPathSectionRunner(
            FakeRepository(snapshot), FakeChartBuilder(), InvalidNarrator(markdown)
        ).run(scope(), Language.ZH, Path("charts"))
        assert result.status is SectionStatus.FAILED
        assert result.failure.stage is FailureStage.LLM
        assert "invented" not in result.markdown
