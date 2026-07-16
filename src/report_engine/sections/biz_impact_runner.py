"""Fault-isolated business-impact narration with separate user provenance."""

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
from report_engine.domain.user_context import UserContext
from report_engine.llm.protocol import NarrationRequest, Narrator
from report_engine.presentation import localize_fact_set
from report_engine.sections.biz_impact import (
    BizImpactInputError,
    BizImpactSnapshot,
    parse_biz_impact_notes,
)


class BizImpactRepository(Protocol):
    def fetch(self, scope: AnalysisScope) -> BizImpactSnapshot: ...


class BizImpactSectionRunner:
    def __init__(
        self,
        repository: BizImpactRepository,
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
            notes = None if section_input is None else section_input.get("notes")
            user_context = parse_biz_impact_notes(notes)
        except BizImpactInputError as error:
            return self._failed(FailureStage.INPUT, str(error), language=language)
        except Exception:
            return self._failed(
                FailureStage.CALCULATION,
                "Business-impact context construction failed",
                language=language,
            )

        try:
            snapshot = self._repository.fetch(scope)
        except Exception:
            return self._failed(
                FailureStage.QUERY,
                "Business-impact query failed",
                language=language,
            )

        try:
            facts = localize_fact_set(SectionId.BIZ_IMPACT, snapshot.to_fact_set(), language)
        except Exception:
            return self._failed(
                FailureStage.CALCULATION,
                "Business-impact calculation failed",
                language=language,
            )

        if not snapshot.has_data:
            heading = "Business impact" if language is Language.EN else "商业影响"
            message = (
                "No monitoring records are available, so the supplied business "
                "context cannot be combined with measured public-opinion signals."
                if language is Language.EN
                else "监测范围内暂无记录，无法将用户提供的业务背景与可测量舆情信号结合。"
            )
            return SectionResult(
                SectionId.BIZ_IMPACT,
                SectionStatus.NO_DATA,
                f"## {heading}\n\n{message}",
                facts=facts,
            )

        try:
            markdown = self._narrator.narrate(
                NarrationRequest(
                    SectionId.BIZ_IMPACT,
                    language,
                    facts,
                    EvidenceSet(),
                    user_context=user_context,
                    report_type=scope.report_type,
                )
            )
            self._validate_markdown(markdown, facts, user_context, language)
        except Exception:
            return self._failed(
                FailureStage.LLM,
                "Business-impact narration validation failed",
                facts=facts,
                language=language,
            )

        return SectionResult(
            section_id=SectionId.BIZ_IMPACT,
            status=SectionStatus.COMPLETE,
            markdown=markdown,
            facts=facts,
        )

    @staticmethod
    def _validate_markdown(
        markdown: str,
        facts: FactSet,
        user_context: UserContext,
        language: Language,
    ) -> None:
        values = facts.prompt_values()
        required_fact_keys = (
            "articles",
            "positiveArticles",
            "positiveShare",
            "neutralArticles",
            "neutralShare",
            "negativeArticles",
            "negativeShare",
            "highCriticalNegativeArticles",
            "highCriticalNegativeShare",
            "highCriticalAllShare",
            "platforms",
            "calendarDays",
            "activeDays",
            "activeDayCoverage",
            "peakDay",
            "peakArticles",
            "peakShare",
            "likes",
            "comments",
            "shares",
            "favorites",
            "totalStoredInteraction",
            "commentsAndShares",
            "storedInteractionPerArticle",
        )
        if language is Language.EN:
            required_text = (
                "## Business impact",
                "### Observable public-opinion signals",
                "### User-provided business context (unverified)",
                "User-provided, not verified by the report database",
                "### Business-outcome verification gap",
                "possible impact path",
                "cannot confirm",
                "No causal relationship is established",
                "does not prescribe actions",
                "captured operational snapshot",
            )
        else:
            required_text = (
                "## 商业影响",
                "### 可观测舆情信号",
                "### 用户提供的业务背景（未验证）",
                "用户提供，数据库未验证",
                "### 业务结果核验缺口",
                "可能的影响路径",
                "尚不能据此确认",
                "未建立因果关系",
                "不提供行动建议",
                "运营快照",
            )

        required = tuple(
            "unavailable"
            if language is Language.EN
            and values[key] in {"不可用", "Unavailable"}
            else values[key]
            for key in required_fact_keys
        )
        required += required_text + (user_context.source_id,)
        if any(value not in markdown for value in required):
            raise ValueError("Business-impact narration must preserve approved inputs")
        if markdown.count(user_context.markdown_safe_text) != 1:
            raise ValueError("Business-impact context must appear once without mutation")
        if (
            user_context.markdown_safe_text != user_context.text
            and user_context.text in markdown
        ):
            raise ValueError("Business-impact context must not remain active Markdown")
        if "[Evidence:" in markdown or "![" in markdown:
            raise ValueError("Business-impact narration cannot add evidence or charts")

    @staticmethod
    def _failed(
        stage: FailureStage,
        message: str,
        facts: FactSet | None = None,
        language: Language = Language.ZH,
    ) -> SectionResult:
        heading = "Business impact" if language is Language.EN else "商业影响"
        safe_message = (
            "This section could not be generated. Check its input or try again later."
            if language is Language.EN
            else "本章节生成失败，请检查输入或稍后重试。"
        )
        return SectionResult(
            section_id=SectionId.BIZ_IMPACT,
            status=SectionStatus.FAILED,
            markdown=f"## {heading}\n\n{safe_message}",
            facts=facts,
            failure=SectionFailure(stage, message),
        )
