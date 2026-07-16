"""Fault-isolated historical benchmark section execution."""

from pathlib import Path
from typing import Mapping, Protocol

from report_engine.config import Language, SectionId
from report_engine.domain.evidence import EvidenceSet
from report_engine.domain.facts import FactSet
from report_engine.domain.results import FailureStage, SectionFailure, SectionResult, SectionStatus
from report_engine.domain.scope import AnalysisScope
from report_engine.llm.protocol import NarrationRequest, Narrator
from report_engine.presentation import localize_fact_set
from report_engine.sections.benchmark import BenchmarkInputError, BenchmarkSnapshot, parse_comparison_tag


class BenchmarkRepository(Protocol):
    def fetch(self, scope: AnalysisScope, comparison_tag: str) -> BenchmarkSnapshot: ...


class BenchmarkChartBuilder(Protocol):
    def build(
        self,
        snapshot: BenchmarkSnapshot,
        output_directory: Path,
        language: Language = Language.ZH,
    ) -> Path: ...


class BenchmarkSectionRunner:
    def __init__(self, repository, chart_builder, narrator: Narrator) -> None:
        self.repository, self.chart_builder, self.narrator = repository, chart_builder, narrator

    def run(self, scope, language, chart_directory, section_input: Mapping[str, object] | None = None):
        try:
            value = None if section_input is None else section_input.get("comparisonTag")
            comparison_tag = parse_comparison_tag(value, scope.topic_tag)
        except BenchmarkInputError as error:
            return self._failed(FailureStage.INPUT, str(error), language)
        try:
            snapshot = self.repository.fetch(scope, comparison_tag)
        except Exception:
            return self._failed(FailureStage.QUERY, "Benchmark query failed", language)
        try:
            facts = localize_fact_set(SectionId.BENCHMARK, snapshot.to_fact_set(), language)
        except Exception:
            return self._failed(FailureStage.CALCULATION, "Benchmark calculation failed", language)
        if not snapshot.has_data:
            heading = "Historical benchmark" if language is Language.EN else "历史事件对标"
            message = ("No independent comparison cohort is available." if language is Language.EN
                       else "当前范围或独立历史对标样本暂无可比较数据。")
            return SectionResult(SectionId.BENCHMARK, SectionStatus.NO_DATA,
                                 f"## {heading}\n\n{message}", facts=facts)
        try:
            chart = self.chart_builder.build(snapshot, chart_directory, language)
        except Exception:
            return self._failed(FailureStage.CHART, "Benchmark chart rendering failed", language, facts)
        try:
            markdown = self.narrator.narrate(
                NarrationRequest(SectionId.BENCHMARK, language, facts, EvidenceSet())
            )
        except Exception:
            return self._failed(FailureStage.LLM, "Benchmark narration failed", language,
                                facts, (chart.name,))
        return SectionResult(SectionId.BENCHMARK, SectionStatus.COMPLETE, markdown,
                             facts=facts, charts=(chart.name,))

    @staticmethod
    def _failed(stage, message, language, facts: FactSet | None = None, charts=()):
        heading = "Historical benchmark" if language is Language.EN else "历史事件对标"
        body = ("This section could not be generated. Please try again later."
                if language is Language.EN else "本章节生成失败，请稍后重试。")
        return SectionResult(SectionId.BENCHMARK, SectionStatus.FAILED,
                             f"## {heading}\n\n{body}", facts=facts, charts=charts,
                             failure=SectionFailure(stage, message))
