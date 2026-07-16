"""Fault-isolated execution of the evidence-linked timeline section."""

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
from report_engine.sections.timeline import (
    ROLE_LABELS_EN,
    SENTIMENT_LABELS,
    TimelineSnapshot,
)


EVIDENCE_CITATION = re.compile(r"\[Evidence:\s*([^\]]+)]")


class TimelineRepository(Protocol):
    def fetch(self, scope: AnalysisScope) -> TimelineSnapshot: ...


class TimelineChartBuilder(Protocol):
    def build(self, snapshot: TimelineSnapshot, output_directory: Path) -> Path: ...


class TimelineSectionRunner:
    def __init__(
        self,
        repository: TimelineRepository,
        chart_builder: TimelineChartBuilder,
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
            return self._failed(FailureStage.QUERY, "Timeline data query failed", language)

        if not snapshot.has_data:
            heading = "Event timeline" if language is Language.EN else "事件时间线"
            message = (
                "No relevant source records are available for this monitoring scope."
                if language is Language.EN
                else "监测范围内暂无可用于时间线分析的相关内容。"
            )
            return SectionResult(
                SectionId.TIMELINE,
                SectionStatus.NO_DATA,
                f"## {heading}\n\n{message}",
            )

        try:
            facts = localize_fact_set(SectionId.TIMELINE, snapshot.to_fact_set(), language)
            evidence = snapshot.to_evidence_set()
        except Exception:
            return self._failed(
                FailureStage.CALCULATION,
                "Timeline facts or evidence construction failed",
                language,
            )

        try:
            chart_path = self._chart_builder.build(snapshot, chart_directory)
        except Exception:
            return self._failed(
                FailureStage.CHART,
                "Timeline chart rendering failed",
                language,
                facts=facts,
                evidence=evidence,
            )

        try:
            markdown = self._narrator.narrate(
                NarrationRequest(SectionId.TIMELINE, language, facts, evidence)
            )
            self._validate_markdown(markdown, facts, evidence, language)
        except Exception:
            return self._failed(
                FailureStage.LLM,
                "Timeline narration or evidence validation failed",
                language,
                facts=facts,
                evidence=evidence,
                charts=(chart_path.name,),
            )

        return SectionResult(
            section_id=SectionId.TIMELINE,
            status=SectionStatus.COMPLETE,
            markdown=markdown,
            facts=facts,
            evidence=evidence,
            charts=(chart_path.name,),
        )

    @staticmethod
    def _validate_markdown(
        markdown: str,
        facts: FactSet,
        evidence: EvidenceSet,
        language: Language,
    ) -> None:
        values = facts.prompt_values()
        required_context = (
            values["articles"],
            values["peakDay"],
            values["peakArticles"],
            values["observedCalendarDays"],
            values["milestoneCount"],
            "official-response",
        )
        if any(value not in markdown for value in required_context):
            raise ValueError("Timeline narration must preserve approved context facts")

        cited_ids = tuple(match.strip() for match in EVIDENCE_CITATION.findall(markdown))
        if cited_ids != evidence.record_ids:
            raise ValueError("Timeline narration must cite approved evidence in order")
        lines = markdown.splitlines()
        sentiment_labels_en = {
            "positive": "positive",
            "neutral": "neutral",
            "negative": "negative",
        }
        for index, record in enumerate(evidence.records, start=1):
            prefix = f"milestone{index}"
            citation = f"[Evidence: {record.record_id}]"
            evidence_lines = [line for line in lines if citation in line]
            if len(evidence_lines) != 1:
                raise ValueError("Each timeline citation must appear on one line")
            line = evidence_lines[0]
            role_keys = values[f"{prefix}RoleKeys"].split(",")
            role_display = (
                ", ".join(ROLE_LABELS_EN[role] for role in role_keys)
                if language is Language.EN
                else values[f"{prefix}Roles"]
            )
            sentiment = (
                sentiment_labels_en[record.sentiment]
                if language is Language.EN
                else SENTIMENT_LABELS[record.sentiment]
            )
            required_values = (
                role_display,
                values[f"{prefix}PublishedAt"],
                values[f"{prefix}Platform"],
                sentiment,
                record.title,
                record.summary,
            )
            peak_key = f"{prefix}PeakEngagement"
            if peak_key in values:
                required_values += (values[peak_key],)
            if any(value not in line for value in required_values):
                raise ValueError("Timeline milestone must preserve approved evidence facts")

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
            section_id=SectionId.TIMELINE,
            status=SectionStatus.FAILED,
            markdown=failed_section_markdown(SectionId.TIMELINE, language),
            facts=facts,
            evidence=evidence,
            charts=charts,
            failure=SectionFailure(stage, message),
        )
