"""Fault-isolated execution of the metrics report section."""

from __future__ import annotations

from typing import Protocol

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
from report_engine.sections.metrics import MetricsSnapshot


class MetricsRepository(Protocol):
    def fetch(self, scope: AnalysisScope) -> MetricsSnapshot: ...


class MetricsSectionRunner:
    def __init__(self, repository: MetricsRepository, narrator: Narrator) -> None:
        self._repository = repository
        self._narrator = narrator

    def run(self, scope: AnalysisScope, language: Language) -> SectionResult:
        try:
            snapshot = self._repository.fetch(scope)
        except Exception:
            return self._failed(FailureStage.QUERY, "Metrics data query failed")

        if not snapshot.has_data:
            return SectionResult(
                section_id=SectionId.METRICS,
                status=SectionStatus.NO_DATA,
                markdown="## 全网数据概览\n\n监测范围内暂无相关数据。",
            )

        facts = snapshot.to_fact_set()
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
            return self._failed(FailureStage.LLM, "Metrics narration failed", facts=facts)

        return SectionResult(
            section_id=SectionId.METRICS,
            status=SectionStatus.COMPLETE,
            markdown=markdown,
            facts=facts,
        )

    @staticmethod
    def _failed(
        stage: FailureStage,
        message: str,
        facts: FactSet | None = None,
    ) -> SectionResult:
        return SectionResult(
            section_id=SectionId.METRICS,
            status=SectionStatus.FAILED,
            markdown="## 全网数据概览\n\n本章节生成失败，请稍后重试。",
            facts=facts,
            failure=SectionFailure(stage=stage, message=message),
        )
