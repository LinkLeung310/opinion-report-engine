from __future__ import annotations

from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.negative_themes import NegativeThemesSnapshot
from report_engine.sections.negative_themes_runner import NegativeThemesSectionRunner
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config
from tests.test_negative_themes import fixture_snapshot, record


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
        return output_directory / "negative-theme-coverage.png"


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


def no_theme_snapshot() -> NegativeThemesSnapshot:
    records = (
        record("one", "单篇仅有选择权表达。", 0),
        record("two", "另一篇没有代码本指标。", 1),
    )
    return NegativeThemesSnapshot(2, 2, records, "negative-themes.v1")


def test_success_charts_then_calls_narrator_once_with_theme_order() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = NegativeThemesSectionRunner(
        FakeRepository(fixture_snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert chart.calls == 1 and len(narrator.requests) == 1
    assert result.evidence.record_ids == ("bili-005", "bili-003", "bili-007")
    assert result.charts == ("negative-theme-coverage.png",)
    assert "展示 3 个固定议题维度" in result.markdown
    assert "共记录 12 次可重叠主题归属" in result.markdown
    assert "用户自主权：覆盖负面内容 5/7 篇（71.4%）" in result.markdown
    assert "[Evidence: bili-005]" in result.markdown
    assert "不代表根因、受众分群、已验证伤害" in result.markdown


def test_no_data_and_no_qualifying_theme_skip_chart_and_narrator() -> None:
    cases = (
        (
            NegativeThemesSnapshot(0, 0, (), "negative-themes.v1"),
            SectionStatus.NO_DATA,
            "未发现负面内容",
        ),
        (no_theme_snapshot(), SectionStatus.COMPLETE, "无符合条件议题结论"),
    )
    for snapshot, expected_status, expected_text in cases:
        narrator, chart = StubNarrator(), FakeChartBuilder()
        result = NegativeThemesSectionRunner(
            FakeRepository(snapshot), chart, narrator
        ).run(scope(), Language.ZH, Path("charts"))
        assert result.status is expected_status
        assert expected_text in result.markdown
        assert result.facts is not None
        assert chart.calls == 0 and narrator.requests == []


def test_english_narration_preserves_fixed_labels_and_limits() -> None:
    result = NegativeThemesSectionRunner(
        FakeRepository(fixture_snapshot()), FakeChartBuilder(), StubNarrator()
    ).run(scope(), Language.EN, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert "## Negative issue themes" in result.markdown
    assert "User agency and control" in result.markdown
    assert "5 of 7 negative records (71.4%)" in result.markdown
    assert "versioned exact-indicator baseline" in result.markdown


def test_query_calculation_chart_and_narrator_failures_are_safe() -> None:
    narrator = StubNarrator()
    query = NegativeThemesSectionRunner(
        FakeRepository(RuntimeError("secret")), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert query.failure.stage is FailureStage.QUERY and narrator.requests == []

    calculation = NegativeThemesSectionRunner(
        FakeRepository(BrokenSnapshot()), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert calculation.failure.stage is FailureStage.CALCULATION

    chart = NegativeThemesSectionRunner(
        FakeRepository(fixture_snapshot()),
        FakeChartBuilder(RuntimeError("secret")),
        narrator,
    ).run(scope(), Language.ZH, Path("charts"))
    assert chart.failure.stage is FailureStage.CHART

    failing = StubNarrator([SectionId.NEGATIVE_THEMES])
    llm = NegativeThemesSectionRunner(
        FakeRepository(fixture_snapshot()), FakeChartBuilder(), failing
    ).run(scope(), Language.ZH, Path("charts"))
    assert llm.failure.stage is FailureStage.LLM and len(failing.requests) == 1
    assert llm.charts == ("negative-theme-coverage.png",)
    assert "secret" not in llm.markdown


def test_reordered_modified_or_unapproved_theme_evidence_fails_validation() -> None:
    snapshot = fixture_snapshot()
    valid = NegativeThemesSectionRunner(
        FakeRepository(snapshot), FakeChartBuilder(), StubNarrator()
    ).run(scope(), Language.ZH, Path("charts"))
    evidence_lines = [line for line in valid.markdown.splitlines() if "[Evidence:" in line]
    invalid_markdown = (
        valid.markdown.replace("\n".join(evidence_lines), "\n".join(reversed(evidence_lines))),
        valid.markdown.replace(snapshot.display_themes[0].representative.summary, "改写摘要"),
        valid.markdown.replace("用户自主权", "用户不满根因", 1),
        valid.markdown.replace("5/7", "6/7", 1),
        valid.markdown + "\n[Evidence: invented] 未批准记录",
    )
    for markdown in invalid_markdown:
        result = NegativeThemesSectionRunner(
            FakeRepository(snapshot), FakeChartBuilder(), InvalidNarrator(markdown)
        ).run(scope(), Language.ZH, Path("charts"))
        assert result.status is SectionStatus.FAILED
        assert result.failure.stage is FailureStage.LLM
        assert "invented" not in result.markdown


def test_shared_representative_may_be_cited_once_per_theme() -> None:
    shared = record(
        "shared",
        "用户认为推荐透明度和用户控制感不足。",
        2,
        severity="critical",
        score=5,
        engagement=9_000,
    )
    snapshot = NegativeThemesSnapshot(
        3,
        3,
        (
            record("agency", "用户担心选择权被削弱。", 0),
            record("transparent", "用户质疑推荐原因不透明。", 1),
            shared,
        ),
        "negative-themes.v1",
    )
    result = NegativeThemesSectionRunner(
        FakeRepository(snapshot), FakeChartBuilder(), StubNarrator()
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert result.evidence.record_ids == ("shared",)
    assert result.markdown.count("[Evidence: shared]") == 2
