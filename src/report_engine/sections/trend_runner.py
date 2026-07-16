"""Fault-isolated execution of the heat-trend report section."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Protocol

from report_engine.config import Language, SectionId
from report_engine.domain.evidence import EvidenceSet
from report_engine.domain.facts import FactSet
from report_engine.domain.results import (
    FailureStage,
    SectionFailure,
    SectionResult,
    SectionStatus,
)
from report_engine.domain.scope import AnalysisScope
from report_engine.llm.protocol import NarrationRequest, Narrator
from report_engine.presentation import failed_section_markdown, localize_fact_set
from report_engine.sections.trend import TrendSnapshot


class TrendRepository(Protocol):
    def fetch(self, scope: AnalysisScope) -> TrendSnapshot: ...


class TrendChartBuilder(Protocol):
    def build(self, snapshot: TrendSnapshot, output_directory: Path) -> Path: ...


class TrendSectionRunner:
    def __init__(
        self,
        repository: TrendRepository,
        chart_builder: TrendChartBuilder,
        narrator: Narrator,
    ) -> None:
        self._repository = repository
        self._chart_builder = chart_builder
        self._narrator = narrator

    def run(
        self,
        scope: AnalysisScope,
        language: Language,
        chart_directory: Path,
        section_input: Mapping[str, object] | None = None,
    ) -> SectionResult:
        try:
            snapshot = self._repository.fetch(scope)
        except Exception:
            return self._failed(FailureStage.QUERY, "Trend data query failed", language)

        if not snapshot.has_data:
            heading = "Heat trend" if language is Language.EN else "热度趋势"
            message = (
                "No relevant data is available for this monitoring scope."
                if language is Language.EN
                else "监测范围内暂无相关数据。"
            )
            return SectionResult(
                SectionId.TREND,
                SectionStatus.NO_DATA,
                f"## {heading}\n\n{message}",
            )

        try:
            facts = localize_fact_set(SectionId.TREND, snapshot.to_fact_set(), language)
        except Exception:
            return self._failed(
                FailureStage.CALCULATION,
                "Trend calculation failed",
                language,
            )

        try:
            chart_path = self._chart_builder.build(snapshot, chart_directory)
        except Exception:
            return self._failed(
                FailureStage.CHART,
                "Trend chart rendering failed",
                language,
                facts=facts,
            )

        try:
            markdown = self._narrator.narrate(
                NarrationRequest(SectionId.TREND, language, facts, EvidenceSet())
            )
        except Exception:
            return self._failed(
                FailureStage.LLM,
                "Trend narration failed",
                language,
                facts=facts,
                charts=(chart_path.name,),
            )

        return SectionResult(
            section_id=SectionId.TREND,
            status=SectionStatus.COMPLETE,
            markdown=markdown,
            facts=facts,
            charts=(chart_path.name,),
        )

    @staticmethod
    def _failed(
        stage: FailureStage,
        message: str,
        language: Language,
        facts: FactSet | None = None,
        charts: tuple[str, ...] = (),
    ) -> SectionResult:
        return SectionResult(
            section_id=SectionId.TREND,
            status=SectionStatus.FAILED,
            markdown=failed_section_markdown(SectionId.TREND, language),
            facts=facts,
            charts=charts,
            failure=SectionFailure(stage, message),
        )
