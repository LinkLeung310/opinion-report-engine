from __future__ import annotations

from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.engagement import EngagementSnapshot
from report_engine.sections.engagement_runner import EngagementSectionRunner
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config
from tests.test_engagement import fixture_snapshot


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
        return output_directory / "engagement-composition.png"


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
        raise ValueError("secret calculation failure")

    def to_evidence_set(self):
        raise AssertionError("must stop after fact failure")


def scope():
    return ReportPlanner(default_registry()).build(
        ReportConfig.model_validate(sample_config())
    ).scope


def zero_snapshot(article_count: int) -> EngagementSnapshot:
    return EngagementSnapshot(
        article_count=article_count,
        positive_total_engagement_articles=0,
        zero_engagement_articles=article_count,
        likes=0,
        comments=0,
        shares=0,
        favorites=0,
        leading_record_count=0,
        records=(),
        query_id="engagement.v1",
    )


def test_success_charts_then_calls_narrator_once_with_ranked_evidence() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = EngagementSectionRunner(
        FakeRepository(fixture_snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert chart.calls == 1 and len(narrator.requests) == 1
    assert narrator.requests[0].evidence.record_ids == (
        "bili-007",
        "bili-005",
        "bili-010",
    )
    assert result.evidence.record_ids == narrator.requests[0].evidence.record_ids
    assert result.charts == ("engagement-composition.png",)
    assert "共记录原始互动 26,170" in result.markdown
    assert "评论与转发合计 9,325（35.6%）" in result.markdown
    assert "[Evidence: bili-007]" in result.markdown
    assert "不代表互动率、真实触达或支持度" in result.markdown


def test_no_articles_is_no_data_and_zero_counters_is_complete_without_calls() -> None:
    for article_count, expected_status, expected_text in (
        (0, SectionStatus.NO_DATA, "暂无相关数据"),
        (2, SectionStatus.COMPLETE, "完整的零计数结论"),
    ):
        narrator, chart = StubNarrator(), FakeChartBuilder()
        result = EngagementSectionRunner(
            FakeRepository(zero_snapshot(article_count)), chart, narrator
        ).run(scope(), Language.ZH, Path("charts"))
        assert result.status is expected_status
        assert expected_text in result.markdown
        assert chart.calls == 0 and narrator.requests == []


def test_query_calculation_chart_and_narrator_failures_are_safe() -> None:
    narrator = StubNarrator()
    query = EngagementSectionRunner(
        FakeRepository(RuntimeError("secret")), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert query.failure.stage is FailureStage.QUERY and narrator.requests == []

    calculation = EngagementSectionRunner(
        FakeRepository(BrokenSnapshot()), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert calculation.failure.stage is FailureStage.CALCULATION

    chart = EngagementSectionRunner(
        FakeRepository(fixture_snapshot()),
        FakeChartBuilder(RuntimeError("secret")),
        narrator,
    ).run(scope(), Language.ZH, Path("charts"))
    assert chart.failure.stage is FailureStage.CHART

    failing = StubNarrator([SectionId.ENGAGEMENT])
    llm = EngagementSectionRunner(
        FakeRepository(fixture_snapshot()), FakeChartBuilder(), failing
    ).run(scope(), Language.ZH, Path("charts"))
    assert llm.failure.stage is FailureStage.LLM and len(failing.requests) == 1
    assert llm.charts == ("engagement-composition.png",)


def test_unknown_reordered_or_modified_evidence_fails_validation() -> None:
    snapshot = fixture_snapshot()
    records = snapshot.to_evidence_set().records
    stub = StubNarrator()
    valid_result = EngagementSectionRunner(
        FakeRepository(snapshot), FakeChartBuilder(), stub
    ).run(scope(), Language.ZH, Path("charts"))
    assert valid_result.status is SectionStatus.COMPLETE
    valid_lines = [
        line for line in valid_result.markdown.splitlines() if "[Evidence:" in line
    ]
    invalid_markdown = (
        "\n".join(reversed(valid_lines)),
        "\n".join(valid_lines).replace(records[0].title, "修改后的标题"),
        "\n".join(valid_lines).replace("10,020", "10,021", 1),
        "\n".join(valid_lines + ["[Evidence: invented] 未批准内容"]),
    )
    for markdown in invalid_markdown:
        narrator = InvalidNarrator(markdown)
        result = EngagementSectionRunner(
            FakeRepository(snapshot), FakeChartBuilder(), narrator
        ).run(scope(), Language.ZH, Path("charts"))
        assert result.status is SectionStatus.FAILED
        assert result.failure.stage is FailureStage.LLM
        assert "invented" not in result.markdown
