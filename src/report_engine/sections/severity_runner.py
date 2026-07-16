"""Fault-isolated execution of the negative-severity report section."""

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
from report_engine.sections.severity import SeveritySnapshot


EVIDENCE_CITATION = re.compile(r"\[Evidence:\s*([^\]]+)]")


class SeverityRepository(Protocol):
    def fetch(self, scope: AnalysisScope) -> SeveritySnapshot: ...


class SeverityChartBuilder(Protocol):
    def build(
        self,
        snapshot: SeveritySnapshot,
        output_directory: Path,
        language: Language = Language.ZH,
    ) -> Path: ...


class SeveritySectionRunner:
    def __init__(
        self,
        repository: SeverityRepository,
        chart_builder: SeverityChartBuilder,
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
            return self._failed(FailureStage.QUERY, "Severity data query failed", language)

        if not snapshot.has_data:
            heading = "Negative severity" if language is Language.EN else "负面严重程度"
            message = (
                "No negative content was found in the monitoring scope."
                if language is Language.EN
                else "监测范围内未发现负面内容。"
            )
            return SectionResult(
                SectionId.SEVERITY,
                SectionStatus.NO_DATA,
                f"## {heading}\n\n{message}",
            )

        try:
            facts = localize_fact_set(SectionId.SEVERITY, snapshot.to_fact_set(), language)
            evidence = snapshot.to_evidence_set()
        except Exception:
            return self._failed(
                FailureStage.CALCULATION,
                "Severity facts or evidence construction failed",
                language,
            )

        try:
            chart_path = self._chart_builder.build(snapshot, chart_directory, language)
        except Exception:
            return self._failed(
                FailureStage.CHART,
                "Severity chart rendering failed",
                language,
                facts=facts,
                evidence=evidence,
            )

        try:
            markdown = self._narrator.narrate(
                NarrationRequest(SectionId.SEVERITY, language, facts, evidence)
            )
            self._validate_evidence_markdown(markdown, evidence)
        except Exception:
            return self._failed(
                FailureStage.LLM,
                "Severity narration or evidence validation failed",
                language,
                facts=facts,
                evidence=evidence,
                charts=(chart_path.name,),
            )

        return SectionResult(
            section_id=SectionId.SEVERITY,
            status=SectionStatus.COMPLETE,
            markdown=markdown,
            facts=facts,
            evidence=evidence,
            charts=(chart_path.name,),
        )

    @staticmethod
    def _validate_evidence_markdown(markdown: str, evidence: EvidenceSet) -> None:
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
        charts: tuple[str, ...] = (),
    ) -> SectionResult:
        return SectionResult(
            section_id=SectionId.SEVERITY,
            status=SectionStatus.FAILED,
            markdown=failed_section_markdown(SectionId.SEVERITY, language),
            facts=facts,
            evidence=evidence,
            charts=charts,
            failure=SectionFailure(stage, message),
        )
