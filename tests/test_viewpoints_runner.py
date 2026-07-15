from __future__ import annotations

from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.registry import default_registry
from report_engine.sections.viewpoints_runner import ViewpointsSectionRunner
from tests.test_config import sample_config
from tests.test_viewpoints import empty_snapshot, fixture_snapshot


class FakeRepository:
    def __init__(self, result):
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
    def __init__(self, markdown: str):
        self.markdown = markdown
        self.requests = []

    def narrate(self, request):
        self.requests.append(request)
        return self.markdown


def scope():
    return ReportPlanner(default_registry()).build(
        ReportConfig.model_validate(sample_config())
    ).scope


def test_success_calls_narrator_once_with_real_ordered_evidence() -> None:
    narrator = StubNarrator()
    result = ViewpointsSectionRunner(
        FakeRepository(fixture_snapshot()), narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert len(narrator.requests) == 1
    assert narrator.requests[0].evidence.record_ids == (
        "bili-007",
        "bili-001",
        "bili-008",
        "bili-002",
        "bili-010",
        "bili-006",
    )
    assert result.charts == ()
    assert "负面 7 篇（58.3%）" in result.markdown
    assert "不是完整主题普查" in result.markdown
    assert "### 质疑/反对" in result.markdown
    assert "### 中性/解释" in result.markdown
    assert "### 支持/缓和" in result.markdown


def test_no_data_skips_narrator() -> None:
    narrator = StubNarrator()
    result = ViewpointsSectionRunner(
        FakeRepository(empty_snapshot()), narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.NO_DATA
    assert narrator.requests == []


def test_query_calculation_and_narrator_failures_are_safe() -> None:
    narrator = StubNarrator()
    query = ViewpointsSectionRunner(
        FakeRepository(RuntimeError("secret")), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert query.failure.stage is FailureStage.QUERY and narrator.requests == []

    calculation = ViewpointsSectionRunner(
        FakeRepository(BrokenSnapshot()), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert calculation.failure.stage is FailureStage.CALCULATION
    assert narrator.requests == []

    failing = StubNarrator([SectionId.VIEWPOINTS])
    llm = ViewpointsSectionRunner(
        FakeRepository(fixture_snapshot()), failing
    ).run(scope(), Language.ZH, Path("charts"))
    assert llm.failure.stage is FailureStage.LLM and len(failing.requests) == 1


def test_unknown_reordered_or_modified_evidence_fails_validation() -> None:
    snapshot = fixture_snapshot()
    evidence = snapshot.to_evidence_set().records
    valid_lines = [
        f"- [Evidence: {record.record_id}] {record.title}：{record.summary}"
        for record in evidence
    ]

    unknown = InvalidNarrator("\n".join(valid_lines + ["[Evidence: invented]"]))
    unknown_result = ViewpointsSectionRunner(
        FakeRepository(snapshot), unknown
    ).run(scope(), Language.ZH, Path("charts"))
    assert unknown_result.failure.stage is FailureStage.LLM

    reordered = InvalidNarrator("\n".join(reversed(valid_lines)))
    reordered_result = ViewpointsSectionRunner(
        FakeRepository(snapshot), reordered
    ).run(scope(), Language.ZH, Path("charts"))
    assert reordered_result.failure.stage is FailureStage.LLM

    modified = InvalidNarrator("\n".join(valid_lines).replace(evidence[0].summary, "改写摘要"))
    modified_result = ViewpointsSectionRunner(
        FakeRepository(snapshot), modified
    ).run(scope(), Language.ZH, Path("charts"))
    assert modified_result.failure.stage is FailureStage.LLM
