"""Fault-isolated execution of the cross-signal top-content section."""

from __future__ import annotations

import re
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
from report_engine.sections.top_content import TopContentSnapshot


EVIDENCE_CITATION = re.compile(r"\[Evidence:\s*([^\]]+)]")
CATEGORY_LABELS_EN = {
    "dual_signal": "dual-signal representative",
    "engagement_only": "engagement-only representative",
    "risk_only": "risk-only representative",
}
SENTIMENT_LABELS_EN = {
    "positive": "positive",
    "neutral": "neutral",
    "negative": "negative",
}
SEVERITY_LABELS_EN = {
    None: "unclassified",
    "low": "low",
    "medium": "medium",
    "high": "high",
    "critical": "critical",
}


class TopContentRepository(Protocol):
    def fetch(self, scope: AnalysisScope) -> TopContentSnapshot: ...


class TopContentChartBuilder(Protocol):
    def build(self, snapshot: TopContentSnapshot, output_directory: Path) -> Path: ...


class TopContentSectionRunner:
    def __init__(
        self,
        repository: TopContentRepository,
        chart_builder: TopContentChartBuilder,
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
    ) -> SectionResult:
        try:
            snapshot = self._repository.fetch(scope)
        except Exception:
            return self._failed(
                FailureStage.QUERY,
                "Top-content data query failed",
                language,
            )

        if not snapshot.has_articles:
            heading = "Representative content" if language is Language.EN else "代表性内容"
            message = (
                "No relevant source records are available for this monitoring scope."
                if language is Language.EN
                else "监测范围内暂无可用于代表性内容分析的相关数据。"
            )
            return SectionResult(
                SectionId.TOP_CONTENT,
                SectionStatus.NO_DATA,
                f"## {heading}\n\n{message}",
            )

        try:
            facts = snapshot.to_fact_set()
            evidence = snapshot.to_evidence_set()
        except Exception:
            return self._failed(
                FailureStage.CALCULATION,
                "Top-content facts or evidence construction failed",
                language,
            )

        if not snapshot.has_selected_records:
            return SectionResult(
                section_id=SectionId.TOP_CONTENT,
                status=SectionStatus.COMPLETE,
                markdown=self._no_signal_markdown(language, facts),
                facts=facts,
                evidence=evidence,
            )

        try:
            chart_path = self._chart_builder.build(snapshot, chart_directory)
        except Exception:
            return self._failed(
                FailureStage.CHART,
                "Top-content chart rendering failed",
                language,
                facts=facts,
                evidence=evidence,
            )

        try:
            markdown = self._narrator.narrate(
                NarrationRequest(SectionId.TOP_CONTENT, language, facts, evidence)
            )
            self._validate_markdown(markdown, facts, evidence, language)
        except Exception:
            return self._failed(
                FailureStage.LLM,
                "Top-content narration or evidence validation failed",
                language,
                facts=facts,
                evidence=evidence,
                charts=(chart_path.name,),
            )

        return SectionResult(
            section_id=SectionId.TOP_CONTENT,
            status=SectionStatus.COMPLETE,
            markdown=markdown,
            facts=facts,
            evidence=evidence,
            charts=(chart_path.name,),
        )

    @staticmethod
    def _no_signal_markdown(language: Language, facts: FactSet) -> str:
        values = facts.prompt_values()
        if language is Language.EN:
            return (
                "## Representative content\n\n"
                f"The {values['articles']} scoped records contain neither positive "
                "stored interaction counters nor a negative record meeting the "
                "explicit high-risk-signal rule. This is a complete no-qualifying-"
                "signal finding; no representative shortlist or cross-signal overlap "
                "is inferred."
            )
        return (
            "## 代表性内容\n\n"
            f"监测范围内 {values['articles']} 篇内容既没有正向存储互动计数，也没有"
            "负面记录满足明确高风险信号规则。这是完整的无符合条件信号结论；本章不"
            "生成代表性清单，也不推断跨信号重合。"
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
            "positiveEngagementArticles",
            "highRiskSignalArticles",
            "selectedCount",
            "dualSignalCount",
            "engagementOnlyCount",
            "riskOnlyCount",
            "selectedEngagement",
            "selectedEngagementShare",
        )
        if any(values[key] not in markdown for key in context_keys):
            raise ValueError("Top-content narration must preserve approved context facts")

        cited_ids = tuple(match.strip() for match in EVIDENCE_CITATION.findall(markdown))
        if cited_ids != evidence.record_ids:
            raise ValueError("Top-content narration must cite approved evidence in order")

        lines = markdown.splitlines()
        for index, record in enumerate(evidence.records, start=1):
            prefix = f"record{index}"
            citation = f"[Evidence: {record.record_id}]"
            evidence_lines = [line for line in lines if citation in line]
            if len(evidence_lines) != 1:
                raise ValueError("Each top-content citation must appear on one line")
            line = evidence_lines[0]
            if language is Language.EN:
                category = CATEGORY_LABELS_EN[facts.get(f"{prefix}Category").raw_value]
                sentiment = SENTIMENT_LABELS_EN[record.sentiment]
                engagement_rank = (
                    str(facts.get(f"{prefix}EngagementRank").raw_value)
                    if facts.get(f"{prefix}EngagementRank").raw_value is not None
                    else "unranked"
                )
                risk_rank = (
                    str(facts.get(f"{prefix}RiskRank").raw_value)
                    if facts.get(f"{prefix}RiskRank").raw_value is not None
                    else "unranked"
                )
                severity_raw = facts.get(f"{prefix}Severity").raw_value
                severity = (
                    "not applicable"
                    if record.sentiment != "negative"
                    else SEVERITY_LABELS_EN[severity_raw]
                )
                score = (
                    str(facts.get(f"{prefix}NegativeScore").raw_value)
                    if facts.get(f"{prefix}NegativeScore").raw_value is not None
                    else "unavailable"
                )
            else:
                category = values[f"{prefix}Category"]
                sentiment = values[f"{prefix}Sentiment"]
                engagement_rank = values[f"{prefix}EngagementRank"]
                risk_rank = values[f"{prefix}RiskRank"]
                severity = values[f"{prefix}Severity"]
                score = values[f"{prefix}NegativeScore"]
            required_values = (
                category,
                engagement_rank,
                risk_rank,
                values[f"{prefix}Platform"],
                sentiment,
                record.title,
                record.summary,
                values[f"{prefix}TotalEngagement"],
                severity,
                score,
            )
            if any(value not in line for value in required_values):
                raise ValueError("Top-content bullet must preserve approved evidence facts")

    @staticmethod
    def _failed(
        stage: FailureStage,
        message: str,
        language: Language,
        facts: FactSet | None = None,
        evidence: EvidenceSet = EvidenceSet(),
        charts: tuple[str, ...] = (),
    ) -> SectionResult:
        heading = "Representative content" if language is Language.EN else "代表性内容"
        body = (
            "This section could not be generated. Please try again later."
            if language is Language.EN
            else "本章节生成失败，请稍后重试。"
        )
        return SectionResult(
            section_id=SectionId.TOP_CONTENT,
            status=SectionStatus.FAILED,
            markdown=f"## {heading}\n\n{body}",
            facts=facts,
            evidence=evidence,
            charts=charts,
            failure=SectionFailure(stage, message),
        )
