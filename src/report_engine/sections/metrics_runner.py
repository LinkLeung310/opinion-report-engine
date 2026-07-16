"""Fault-isolated execution of the metrics report section."""

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
from report_engine.presentation import (
    failed_section_markdown,
    localize_fact_set,
    section_heading,
    select,
)
from report_engine.sections.metrics import MetricsSnapshot


class MetricsRepository(Protocol):
    def fetch(self, scope: AnalysisScope) -> MetricsSnapshot: ...


class MetricsChartBuilder(Protocol):
    def build(
        self,
        snapshot: MetricsSnapshot,
        output_directory: Path,
        language: Language = Language.ZH,
    ) -> Path: ...


class MetricsSectionRunner:
    def __init__(
        self,
        repository: MetricsRepository,
        chart_builder: MetricsChartBuilder,
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
            return self._failed(FailureStage.QUERY, "Metrics data query failed", language)

        if not snapshot.has_data:
            return SectionResult(
                section_id=SectionId.METRICS,
                status=SectionStatus.NO_DATA,
                markdown=(
                    f"## {section_heading(SectionId.METRICS, language)}\n\n"
                    + select(
                        language,
                        "监测范围内暂无相关数据。",
                        "No relevant data is available for this monitoring scope.",
                    )
                ),
            )

        facts = localize_fact_set(SectionId.METRICS, snapshot.to_fact_set(), language)
        try:
            chart_path = self._chart_builder.build(snapshot, chart_directory, language)
        except Exception:
            return self._failed(
                FailureStage.CHART,
                "Metrics chart rendering failed",
                language,
                facts=facts,
            )

        try:
            markdown = self._narrator.narrate(
                NarrationRequest(
                    section_id=SectionId.METRICS,
                    language=language,
                    facts=facts,
                    evidence=EvidenceSet(),
                )
            )
        except Exception:
            return self._failed(
                FailureStage.LLM,
                "Metrics narration failed",
                language,
                facts=facts,
                charts=(chart_path.name,),
            )

        return SectionResult(
            section_id=SectionId.METRICS,
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
            section_id=SectionId.METRICS,
            status=SectionStatus.FAILED,
            markdown=failed_section_markdown(SectionId.METRICS, language),
            facts=facts,
            charts=charts,
            failure=SectionFailure(stage=stage, message=message),
        )
