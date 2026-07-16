from __future__ import annotations

from datetime import date
from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.biz_impact import BizImpactSnapshot
from report_engine.sections.biz_impact_runner import BizImpactSectionRunner
from report_engine.sections.registry import default_registry
from tests.test_biz_impact import empty_snapshot, fixture_snapshot
from tests.test_config import sample_config


class Repository:
    def __init__(self, result) -> None:
        self.result = result
        self.calls = 0

    def fetch(self, scope):
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class BrokenSnapshot:
    has_data = True

    def to_fact_set(self):
        raise ValueError("synthetic calculation details")


class MutatingNarrator:
    def narrate(self, request):
        markdown = StubNarrator().narrate(request)
        return markdown.replace(request.user_context.markdown_safe_text, "改写后的背景")


def scope():
    raw = sample_config()
    raw["topic"]["tag"] = "bilibili-dislike"
    config = ReportConfig.model_validate(raw)
    return ReportPlanner(default_registry()).build(config).scope


def test_complete_business_impact_keeps_context_separate_and_calls_once() -> None:
    repository = Repository(fixture_snapshot())
    narrator = StubNarrator()
    runner = BizImpactSectionRunner(repository, narrator)

    result = runner.run(
        scope(),
        Language.ZH,
        Path("charts"),
        {"notes": " 销量下降 20%\n需要结合内部转化数据核验 "},
    )

    assert result.status is SectionStatus.COMPLETE
    assert result.charts == ()
    assert repository.calls == 1
    assert len(narrator.requests) == 1
    request = narrator.requests[0]
    assert request.section_id is SectionId.BIZ_IMPACT
    assert request.evidence.records == ()
    assert request.user_context.text == "销量下降 20% 需要结合内部转化数据核验"
    assert "### 可观测舆情信号" in result.markdown
    assert "### 用户提供的业务背景（未验证）" in result.markdown
    assert "### 业务结果核验缺口" in result.markdown
    assert "存储互动计数合计 26,170" in result.markdown
    assert "未建立因果关系" in result.markdown


def test_business_impact_has_equivalent_english_provenance() -> None:
    narrator = StubNarrator()
    result = BizImpactSectionRunner(Repository(fixture_snapshot()), narrator).run(
        scope(),
        Language.EN,
        Path("charts"),
        {"notes": "Conversion may have declined; verify internally."},
    )

    assert result.status is SectionStatus.COMPLETE
    assert "### Observable public-opinion signals" in result.markdown
    assert "### User-provided business context (unverified)" in result.markdown
    assert "User-provided, not verified by the report database" in result.markdown
    assert "### Business-outcome verification gap" in result.markdown
    assert "No causal relationship is established" in result.markdown


def test_invalid_input_fails_before_query() -> None:
    repository = Repository(fixture_snapshot())
    result = BizImpactSectionRunner(repository, StubNarrator()).run(
        scope(), Language.ZH, Path("charts"), {}
    )

    assert result.status is SectionStatus.FAILED
    assert result.failure.stage is FailureStage.INPUT
    assert "notes" in result.failure.message
    assert repository.calls == 0


def test_no_data_retains_facts_without_narration() -> None:
    narrator = StubNarrator()
    result = BizImpactSectionRunner(Repository(empty_snapshot()), narrator).run(
        scope(), Language.ZH, Path("charts"), {"notes": "内部销量待核验"}
    )

    assert result.status is SectionStatus.NO_DATA
    assert result.facts.get("articles").raw_value == 0
    assert "无法将用户提供的业务背景" in result.markdown
    assert narrator.requests == []


def test_non_empty_zero_negative_scope_is_complete() -> None:
    values = fixture_snapshot().__dict__
    snapshot = BizImpactSnapshot(
        **{
            **values,
            "article_count": 2,
            "positive_articles": 2,
            "neutral_articles": 0,
            "negative_articles": 0,
            "platform_count": 1,
            "active_days": 1,
            "peak_day": date(2026, 3, 17),
            "peak_article_count": 2,
            "high_critical_negative_articles": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "favorites": 0,
        }
    )

    result = BizImpactSectionRunner(Repository(snapshot), StubNarrator()).run(
        scope(), Language.ZH, Path("charts"), {"notes": "内部指标待核验"}
    )

    assert result.status is SectionStatus.COMPLETE
    assert "未显示可测量的负面舆情压力" in result.markdown
    assert "占负面记录的 不可用" in result.markdown


def test_query_calculation_and_narration_failures_are_isolated() -> None:
    notes = {"notes": "内部指标待核验"}
    query = BizImpactSectionRunner(
        Repository(RuntimeError("secret query")), StubNarrator()
    ).run(scope(), Language.ZH, Path("charts"), notes)
    calculation = BizImpactSectionRunner(
        Repository(BrokenSnapshot()), StubNarrator()
    ).run(scope(), Language.ZH, Path("charts"), notes)
    llm = BizImpactSectionRunner(
        Repository(fixture_snapshot()),
        StubNarrator([SectionId.BIZ_IMPACT]),
    ).run(scope(), Language.ZH, Path("charts"), notes)

    assert query.failure.stage is FailureStage.QUERY
    assert calculation.failure.stage is FailureStage.CALCULATION
    assert llm.failure.stage is FailureStage.LLM
    assert "secret" not in query.markdown + calculation.markdown + llm.markdown


def test_mutated_context_is_rejected_as_narration_failure() -> None:
    result = BizImpactSectionRunner(
        Repository(fixture_snapshot()), MutatingNarrator()
    ).run(
        scope(),
        Language.ZH,
        Path("charts"),
        {"notes": "原始业务背景"},
    )

    assert result.status is SectionStatus.FAILED
    assert result.failure.stage is FailureStage.LLM
    assert "改写后的背景" not in result.markdown


def test_context_markup_is_encoded_in_markdown() -> None:
    narrator = StubNarrator()
    result = BizImpactSectionRunner(Repository(fixture_snapshot()), narrator).run(
        scope(),
        Language.ZH,
        Path("charts"),
        {"notes": "<script>![remote](https://example.invalid/image.png)"},
    )

    assert result.status is SectionStatus.COMPLETE
    assert "<script>" not in result.markdown
    assert "![remote]" not in result.markdown
    assert "&lt;script&gt;" in result.markdown
    assert "&#33;&#91;remote&#93;" in result.markdown
