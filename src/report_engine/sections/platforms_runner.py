"""Fault-isolated execution of the platform-performance report section."""

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
from report_engine.sections.platforms import PlatformsSnapshot


class PlatformsRepository(Protocol):
    def fetch(self, scope: AnalysisScope) -> PlatformsSnapshot: ...


class PlatformsChartBuilder(Protocol):
    def build(self, snapshot: PlatformsSnapshot, output_directory: Path) -> Path: ...


class PlatformsSectionRunner:
    def __init__(
        self,
        repository: PlatformsRepository,
        chart_builder: PlatformsChartBuilder,
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
            return self._failed(FailureStage.QUERY, "Platform data query failed")

        if not snapshot.has_data:
            heading = "Platform performance" if language is Language.EN else "平台表现"
            message = (
                "No relevant data is available for this monitoring scope."
                if language is Language.EN
                else "监测范围内暂无相关数据。"
            )
            return SectionResult(
                SectionId.PLATFORMS,
                SectionStatus.NO_DATA,
                f"## {heading}\n\n{message}",
            )

        try:
            facts = snapshot.to_fact_set()
        except Exception:
            return self._failed(FailureStage.CALCULATION, "Platform calculation failed")

        try:
            chart_path = self._chart_builder.build(snapshot, chart_directory)
        except Exception:
            return self._failed(
                FailureStage.CHART,
                "Platform chart rendering failed",
                facts=facts,
            )

        try:
            markdown = self._narrator.narrate(
                NarrationRequest(SectionId.PLATFORMS, language, facts, EvidenceSet())
            )
        except Exception:
            return self._failed(
                FailureStage.LLM,
                "Platform narration failed",
                facts=facts,
                charts=(chart_path.name,),
            )

        return SectionResult(
            section_id=SectionId.PLATFORMS,
            status=SectionStatus.COMPLETE,
            markdown=markdown,
            facts=facts,
            charts=(chart_path.name,),
        )

    @staticmethod
    def _failed(
        stage: FailureStage,
        message: str,
        facts: FactSet | None = None,
        charts: tuple[str, ...] = (),
    ) -> SectionResult:
        return SectionResult(
            section_id=SectionId.PLATFORMS,
            status=SectionStatus.FAILED,
            markdown="## 平台表现\n\n本章节生成失败，请稍后重试。",
            facts=facts,
            charts=charts,
            failure=SectionFailure(stage, message),
        )
