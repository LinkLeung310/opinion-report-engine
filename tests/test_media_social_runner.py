from __future__ import annotations

from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.media_social import MediaSocialSnapshot
from report_engine.sections.media_social_runner import MediaSocialSectionRunner
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config
from tests.test_media_social import fixture_snapshot, row


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
        return output_directory / "media-social-comparison.png"


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
        raise ValueError("secret calculation failure")


def scope():
    return ReportPlanner(default_registry()).build(
        ReportConfig.model_validate(sample_config())
    ).scope


def empty_snapshot() -> MediaSocialSnapshot:
    return MediaSocialSnapshot(
        rows=(row("media", 0, 0, 0, 0, 0), row("social", 0, 0, 0, 0, 0)),
        query_id="media-social.v1",
    )


def one_group_snapshot() -> MediaSocialSnapshot:
    return MediaSocialSnapshot(
        rows=(row("media", 0, 0, 0, 0, 0), row("social", 2, 1, 0, 1, 1)),
        query_id="media-social.v1",
    )


def test_success_charts_then_calls_narrator_once_without_evidence() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = MediaSocialSectionRunner(
        FakeRepository(fixture_snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert chart.calls == 1 and len(narrator.requests) == 1
    assert narrator.requests[0].evidence.records == ()
    assert result.charts == ("media-social-comparison.png",)
    assert "媒体内容 3 篇（25.0%）" in result.markdown
    assert "社交减媒体为 +33.3 个百分点" in result.markdown
    assert "数据库 source_type 字段" in result.markdown


def test_no_data_skips_chart_and_narrator() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = MediaSocialSectionRunner(
        FakeRepository(empty_snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.NO_DATA
    assert "暂无相关数据" in result.markdown
    assert chart.calls == 0 and narrator.requests == []


def test_one_group_remains_complete_but_disallows_comparison() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = MediaSocialSectionRunner(
        FakeRepository(one_group_snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert chart.calls == 1 and len(narrator.requests) == 1
    assert "跨组情感不可比较" in result.markdown
    assert "+0.0 个百分点" not in result.markdown


def test_query_calculation_chart_and_narrator_failures_are_safe() -> None:
    narrator = StubNarrator()
    query = MediaSocialSectionRunner(
        FakeRepository(RuntimeError("secret")), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert query.failure.stage is FailureStage.QUERY and narrator.requests == []

    calculation = MediaSocialSectionRunner(
        FakeRepository(BrokenSnapshot()), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert calculation.failure.stage is FailureStage.CALCULATION

    chart = MediaSocialSectionRunner(
        FakeRepository(fixture_snapshot()),
        FakeChartBuilder(RuntimeError("secret")),
        narrator,
    ).run(scope(), Language.ZH, Path("charts"))
    assert chart.failure.stage is FailureStage.CHART

    failing = StubNarrator([SectionId.MEDIA_SOCIAL])
    llm = MediaSocialSectionRunner(
        FakeRepository(fixture_snapshot()), FakeChartBuilder(), failing
    ).run(scope(), Language.ZH, Path("charts"))
    assert llm.failure.stage is FailureStage.LLM and len(failing.requests) == 1
    assert llm.charts == ("media-social-comparison.png",)


def test_narration_missing_approved_fact_fails_validation() -> None:
    valid = StubNarrator()
    valid_result = MediaSocialSectionRunner(
        FakeRepository(fixture_snapshot()), FakeChartBuilder(), valid
    ).run(scope(), Language.ZH, Path("charts"))
    narrator = InvalidNarrator(valid_result.markdown.replace("66.7%", "未知", 1))

    result = MediaSocialSectionRunner(
        FakeRepository(fixture_snapshot()), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert result.status is SectionStatus.FAILED
    assert result.failure.stage is FailureStage.LLM
    assert "未知" not in result.markdown
