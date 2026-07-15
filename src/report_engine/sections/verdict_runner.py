"""Fault-isolated execution of the executive verdict report section."""

from __future__ import annotations

from pathlib import Path
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
from report_engine.sections.verdict import VerdictSnapshot


class VerdictRepository(Protocol):
    def fetch(self, scope: AnalysisScope) -> VerdictSnapshot: ...


class VerdictSectionRunner:
    def __init__(self, repository: VerdictRepository, narrator: Narrator) -> None:
        self._repository = repository
        self._narrator = narrator

    def run(
        self,
        scope: AnalysisScope,
        language: Language,
        _chart_directory: Path,
    ) -> SectionResult:
        try:
            snapshot = self._repository.fetch(scope)
        except Exception:
            return self._failed(FailureStage.QUERY, "Verdict data query failed")

        if not snapshot.has_data:
            message = (
                "No relevant data is available for this monitoring scope."
                if language is Language.EN
                else "监测范围内暂无相关数据。"
            )
            heading = "Executive verdict" if language is Language.EN else "核心结论"
            return SectionResult(
                section_id=SectionId.VERDICT,
                status=SectionStatus.NO_DATA,
                markdown=f"## {heading}\n\n{message}",
            )

        try:
            facts = snapshot.to_fact_set()
        except Exception:
            return self._failed(
                FailureStage.CALCULATION,
                "Verdict calculation failed",
            )

        try:
            markdown = self._narrator.narrate(
                NarrationRequest(
                    section_id=SectionId.VERDICT,
                    language=language,
                    facts=facts,
                    evidence=EvidenceSet(),
                )
            )
        except Exception:
            return self._failed(
                FailureStage.LLM,
                "Verdict narration failed",
                facts=facts,
            )

        return SectionResult(
            section_id=SectionId.VERDICT,
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
            section_id=SectionId.VERDICT,
            status=SectionStatus.FAILED,
            markdown="## 核心结论\n\n本章节生成失败，请稍后重试。",
            facts=facts,
            failure=SectionFailure(stage=stage, message=message),
        )
