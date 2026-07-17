"""Fault-isolated execution of the media-versus-social report section."""

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
)
from report_engine.sections.media_social import MediaSocialSnapshot


class MediaSocialRepository(Protocol):
    def fetch(self, scope: AnalysisScope) -> MediaSocialSnapshot: ...


class MediaSocialChartBuilder(Protocol):
    def build(
        self,
        snapshot: MediaSocialSnapshot,
        output_directory: Path,
        language: Language = Language.ZH,
    ) -> Path: ...


class MediaSocialSectionRunner:
    def __init__(
        self,
        repository: MediaSocialRepository,
        chart_builder: MediaSocialChartBuilder,
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
            return self._failed(FailureStage.QUERY, "Media-social query failed", language)

        if not snapshot.has_data:
            message = (
                "No relevant data is available for this monitoring scope."
                if language is Language.EN
                else "监测范围内暂无相关数据。"
            )
            return SectionResult(
                SectionId.MEDIA_SOCIAL,
                SectionStatus.NO_DATA,
                f"## {section_heading(SectionId.MEDIA_SOCIAL, language)}\n\n{message}",
            )

        try:
            facts = localize_fact_set(SectionId.MEDIA_SOCIAL, snapshot.to_fact_set(), language)
        except Exception:
            return self._failed(
                FailureStage.CALCULATION,
                "Media-social calculation failed",
                language,
            )

        try:
            chart_path = self._chart_builder.build(snapshot, chart_directory, language)
        except Exception:
            return self._failed(
                FailureStage.CHART,
                "Media-social chart rendering failed",
                language,
                facts=facts,
            )

        try:
            markdown = self._narrator.narrate(
                NarrationRequest(
                    SectionId.MEDIA_SOCIAL,
                    language,
                    facts,
                    EvidenceSet(),
                    report_type=scope.report_type,
                )
            )
            self._validate_markdown(markdown, facts, language)
        except Exception:
            return self._failed(
                FailureStage.LLM,
                "Media-social narration validation failed",
                language,
                facts=facts,
                charts=(chart_path.name,),
            )

        return SectionResult(
            section_id=SectionId.MEDIA_SOCIAL,
            status=SectionStatus.COMPLETE,
            markdown=markdown,
            facts=facts,
            charts=(chart_path.name,),
        )

    @staticmethod
    def _validate_markdown(
        markdown: str,
        facts: FactSet,
        language: Language,
    ) -> None:
        values = facts.prompt_values()
        required = (
            values["articles"],
            values["mediaArticles"],
            values["mediaArticleShare"],
            values["socialArticles"],
            values["socialArticleShare"],
            "source_type",
        )
        if values["comparisonStatus"] == "comparable":
            required += (
                values["mediaNegativeArticles"],
                values["mediaNegativeShare"],
                values["socialNegativeArticles"],
                values["socialNegativeShare"],
                values["socialMinusMediaNegativeShare"],
            )
        else:
            required += (
                "unavailable" if language is Language.EN else "不可比较",
            )
        if any(value not in markdown for value in required):
            raise ValueError("Media-social narration must preserve approved facts")

    @staticmethod
    def _failed(
        stage: FailureStage,
        message: str,
        language: Language,
        facts: FactSet | None = None,
        charts: tuple[str, ...] = (),
    ) -> SectionResult:
        return SectionResult(
            section_id=SectionId.MEDIA_SOCIAL,
            status=SectionStatus.FAILED,
            markdown=failed_section_markdown(SectionId.MEDIA_SOCIAL, language),
            facts=facts,
            charts=charts,
            failure=SectionFailure(stage, message),
        )
