from __future__ import annotations

from datetime import date
from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.registry import default_registry
from report_engine.sections.verdict import VerdictSnapshot
from report_engine.sections.verdict_runner import VerdictSectionRunner
from tests.test_config import sample_config


def snapshot(article_count: int = 12, peak_article_count: int = 3) -> VerdictSnapshot:
    return VerdictSnapshot(
        article_count=article_count,
        negative_articles=7 if article_count else 0,
        high_risk_negative_articles=4 if article_count else 0,
        critical_negative_articles=1 if article_count else 0,
        peak_day=date(2026, 3, 20) if article_count else None,
        peak_article_count=peak_article_count if article_count else 0,
        final_day_article_count=1 if article_count else 0,
        query_id="verdict.v1",
    )


class FakeRepository:
    def __init__(self, result: VerdictSnapshot | Exception) -> None:
        self.result = result

    def fetch(self, _scope):
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def scope():
    config = ReportConfig.model_validate(sample_config())
    return ReportPlanner(default_registry()).build(config).scope


def test_success_calls_narrator_once_with_only_approved_facts() -> None:
    narrator = StubNarrator()
    runner = VerdictSectionRunner(FakeRepository(snapshot()), narrator)

    result = runner.run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert result.charts == ()
    assert len(narrator.requests) == 1
    request = narrator.requests[0]
    assert request.section_id is SectionId.VERDICT
    assert request.evidence.records == ()
    assert request.facts.get("riskLevel").raw_value == "high"
    assert "58.3%" in result.markdown
    assert "57.1%" in result.markdown
    assert "核心结论" in result.markdown


def test_no_data_is_visible_and_skips_narrator() -> None:
    narrator = StubNarrator()
    runner = VerdictSectionRunner(FakeRepository(snapshot(article_count=0)), narrator)

    result = runner.run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.NO_DATA
    assert "暂无相关数据" in result.markdown
    assert narrator.requests == []


def test_query_failure_is_safe_and_stops_before_narration() -> None:
    narrator = StubNarrator()
    runner = VerdictSectionRunner(
        FakeRepository(RuntimeError("postgresql://user:secret@internal/report")),
        narrator,
    )

    result = runner.run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.FAILED
    assert result.failure.stage is FailureStage.QUERY
    assert result.failure.message == "Verdict data query failed"
    assert "secret" not in result.markdown
    assert narrator.requests == []


def test_calculation_failure_is_safe_and_skips_narrator() -> None:
    narrator = StubNarrator()
    inconsistent = snapshot(peak_article_count=0)
    runner = VerdictSectionRunner(FakeRepository(inconsistent), narrator)

    result = runner.run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.FAILED
    assert result.failure.stage is FailureStage.CALCULATION
    assert result.failure.message == "Verdict calculation failed"
    assert narrator.requests == []


def test_narrator_failure_preserves_facts_and_does_not_retry() -> None:
    narrator = StubNarrator(fail_sections=[SectionId.VERDICT])
    runner = VerdictSectionRunner(FakeRepository(snapshot()), narrator)

    result = runner.run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.FAILED
    assert result.failure.stage is FailureStage.LLM
    assert result.failure.message == "Verdict narration failed"
    assert result.facts.get("negativeRatio").formatted_value == "58.3%"
    assert len(narrator.requests) == 1
