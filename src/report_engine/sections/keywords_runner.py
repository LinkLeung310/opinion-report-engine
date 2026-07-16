"""Fault-isolated execution of the recurring-keywords report section."""

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
from report_engine.sections.keywords import KeywordsSnapshot


class KeywordsRepository(Protocol):
    def fetch(self, scope: AnalysisScope) -> KeywordsSnapshot: ...


class KeywordsChartBuilder(Protocol):
    def build(
        self,
        snapshot: KeywordsSnapshot,
        output_directory: Path,
        language: Language = Language.ZH,
    ) -> Path: ...


class KeywordsSectionRunner:
    def __init__(
        self,
        repository: KeywordsRepository,
        chart_builder: KeywordsChartBuilder,
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
            return self._failed(FailureStage.QUERY, "Keywords data query failed", language)

        if not snapshot.has_articles:
            return self._no_data(language, has_articles=False)
        if not snapshot.has_data:
            return self._no_data(language, has_articles=True)

        try:
            facts = localize_fact_set(SectionId.KEYWORDS, snapshot.to_fact_set(), language)
        except Exception:
            return self._failed(
                FailureStage.CALCULATION,
                "Keywords extraction failed",
                language,
            )

        try:
            chart_path = self._chart_builder.build(snapshot, chart_directory, language)
        except Exception:
            return self._failed(
                FailureStage.CHART,
                "Keywords chart rendering failed",
                language,
                facts=facts,
            )

        try:
            markdown = self._narrator.narrate(
                NarrationRequest(
                    SectionId.KEYWORDS,
                    language,
                    facts,
                    EvidenceSet(),
                    report_type=scope.report_type,
                )
            )
        except Exception:
            return self._failed(
                FailureStage.LLM,
                "Keywords narration failed",
                language,
                facts=facts,
                charts=(chart_path.name,),
            )

        return SectionResult(
            section_id=SectionId.KEYWORDS,
            status=SectionStatus.COMPLETE,
            markdown=markdown,
            facts=facts,
            charts=(chart_path.name,),
        )

    @staticmethod
    def _no_data(language: Language, has_articles: bool) -> SectionResult:
        heading = "Keywords and topics" if language is Language.EN else "关键词与话题"
        if language is Language.EN:
            message = (
                "Relevant records exist, but no exact phrase recurs across at least "
                "two articles."
                if has_articles
                else "No relevant data is available for this monitoring scope."
            )
        else:
            message = (
                "监测范围内有相关内容，但没有原文短语在至少两篇文章中重复出现。"
                if has_articles
                else "监测范围内暂无相关数据。"
            )
        return SectionResult(
            SectionId.KEYWORDS,
            SectionStatus.NO_DATA,
            f"## {heading}\n\n{message}",
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
            section_id=SectionId.KEYWORDS,
            status=SectionStatus.FAILED,
            markdown=failed_section_markdown(SectionId.KEYWORDS, language),
            facts=facts,
            charts=charts,
            failure=SectionFailure(stage, message),
        )
