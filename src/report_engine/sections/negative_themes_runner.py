"""Fault-isolated execution of the auditable negative-themes section."""

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
from report_engine.sections.negative_themes import (
    THEME_CODEBOOK,
    NegativeThemesSnapshot,
)


EVIDENCE_CITATION = re.compile(r"\[Evidence:\s*([^\]]+)]")
THEME_LABELS_EN = {
    definition.theme_id: definition.label_en for definition in THEME_CODEBOOK
}


class NegativeThemesRepository(Protocol):
    def fetch(self, scope: AnalysisScope) -> NegativeThemesSnapshot: ...


class NegativeThemesChartBuilder(Protocol):
    def build(self, snapshot: NegativeThemesSnapshot, output_directory: Path) -> Path: ...


class NegativeThemesSectionRunner:
    def __init__(
        self,
        repository: NegativeThemesRepository,
        chart_builder: NegativeThemesChartBuilder,
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
                "Negative-theme data query failed",
                language,
            )

        try:
            facts = snapshot.to_fact_set()
            evidence = snapshot.to_evidence_set()
        except Exception:
            return self._failed(
                FailureStage.CALCULATION,
                "Negative-theme classification, facts, or evidence construction failed",
                language,
            )

        if not snapshot.has_negative_articles:
            heading = "Negative issue themes" if language is Language.EN else "负面议题拆解"
            message = (
                "No negative content was found in this monitoring scope."
                if language is Language.EN
                else "监测范围内未发现负面内容。"
            )
            return SectionResult(
                section_id=SectionId.NEGATIVE_THEMES,
                status=SectionStatus.NO_DATA,
                markdown=f"## {heading}\n\n{message}",
                facts=facts,
                evidence=evidence,
            )

        if not snapshot.has_display_themes:
            return SectionResult(
                section_id=SectionId.NEGATIVE_THEMES,
                status=SectionStatus.COMPLETE,
                markdown=self._no_theme_markdown(language, facts),
                facts=facts,
                evidence=evidence,
            )

        try:
            chart_path = self._chart_builder.build(snapshot, chart_directory)
        except Exception:
            return self._failed(
                FailureStage.CHART,
                "Negative-theme chart rendering failed",
                language,
                facts=facts,
                evidence=evidence,
            )

        try:
            markdown = self._narrator.narrate(
                NarrationRequest(SectionId.NEGATIVE_THEMES, language, facts, evidence)
            )
            self._validate_markdown(markdown, snapshot, facts, evidence, language)
        except Exception:
            return self._failed(
                FailureStage.LLM,
                "Negative-theme narration or evidence validation failed",
                language,
                facts=facts,
                evidence=evidence,
                charts=(chart_path.name,),
            )

        return SectionResult(
            section_id=SectionId.NEGATIVE_THEMES,
            status=SectionStatus.COMPLETE,
            markdown=markdown,
            facts=facts,
            evidence=evidence,
            charts=(chart_path.name,),
        )

    @staticmethod
    def _no_theme_markdown(language: Language, facts: FactSet) -> str:
        values = facts.prompt_values()
        if language is Language.EN:
            return (
                "## Negative issue themes\n\n"
                f"Among {values['articles']} scoped records, "
                f"{values['negativeArticles']} are negative. The versioned exact-"
                f"indicator codebook classifies {values['classifiedNegativeArticles']} "
                f"({values['classifiedNegativeShare']}) and leaves "
                f"{values['unclassifiedNegativeArticles']} "
                f"({values['unclassifiedNegativeShare']}) unclassified, but no fixed "
                f"dimension reaches the minimum {values['minimumThemeArticles']} records. "
                "This is a complete no-qualifying-theme finding; no theme narrative or "
                "chart is inferred."
            )
        return (
            "## 负面议题拆解\n\n"
            f"监测范围内 {values['articles']} 篇内容中有 "
            f"{values['negativeArticles']} 篇负面内容。版本化精确指标码表分类 "
            f"{values['classifiedNegativeArticles']} 篇（"
            f"{values['classifiedNegativeShare']}），未分类 "
            f"{values['unclassifiedNegativeArticles']} 篇（"
            f"{values['unclassifiedNegativeShare']}），但没有固定议题维度达到至少 "
            f"{values['minimumThemeArticles']} 篇的展示门槛。这是完整的无符合条件"
            "议题结论；本章不推断主题叙述，也不生成图表。"
        )

    @staticmethod
    def _validate_markdown(
        markdown: str,
        snapshot: NegativeThemesSnapshot,
        facts: FactSet,
        evidence: EvidenceSet,
        language: Language,
    ) -> None:
        values = facts.prompt_values()
        context_keys = (
            "articles",
            "negativeArticles",
            "classifiedNegativeArticles",
            "classifiedNegativeShare",
            "unclassifiedNegativeArticles",
            "unclassifiedNegativeShare",
            "displayThemeCount",
            "totalThemeMemberships",
        )
        if any(values[key] not in markdown for key in context_keys):
            raise ValueError("Negative-theme narration must preserve context facts")

        cited_ids = tuple(match.strip() for match in EVIDENCE_CITATION.findall(markdown))
        if cited_ids != snapshot.representative_ids:
            raise ValueError("Negative-theme narration must cite representatives in theme order")
        if any(record_id not in evidence.record_ids for record_id in cited_ids):
            raise ValueError("Negative-theme narration cited evidence outside the approved set")

        citation_lines = [line for line in markdown.splitlines() if EVIDENCE_CITATION.search(line)]
        if len(citation_lines) != len(snapshot.display_themes):
            raise ValueError("Each negative theme must use exactly one evidence line")

        evidence_by_id = {record.record_id: record for record in evidence.records}
        for index, (theme, line) in enumerate(
            zip(snapshot.display_themes, citation_lines, strict=True),
            start=1,
        ):
            prefix = f"theme{index}"
            representative = evidence_by_id[theme.representative.external_id]
            label = (
                THEME_LABELS_EN[theme.theme_id]
                if language is Language.EN
                else values[f"{prefix}Label"]
            )
            structural_phrases = (
                (
                    f"{label}:",
                    f"{values[f'{prefix}Articles']} of {values['negativeArticles']} "
                    f"negative records ({values[f'{prefix}Share']})",
                )
                if language is Language.EN
                else (
                    f"{label}：",
                    f"{values[f'{prefix}Articles']}/{values['negativeArticles']} 篇（"
                    f"{values[f'{prefix}Share']}）",
                )
            )
            if any(phrase not in line for phrase in structural_phrases):
                raise ValueError("Negative-theme block must preserve its fixed label and coverage")
            required_values = (
                values[f"{prefix}ConcernArticles"],
                values[f"{prefix}DemandArticles"],
                values[f"{prefix}HighCriticalArticles"],
                values[f"{prefix}HighCriticalShare"],
                values[f"{prefix}Indicators"],
                representative.platform,
                representative.title,
                representative.summary,
                representative.record_id,
            )
            if any(value not in line for value in required_values):
                raise ValueError("Negative-theme block must preserve approved facts and evidence")

    @staticmethod
    def _failed(
        stage: FailureStage,
        message: str,
        language: Language,
        facts: FactSet | None = None,
        evidence: EvidenceSet = EvidenceSet(),
        charts: tuple[str, ...] = (),
    ) -> SectionResult:
        heading = "Negative issue themes" if language is Language.EN else "负面议题拆解"
        body = (
            "This section could not be generated. Please try again later."
            if language is Language.EN
            else "本章节生成失败，请稍后重试。"
        )
        return SectionResult(
            section_id=SectionId.NEGATIVE_THEMES,
            status=SectionStatus.FAILED,
            markdown=f"## {heading}\n\n{body}",
            facts=facts,
            evidence=evidence,
            charts=charts,
            failure=SectionFailure(stage, message),
        )
