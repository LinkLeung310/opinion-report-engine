"""Fault-isolated execution of the balanced response comparison section."""

from __future__ import annotations

from datetime import date
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
from report_engine.sections.response import (
    ResponseInputError,
    ResponseSnapshot,
    ResponseWindow,
    parse_response_date,
)


class ResponseRepository(Protocol):
    def fetch(self, scope: AnalysisScope, response_date: date) -> ResponseSnapshot: ...


class ResponseChartBuilder(Protocol):
    def build(self, snapshot: ResponseSnapshot, output_directory: Path) -> Path: ...


class ResponseSectionRunner:
    def __init__(
        self,
        repository: ResponseRepository,
        chart_builder: ResponseChartBuilder,
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
            value = None if section_input is None else section_input.get("responseDate")
            response_date = parse_response_date(value)
            ResponseWindow.build(scope.from_date, scope.to_date, response_date)
        except ResponseInputError as error:
            return self._failed(FailureStage.INPUT, str(error), language=language)

        try:
            snapshot = self._repository.fetch(scope, response_date)
        except Exception:
            return self._failed(
                FailureStage.QUERY,
                "Response comparison query failed",
                language=language,
            )

        try:
            facts = snapshot.to_fact_set()
        except Exception:
            return self._failed(
                FailureStage.CALCULATION,
                "Response comparison calculation failed",
                language=language,
            )

        if not snapshot.has_comparison_data:
            heading = "Response comparison" if language is Language.EN else "回应前后对比"
            if snapshot.has_scoped_data:
                message = (
                    "Scoped records exist, but none fall inside the matched pre/post "
                    "windows after excluding the response date."
                    if language is Language.EN
                    else "监测范围内存在相关内容，但排除回应日后，等长的回应前后窗口内暂无记录。"
                )
            else:
                message = (
                    "No relevant data is available for this monitoring scope."
                    if language is Language.EN
                    else "监测范围内暂无相关数据。"
                )
            return SectionResult(
                SectionId.RESPONSE,
                SectionStatus.NO_DATA,
                f"## {heading}\n\n{message}",
                facts=facts,
            )

        try:
            chart_path = self._chart_builder.build(snapshot, chart_directory)
        except Exception:
            return self._failed(
                FailureStage.CHART,
                "Response comparison chart rendering failed",
                facts=facts,
                language=language,
            )

        try:
            markdown = self._narrator.narrate(
                NarrationRequest(SectionId.RESPONSE, language, facts, EvidenceSet())
            )
        except Exception:
            return self._failed(
                FailureStage.LLM,
                "Response comparison narration failed",
                facts=facts,
                charts=(chart_path.name,),
                language=language,
            )

        return SectionResult(
            section_id=SectionId.RESPONSE,
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
        language: Language = Language.ZH,
    ) -> SectionResult:
        heading = "Response comparison" if language is Language.EN else "回应前后对比"
        safe_message = (
            "This section could not be generated. Please try again later."
            if language is Language.EN
            else "本章节生成失败，请稍后重试。"
        )
        return SectionResult(
            section_id=SectionId.RESPONSE,
            status=SectionStatus.FAILED,
            markdown=f"## {heading}\n\n{safe_message}",
            facts=facts,
            charts=charts,
            failure=SectionFailure(stage, message),
        )
