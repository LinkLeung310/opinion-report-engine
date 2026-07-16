"""Fault-isolated execution of evidence-linked recommended actions."""

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
from report_engine.presentation import localize_fact_set
from report_engine.sections.recommendations import RecommendationsSnapshot


EVIDENCE_CITATION = re.compile(r"\[Evidence:\s*([^\]]+)]")


class RecommendationsRepository(Protocol):
    def fetch(self, scope: AnalysisScope) -> RecommendationsSnapshot: ...


class RecommendationsSectionRunner:
    def __init__(self, repository: RecommendationsRepository, narrator: Narrator) -> None:
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
            snapshot = self._repository.fetch(scope)
        except Exception:
            return self._failed(FailureStage.QUERY, "Recommendations query failed", language)

        try:
            facts = localize_fact_set(SectionId.RECOMMENDATIONS, snapshot.to_fact_set(), language)
            evidence = snapshot.to_evidence_set()
            actions = snapshot.selected_actions
        except Exception:
            return self._failed(
                FailureStage.CALCULATION,
                "Recommendation selection, facts, or evidence construction failed",
                language,
            )

        if not snapshot.has_data:
            heading = "Recommended actions" if language is Language.EN else "行动建议"
            body = (
                "No monitoring records are available, so no evidence-linked action is proposed."
                if language is Language.EN
                else "监测范围内暂无记录，因此不提出缺少证据支撑的行动。"
            )
            return SectionResult(
                SectionId.RECOMMENDATIONS,
                SectionStatus.NO_DATA,
                f"## {heading}\n\n{body}",
                facts=facts,
                evidence=evidence,
            )

        if not snapshot.has_negative_articles:
            return SectionResult(
                SectionId.RECOMMENDATIONS,
                SectionStatus.COMPLETE,
                self._no_negative_markdown(language, facts),
                facts=facts,
                evidence=evidence,
            )

        if not actions:
            return self._failed(
                FailureStage.CALCULATION,
                "Negative records produced no recommendation action",
                language,
                facts,
                evidence,
            )

        try:
            markdown = self._narrator.narrate(
                NarrationRequest(
                    SectionId.RECOMMENDATIONS,
                    language,
                    facts,
                    evidence,
                    report_type=scope.report_type,
                )
            )
            self._validate_markdown(markdown, snapshot, facts, evidence, language)
        except Exception:
            return self._failed(
                FailureStage.LLM,
                "Recommendation narration or evidence validation failed",
                language,
                facts,
                evidence,
            )

        return SectionResult(
            section_id=SectionId.RECOMMENDATIONS,
            status=SectionStatus.COMPLETE,
            markdown=markdown,
            facts=facts,
            evidence=evidence,
        )

    @staticmethod
    def _no_negative_markdown(language: Language, facts: FactSet) -> str:
        values = facts.prompt_values()
        if language is Language.EN:
            return (
                "## Recommended actions\n\n"
                f"The scope contains {values['articles']} records and "
                f"{values['negativeArticles']} negative records "
                f"({values['negativeShare']}). No escalation action is triggered by "
                "the versioned playbook. Continue routine monitoring; this is not a "
                "guarantee that no operational or business issue exists."
            )
        return (
            "## 行动建议\n\n"
            f"监测范围内共 {values['articles']} 篇内容，其中负面 "
            f"{values['negativeArticles']} 篇（{values['negativeShare']}）。版本化行动"
            "代码本未触发升级动作，建议维持常规监测；这不保证不存在运营或业务问题。"
        )

    @staticmethod
    def _validate_markdown(
        markdown: str,
        snapshot: RecommendationsSnapshot,
        facts: FactSet,
        evidence: EvidenceSet,
        language: Language,
    ) -> None:
        values = facts.prompt_values()
        context_keys = (
            "articles",
            "negativeArticles",
            "negativeShare",
            "highCriticalNegativeArticles",
            "highCriticalNegativeShare",
            "classifiedNegativeArticles",
            "classifiedNegativeShare",
            "selectedActionCount",
            "omittedActionCount",
            "maximumActions",
        )
        if any(values[key] not in markdown for key in context_keys):
            raise ValueError("Recommendation narration must preserve context facts")

        cited_ids = tuple(match.strip() for match in EVIDENCE_CITATION.findall(markdown))
        if cited_ids != snapshot.action_citation_ids:
            raise ValueError("Recommendation citations must preserve action order")
        if any(record_id not in evidence.record_ids for record_id in cited_ids):
            raise ValueError("Recommendation narration cited unapproved evidence")

        citation_lines = [line for line in markdown.splitlines() if EVIDENCE_CITATION.search(line)]
        if len(citation_lines) != len(snapshot.selected_actions):
            raise ValueError("Every recommendation action needs one evidence line")
        evidence_by_id = {record.record_id: record for record in evidence.records}
        for action, line in zip(snapshot.selected_actions, citation_lines, strict=True):
            prefix = f"action{action.priority}"
            representative = evidence_by_id[action.representative.external_id]
            required = (
                values[f"{prefix}RepresentativeId"],
                representative.platform,
                representative.title,
                representative.summary,
            )
            if any(value not in line for value in required):
                raise ValueError("Recommendation evidence line changed approved evidence")

            action_block = markdown.split(
                f"### {action.priority}. {values[f'{prefix}LabelEn' if language is Language.EN else f'{prefix}LabelZh']}"
            )
            if len(action_block) != 2:
                raise ValueError("Recommendation action heading must preserve rank and label")
            block = action_block[1].split("\n### ", maxsplit=1)[0]
            required_keys = (
                f"{prefix}HorizonEn" if language is Language.EN else f"{prefix}HorizonZh",
                f"{prefix}OwnersEn" if language is Language.EN else f"{prefix}OwnersZh",
                f"{prefix}ActionEn" if language is Language.EN else f"{prefix}ActionZh",
                f"{prefix}VerificationEn" if language is Language.EN else f"{prefix}VerificationZh",
                f"{prefix}TriggerArticles",
                f"{prefix}TriggerShare",
                f"{prefix}HighCriticalArticles",
            )
            if any(values[key] not in block for key in required_keys):
                raise ValueError("Recommendation action changed approved playbook facts")

        boundaries = (
            (
                "Suggested role owners are not automatic assignments",
                "Playbook horizons are response targets",
                "human review must adapt every action to operational, legal, policy, and business context",
                "does not send messages, change the product, or open tickets",
                "deterministic rule order, not an effectiveness, confidence, or expected-value score",
            )
            if language is Language.EN
            else (
                "建议角色而非自动指派",
                "行动时限是 playbook 响应目标",
                "必须由人工结合运营、法律、政策和业务背景审核调整",
                "不会自动发送消息、修改产品或创建工单",
                "确定性规则排序，不是效果、置信度或预期价值评分",
            )
        )
        if any(text not in markdown for text in boundaries) or "![" in markdown:
            raise ValueError("Recommendation narration must preserve human-review boundaries")

    @staticmethod
    def _failed(
        stage: FailureStage,
        message: str,
        language: Language,
        facts: FactSet | None = None,
        evidence: EvidenceSet = EvidenceSet(),
    ) -> SectionResult:
        heading = "Recommended actions" if language is Language.EN else "行动建议"
        body = (
            "This section could not be generated. Please try again later."
            if language is Language.EN
            else "本章节生成失败，请稍后重试。"
        )
        return SectionResult(
            section_id=SectionId.RECOMMENDATIONS,
            status=SectionStatus.FAILED,
            markdown=f"## {heading}\n\n{body}",
            facts=facts,
            evidence=evidence,
            failure=SectionFailure(stage, message),
        )
