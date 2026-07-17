"""Fault-isolated execution of the evidence-backed viewpoints section."""

from __future__ import annotations

import re
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
from report_engine.sections.viewpoints import ViewpointsSnapshot


EVIDENCE_CITATION = re.compile(r"\[Evidence:\s*([^\]]+)]")


class ViewpointsRepository(Protocol):
    def fetch(self, scope: AnalysisScope) -> ViewpointsSnapshot: ...


class ViewpointsSectionRunner:
    def __init__(
        self,
        repository: ViewpointsRepository,
        narrator: Narrator,
    ) -> None:
        self._repository = repository
        self._narrator = narrator

    def run(
        self,
        scope: AnalysisScope,
        language: Language,
        _chart_directory: Path,
        section_input: Mapping[str, object] | None = None,
    ) -> SectionResult:
        try:
            snapshot = self._repository.fetch(scope)
        except Exception:
            return self._failed(
                FailureStage.QUERY,
                "Viewpoints data query failed",
                language,
            )

        if not snapshot.has_data:
            heading = "Main viewpoints" if language is Language.EN else "主要观点"
            message = (
                "No relevant source records are available for this monitoring scope."
                if language is Language.EN
                else "监测范围内暂无可用于观点分析的相关内容。"
            )
            return SectionResult(
                SectionId.VIEWPOINTS,
                SectionStatus.NO_DATA,
                f"## {heading}\n\n{message}",
            )

        try:
            facts = localize_fact_set(SectionId.VIEWPOINTS, snapshot.to_fact_set(), language)
            evidence = snapshot.to_evidence_set()
        except Exception:
            return self._failed(
                FailureStage.CALCULATION,
                "Viewpoints facts or evidence construction failed",
                language,
            )

        try:
            markdown = self._narrator.narrate(
                NarrationRequest(
                    SectionId.VIEWPOINTS,
                    language,
                    facts,
                    evidence,
                    report_type=scope.report_type,
                )
            )
            self._validate_evidence_markdown(markdown, evidence)
        except Exception:
            return self._failed(
                FailureStage.LLM,
                "Viewpoints narration or evidence validation failed",
                language,
                facts=facts,
                evidence=evidence,
            )

        return SectionResult(
            section_id=SectionId.VIEWPOINTS,
            status=SectionStatus.COMPLETE,
            markdown=markdown,
            facts=facts,
            evidence=evidence,
        )

    @staticmethod
    def _validate_evidence_markdown(
        markdown: str,
        evidence: EvidenceSet,
    ) -> None:
        cited_ids = tuple(match.strip() for match in EVIDENCE_CITATION.findall(markdown))
        if cited_ids != evidence.record_ids:
            raise ValueError("Narration must cite each approved evidence ID in order")
        for record in evidence.records:
            if record.title not in markdown or record.summary not in markdown:
                raise ValueError("Narration must preserve approved evidence text")

    @staticmethod
    def _failed(
        stage: FailureStage,
        message: str,
        language: Language,
        facts: FactSet | None = None,
        evidence: EvidenceSet = EvidenceSet(),
    ) -> SectionResult:
        return SectionResult(
            section_id=SectionId.VIEWPOINTS,
            status=SectionStatus.FAILED,
            markdown=failed_section_markdown(SectionId.VIEWPOINTS, language),
            facts=facts,
            evidence=evidence,
            failure=SectionFailure(stage, message),
        )
