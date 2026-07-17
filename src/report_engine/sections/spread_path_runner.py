"""Fault-isolated execution of observable platform migration."""

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
from report_engine.presentation import localize_fact_set, section_heading
from report_engine.sections.spread_path import SpreadPathSnapshot


EVIDENCE_CITATION = re.compile(r"\[Evidence:\s*([^\]]+)]")
SENTIMENT_LABELS_EN = {
    "positive": "positive",
    "neutral": "neutral",
    "negative": "negative",
}


class SpreadPathRepository(Protocol):
    def fetch(self, scope: AnalysisScope) -> SpreadPathSnapshot: ...


class SpreadPathChartBuilder(Protocol):
    def build(
        self,
        snapshot: SpreadPathSnapshot,
        output_directory: Path,
        language: Language = Language.ZH,
    ) -> Path: ...


class SpreadPathSectionRunner:
    def __init__(
        self,
        repository: SpreadPathRepository,
        chart_builder: SpreadPathChartBuilder,
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
                "Spread-path data query failed",
                language,
            )

        try:
            facts = localize_fact_set(SectionId.SPREAD_PATH, snapshot.to_fact_set(), language)
            evidence = snapshot.to_evidence_set()
        except Exception:
            return self._failed(
                FailureStage.CALCULATION,
                "Spread-path facts or evidence construction failed",
                language,
            )

        if not snapshot.has_data:
            message = (
                "No relevant source records are available for observable platform migration."
                if language is Language.EN
                else "监测范围内暂无可用于观察平台迁移的相关数据。"
            )
            return SectionResult(
                section_id=SectionId.SPREAD_PATH,
                status=SectionStatus.NO_DATA,
                markdown=(
                    f"## {section_heading(SectionId.SPREAD_PATH, language)}\n\n"
                    f"{message}"
                ),
                facts=facts,
            )

        if snapshot.platform_count == 1:
            return SectionResult(
                section_id=SectionId.SPREAD_PATH,
                status=SectionStatus.COMPLETE,
                markdown=self._single_platform_markdown(language, facts),
                facts=facts,
            )

        try:
            chart_path = self._chart_builder.build(snapshot, chart_directory, language)
        except Exception:
            return self._failed(
                FailureStage.CHART,
                "Spread-path chart rendering failed",
                language,
                facts=facts,
                evidence=evidence,
            )

        try:
            markdown = self._narrator.narrate(
                NarrationRequest(
                    SectionId.SPREAD_PATH,
                    language,
                    facts,
                    evidence,
                    report_type=scope.report_type,
                )
            )
            self._validate_markdown(markdown, facts, evidence, language)
        except Exception:
            return self._failed(
                FailureStage.LLM,
                "Spread-path narration or evidence validation failed",
                language,
                facts=facts,
                evidence=evidence,
                charts=(chart_path.name,),
            )

        return SectionResult(
            section_id=SectionId.SPREAD_PATH,
            status=SectionStatus.COMPLETE,
            markdown=markdown,
            facts=facts,
            evidence=evidence,
            charts=(chart_path.name,),
        )

    @staticmethod
    def _single_platform_markdown(language: Language, facts: FactSet) -> str:
        values = facts.prompt_values()
        if language is Language.EN:
            return (
                f"## {section_heading(SectionId.SPREAD_PATH, language)}\n\n"
                f"All {values['articles']} scoped records come from one platform, "
                f"{values['platform1Name']}, observed from "
                f"{values['platform1FirstObservedAt']} to "
                f"{values['platform1LastObservedAt']}. This is a complete single-"
                "platform finding; no cross-platform order, migration, or propagation "
                "edge is inferred, and no chart or model narration is generated."
            )
        return (
            f"## {section_heading(SectionId.SPREAD_PATH, language)}\n\n"
            f"监测范围内 {values['articles']} 篇内容均来自单一平台 "
            f"{values['platform1Name']}，首末收录时间为 "
            f"{values['platform1FirstObservedAt']} 至 "
            f"{values['platform1LastObservedAt']}。这是完整的单平台结论；本章不推断"
            "跨平台顺序、迁移或传播边，也不生成图表或模型叙述。"
        )

    @staticmethod
    def _validate_markdown(
        markdown: str,
        facts: FactSet,
        evidence: EvidenceSet,
        language: Language,
    ) -> None:
        values = facts.prompt_values()
        context_keys = (
            "articles",
            "platformCount",
            "displayPlatformCount",
            "omittedPlatformCount",
            "calendarDays",
            "multiPlatformDays",
            "maxDailyPlatforms",
            "maxDailyPlatformDays",
            "entryWaveCount",
            "firstObservationIntervalHours",
            "earliestPlatforms",
            "latestNewPlatforms",
        )
        if any(values[key] not in markdown for key in context_keys):
            raise ValueError("Spread-path narration must preserve approved context facts")

        cited_ids = tuple(match.strip() for match in EVIDENCE_CITATION.findall(markdown))
        if cited_ids != evidence.record_ids:
            raise ValueError("Spread-path narration must cite first records in order")
        citation_lines = [
            line for line in markdown.splitlines() if EVIDENCE_CITATION.search(line)
        ]
        if len(citation_lines) != len(evidence.records):
            raise ValueError("Each displayed platform must use exactly one evidence line")

        for index, (record, line) in enumerate(
            zip(evidence.records, citation_lines, strict=True),
            start=1,
        ):
            prefix = f"platform{index}"
            sentiment = (
                SENTIMENT_LABELS_EN[record.sentiment]
                if language is Language.EN
                else values[f"{prefix}FirstSentiment"]
            )
            phrases = (
                (
                    f"wave {values[f'{prefix}EntryWave']} | "
                    f"{values[f'{prefix}Name']} | first "
                    f"{values[f'{prefix}FirstObservedAt']} | last "
                    f"{values[f'{prefix}LastObservedAt']}",
                    f"{values[f'{prefix}Articles']} records "
                    f"({values[f'{prefix}NegativeArticles']} negative)",
                    f"{values[f'{prefix}ActiveDays']} active days",
                    f"stored interactions {values[f'{prefix}TotalEngagement']}",
                    f"[Evidence: {record.record_id}] {sentiment} | "
                    f"{record.title}: {record.summary}",
                )
                if language is Language.EN
                else (
                    f"波次 {values[f'{prefix}EntryWave']}｜"
                    f"{values[f'{prefix}Name']}｜首次 "
                    f"{values[f'{prefix}FirstObservedAt']}｜末次 "
                    f"{values[f'{prefix}LastObservedAt']}",
                    f"{values[f'{prefix}Articles']} 篇（负面 "
                    f"{values[f'{prefix}NegativeArticles']} 篇）",
                    f"活跃 {values[f'{prefix}ActiveDays']} 日",
                    f"存储互动 {values[f'{prefix}TotalEngagement']}",
                    f"[Evidence: {record.record_id}] {sentiment}｜"
                    f"{record.title}：{record.summary}",
                )
            )
            if any(phrase not in line for phrase in phrases):
                raise ValueError("Spread-path platform entry must preserve facts and evidence")

        required_limit = (
            "no repost, quote, parent, referral, or source-edge fields"
            if language is Language.EN
            else "没有转载、引用、父子、引流或来源边字段"
        )
        if required_limit not in markdown:
            raise ValueError("Spread-path narration must disclose missing relation edges")

    @staticmethod
    def _failed(
        stage: FailureStage,
        message: str,
        language: Language,
        facts: FactSet | None = None,
        evidence: EvidenceSet = EvidenceSet(),
        charts: tuple[str, ...] = (),
    ) -> SectionResult:
        body = (
            "This section could not be generated. Please try again later."
            if language is Language.EN
            else "本章节生成失败，请稍后重试。"
        )
        return SectionResult(
            section_id=SectionId.SPREAD_PATH,
            status=SectionStatus.FAILED,
            markdown=(
                f"## {section_heading(SectionId.SPREAD_PATH, language)}\n\n{body}"
            ),
            facts=facts,
            evidence=evidence,
            charts=charts,
            failure=SectionFailure(stage, message),
        )
