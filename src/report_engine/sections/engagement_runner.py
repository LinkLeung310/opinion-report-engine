"""Fault-isolated execution of the interaction-composition report section."""

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
from report_engine.sections.engagement import EngagementSnapshot


EVIDENCE_CITATION = re.compile(r"\[Evidence:\s*([^\]]+)]")


class EngagementRepository(Protocol):
    def fetch(self, scope: AnalysisScope) -> EngagementSnapshot: ...


class EngagementChartBuilder(Protocol):
    def build(
        self,
        snapshot: EngagementSnapshot,
        output_directory: Path,
        language: Language = Language.ZH,
    ) -> Path: ...


class EngagementSectionRunner:
    def __init__(
        self,
        repository: EngagementRepository,
        chart_builder: EngagementChartBuilder,
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
            return self._failed(
                FailureStage.QUERY,
                "Engagement data query failed",
                language,
            )

        if not snapshot.has_articles:
            heading = "Engagement" if language is Language.EN else "互动传播"
            message = (
                "No relevant data is available for this monitoring scope."
                if language is Language.EN
                else "监测范围内暂无相关数据。"
            )
            return SectionResult(
                SectionId.ENGAGEMENT,
                SectionStatus.NO_DATA,
                f"## {heading}\n\n{message}",
            )

        try:
            facts = localize_fact_set(SectionId.ENGAGEMENT, snapshot.to_fact_set(), language)
            evidence = snapshot.to_evidence_set()
        except Exception:
            return self._failed(
                FailureStage.CALCULATION,
                "Engagement facts or evidence construction failed",
                language,
            )

        if not snapshot.has_engagement:
            return SectionResult(
                section_id=SectionId.ENGAGEMENT,
                status=SectionStatus.COMPLETE,
                markdown=self._zero_engagement_markdown(language, facts),
                facts=facts,
                evidence=evidence,
            )

        try:
            chart_path = self._chart_builder.build(snapshot, chart_directory, language)
        except Exception:
            return self._failed(
                FailureStage.CHART,
                "Engagement chart rendering failed",
                language,
                facts=facts,
                evidence=evidence,
            )

        try:
            markdown = self._narrator.narrate(
                NarrationRequest(SectionId.ENGAGEMENT, language, facts, evidence)
            )
            self._validate_evidence_markdown(markdown, evidence, facts)
        except Exception:
            return self._failed(
                FailureStage.LLM,
                "Engagement narration or evidence validation failed",
                language,
                facts=facts,
                evidence=evidence,
                charts=(chart_path.name,),
            )

        return SectionResult(
            section_id=SectionId.ENGAGEMENT,
            status=SectionStatus.COMPLETE,
            markdown=markdown,
            facts=facts,
            evidence=evidence,
            charts=(chart_path.name,),
        )

    @staticmethod
    def _zero_engagement_markdown(language: Language, facts: FactSet) -> str:
        values = facts.prompt_values()
        if language is Language.EN:
            return (
                "## Engagement\n\n"
                f"The {values['articles']} scoped records contain zero stored likes, "
                "comments, shares, or favorites. This is a complete zero-counter "
                "finding, not an engagement rate; impression and unique-user "
                "denominators are unavailable."
            )
        return (
            "## 互动传播\n\n"
            f"监测范围内 {values['articles']} 篇内容的点赞、评论、转发和收藏存储计数"
            "均为 0。这是完整的零计数结论，不是互动率；当前数据没有曝光量或独立用户"
            "分母。"
        )

    @staticmethod
    def _validate_evidence_markdown(
        markdown: str,
        evidence: EvidenceSet,
        facts: FactSet,
    ) -> None:
        cited_ids = tuple(match.strip() for match in EVIDENCE_CITATION.findall(markdown))
        if cited_ids != evidence.record_ids:
            raise ValueError("Narration must cite each engagement evidence ID in order")
        lines = markdown.splitlines()
        for index, record in enumerate(evidence.records, start=1):
            citation = f"[Evidence: {record.record_id}]"
            evidence_lines = [line for line in lines if citation in line]
            if len(evidence_lines) != 1:
                raise ValueError("Each engagement citation must appear on one bullet")
            line = evidence_lines[0]
            required_values = (
                record.title,
                facts.get(f"record{index}Total").formatted_value,
                facts.get(f"record{index}Likes").formatted_value,
                facts.get(f"record{index}Comments").formatted_value,
                facts.get(f"record{index}Shares").formatted_value,
                facts.get(f"record{index}Favorites").formatted_value,
            )
            if any(value not in line for value in required_values):
                raise ValueError("Engagement bullets must preserve approved record facts")

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
            section_id=SectionId.ENGAGEMENT,
            status=SectionStatus.FAILED,
            markdown=failed_section_markdown(SectionId.ENGAGEMENT, language),
            facts=facts,
            evidence=evidence,
            charts=charts,
            failure=SectionFailure(stage, message),
        )
