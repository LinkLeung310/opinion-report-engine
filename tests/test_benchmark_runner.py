from pathlib import Path

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.benchmark_runner import BenchmarkSectionRunner
from report_engine.sections.registry import default_registry
from tests.test_benchmark import cohort, fixture_snapshot
from tests.test_config import sample_config


class Repository:
    def __init__(self, result): self.result, self.calls = result, []
    def fetch(self, scope, tag):
        self.calls.append(tag)
        if isinstance(self.result, Exception): raise self.result
        return self.result


class Chart:
    def __init__(self, error=None): self.error, self.calls = error, 0
    def build(self, snapshot, directory, _language: Language = Language.ZH):
        self.calls += 1
        if self.error: raise self.error
        return directory / "historical-benchmark-comparison.png"


def scope():
    raw = sample_config(); raw["topic"]["tag"] = "bilibili-dislike"
    return ReportPlanner(default_registry()).build(ReportConfig.model_validate(raw)).scope


def test_complete_benchmark_calls_narrator_once_with_no_evidence() -> None:
    narrator, chart, repository = StubNarrator(), Chart(), Repository(fixture_snapshot())
    result = BenchmarkSectionRunner(repository, chart, narrator).run(
        scope(), Language.ZH, Path("charts"), {"comparisonTag": "legacy-feed-controls"})
    assert result.status is SectionStatus.COMPLETE
    assert repository.calls == ["legacy-feed-controls"] and chart.calls == 1
    assert len(narrator.requests) == 1 and narrator.requests[0].evidence.records == ()
    assert "本次收录样本中" in result.markdown
    assert "不能证明事件本身的客观重要性、严重性或成败" in result.markdown


def test_input_no_data_and_stage_failures_are_isolated() -> None:
    narrator, chart, repository = StubNarrator(), Chart(), Repository(fixture_snapshot())
    invalid = BenchmarkSectionRunner(repository, chart, narrator).run(
        scope(), Language.ZH, Path("charts"), {})
    assert invalid.failure.stage is FailureStage.INPUT and repository.calls == []
    empty = fixture_snapshot().__class__(cohort("current"), cohort("comparison", False), "benchmark.v1")
    no_data = BenchmarkSectionRunner(Repository(empty), chart, narrator).run(
        scope(), Language.ZH, Path("charts"), {"comparisonTag": "missing"})
    assert no_data.status is SectionStatus.NO_DATA and chart.calls == 0
    query = BenchmarkSectionRunner(Repository(RuntimeError("secret")), chart, narrator).run(
        scope(), Language.ZH, Path("charts"), {"comparisonTag": "history"})
    assert query.failure.stage is FailureStage.QUERY
    llm = BenchmarkSectionRunner(Repository(fixture_snapshot()), Chart(),
                                 StubNarrator([SectionId.BENCHMARK])).run(
        scope(), Language.ZH, Path("charts"), {"comparisonTag": "history"})
    assert llm.failure.stage is FailureStage.LLM and "secret" not in llm.markdown
