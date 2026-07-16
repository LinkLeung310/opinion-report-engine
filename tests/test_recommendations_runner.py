from __future__ import annotations

from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.recommendations import RecommendationsSnapshot
from report_engine.sections.recommendations_runner import RecommendationsSectionRunner
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config
from tests.test_recommendations import fixture_snapshot


class Repository:
    def __init__(self, result) -> None:
        self.result = result

    def fetch(self, _scope):
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class BrokenSnapshot:
    has_data = True

    def to_fact_set(self):
        raise ValueError("synthetic calculation failure")


class InvalidNarrator:
    def __init__(self, markdown: str) -> None:
        self.markdown = markdown

    def narrate(self, _request):
        return self.markdown


def scope():
    raw = sample_config()
    raw["topic"]["tag"] = "bilibili-dislike"
    return ReportPlanner(default_registry()).build(
        ReportConfig.model_validate(raw)
    ).scope


def test_complete_plan_calls_stub_once_and_preserves_shared_evidence() -> None:
    narrator = StubNarrator()
    result = RecommendationsSectionRunner(
        Repository(fixture_snapshot()), narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert result.charts == ()
    assert len(narrator.requests) == 1
    assert narrator.requests[0].section_id is SectionId.RECOMMENDATIONS
    assert result.evidence.record_ids == ("bili-007", "bili-005", "bili-003")
    assert result.markdown.count("[Evidence: bili-007]") == 2
    assert "### 1. 核验高风险记录" in result.markdown
    assert "### 4. 建立反馈闭环" in result.markdown
    assert "建议角色而非自动指派" in result.markdown
    assert "不会自动发送消息、修改产品或创建工单" in result.markdown


def test_equivalent_english_plan_preserves_human_review_boundary() -> None:
    result = RecommendationsSectionRunner(
        Repository(fixture_snapshot()), StubNarrator()
    ).run(scope(), Language.EN, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert "## Recommended actions" in result.markdown
    assert "### 2. Validate the user-control path" in result.markdown
    assert "within 24 hours" in result.markdown
    assert "Suggested role owners are not automatic assignments" in result.markdown
    assert "does not send messages, change the product, or open tickets" in result.markdown


def test_zero_articles_and_zero_negative_skip_narrator() -> None:
    cases = (
        (
            RecommendationsSnapshot(0, 0, (), "recommendations.v1"),
            SectionStatus.NO_DATA,
            "不提出缺少证据支撑的行动",
        ),
        (
            RecommendationsSnapshot(3, 0, (), "recommendations.v1"),
            SectionStatus.COMPLETE,
            "维持常规监测",
        ),
    )
    for snapshot, status, text in cases:
        narrator = StubNarrator()
        result = RecommendationsSectionRunner(Repository(snapshot), narrator).run(
            scope(), Language.ZH, Path("charts")
        )
        assert result.status is status
        assert text in result.markdown
        assert narrator.requests == []


def test_query_calculation_and_llm_failures_are_safe() -> None:
    query = RecommendationsSectionRunner(
        Repository(RuntimeError("secret query")), StubNarrator()
    ).run(scope(), Language.ZH, Path("charts"))
    calculation = RecommendationsSectionRunner(
        Repository(BrokenSnapshot()), StubNarrator()
    ).run(scope(), Language.ZH, Path("charts"))
    llm = RecommendationsSectionRunner(
        Repository(fixture_snapshot()),
        StubNarrator([SectionId.RECOMMENDATIONS]),
    ).run(scope(), Language.ZH, Path("charts"))

    assert query.failure.stage is FailureStage.QUERY
    assert calculation.failure.stage is FailureStage.CALCULATION
    assert llm.failure.stage is FailureStage.LLM
    assert "secret" not in query.markdown + calculation.markdown + llm.markdown


def test_reordered_or_mutated_evidence_is_rejected() -> None:
    snapshot = fixture_snapshot()
    valid = RecommendationsSectionRunner(
        Repository(snapshot), StubNarrator()
    ).run(scope(), Language.ZH, Path("charts"))
    first = "[Evidence: bili-007]"
    second = "[Evidence: bili-005]"
    invalid = (
        valid.markdown.replace(first, "[Evidence: swap]", 1)
        .replace(second, first, 1)
        .replace("[Evidence: swap]", second, 1)
    )
    result = RecommendationsSectionRunner(
        Repository(snapshot), InvalidNarrator(invalid)
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.FAILED
    assert result.failure.stage is FailureStage.LLM
    assert "swap" not in result.markdown
