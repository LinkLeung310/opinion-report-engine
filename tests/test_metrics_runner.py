from __future__ import annotations

from datetime import date

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.metrics import MetricsSnapshot
from report_engine.sections.metrics_runner import MetricsSectionRunner
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


def snapshot(article_count: int = 12) -> MetricsSnapshot:
    return MetricsSnapshot(
        article_count=article_count,
        positive_articles=2 if article_count else 0,
        neutral_articles=3 if article_count else 0,
        negative_articles=7 if article_count else 0,
        platform_count=4 if article_count else 0,
        likes=15_460 if article_count else 0,
        comments=4_705 if article_count else 0,
        shares=4_620 if article_count else 0,
        favorites=1_385 if article_count else 0,
        peak_day=date(2026, 3, 20) if article_count else None,
        peak_article_count=3 if article_count else 0,
        query_id="metrics.v1",
    )


class FakeRepository:
    def __init__(self, result: MetricsSnapshot | Exception) -> None:
        self.result = result

    def fetch(self, _scope):
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def scope():
    config = ReportConfig.model_validate(sample_config())
    return ReportPlanner(default_registry()).build(config).scope


def test_success_calls_the_narrator_once_with_approved_facts() -> None:
    narrator = StubNarrator()
    runner = MetricsSectionRunner(FakeRepository(snapshot()), narrator)

    result = runner.run(scope(), Language.ZH)

    assert result.status is SectionStatus.COMPLETE
    assert len(narrator.requests) == 1
    assert narrator.requests[0].facts.get("negativeRatio").formatted_value == "58.3%"
    assert "58.3%" in result.markdown


def test_no_data_is_visible_and_does_not_call_the_narrator() -> None:
    narrator = StubNarrator()
    runner = MetricsSectionRunner(FakeRepository(snapshot(article_count=0)), narrator)

    result = runner.run(scope(), Language.ZH)

    assert result.status is SectionStatus.NO_DATA
    assert "暂无相关数据" in result.markdown
    assert narrator.requests == []


def test_query_failure_is_safe_and_does_not_stop_the_report_protocol() -> None:
    narrator = StubNarrator()
    repository_error = RuntimeError("postgresql://user:secret@internal.example/report")
    runner = MetricsSectionRunner(FakeRepository(repository_error), narrator)

    result = runner.run(scope(), Language.ZH)

    assert result.status is SectionStatus.FAILED
    assert result.failure.stage is FailureStage.QUERY
    assert result.failure.message == "Metrics data query failed"
    assert "secret" not in result.markdown
    assert narrator.requests == []


def test_narrator_failure_is_safe_and_never_retries_at_section_level() -> None:
    narrator = StubNarrator(fail_sections=[SectionId.METRICS])
    runner = MetricsSectionRunner(FakeRepository(snapshot()), narrator)

    result = runner.run(scope(), Language.ZH)

    assert result.status is SectionStatus.FAILED
    assert result.failure.stage is FailureStage.LLM
    assert result.failure.message == "Metrics narration failed"
    assert "secret" not in result.markdown
    assert len(narrator.requests) == 1
