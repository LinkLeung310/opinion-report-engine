"""Deterministic, evidence-linked recommendation playbook facts."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from report_engine.domain.evidence import Evidence, EvidenceSet
from report_engine.domain.facts import Fact, FactSet
from report_engine.sections.negative_themes import (
    NegativeThemeSourceRecord,
    NegativeThemesSnapshot,
    SEVERITY_ORDER,
)


MAX_ACTIONS = 4
PLAYBOOK_SOURCE_ID = "recommendations.playbook.v1"
SELECTION_SOURCE_ID = "recommendations.selection.v1"
EVIDENCE_SOURCE_ID = "recommendations.evidence.v1"


@dataclass(frozen=True)
class RecommendationDefinition:
    action_id: str
    label_zh: str
    label_en: str
    owners_zh: str
    owners_en: str
    action_zh: str
    action_en: str
    verification_zh: str
    verification_en: str


ACTION_DEFINITIONS = {
    "triage_high_risk": RecommendationDefinition(
        "triage_high_risk",
        "核验高风险记录",
        "Triage high-risk records",
        "公关负责人、事件责任人",
        "PR lead, incident owner",
        "为每条高/危记录指定负责人和状态，并记录是否需要升级处置。",
        "Assign an owner and status to every high/critical record and document whether escalation is required.",
        "逐条核对负责人、当前状态、升级决定及其依据。",
        "Verify the owner, current status, escalation decision, and rationale for every record.",
    ),
    "restore_user_control": RecommendationDefinition(
        "restore_user_control",
        "核验用户控制路径",
        "Validate the user-control path",
        "产品/体验、客服",
        "Product/UX, Support",
        "核验受影响的控制路径，准备分步指引，并登记尚未解决的案例。",
        "Validate the affected control path, prepare step-by-step guidance, and log unresolved cases.",
        "复测入口与指引，抽查未解决案例是否有状态和责任人。",
        "Retest the control and guidance, then sample unresolved cases for a status and owner.",
    ),
    "explain_change": RecommendationDefinition(
        "explain_change",
        "建立变更说明单一来源",
        "Create one source of truth for the change",
        "产品、公关",
        "Product, PR",
        "准备一份单一事实来源，明确已变与未变范围，以及反馈或回退边界。",
        "Prepare one source of truth covering changed and unchanged scope plus feedback or rollback boundaries.",
        "由产品、运营与公关共同核对范围、例外和更新时间。",
        "Have Product, Operations, and PR verify scope, exceptions, and the last-updated time.",
    ),
    "close_feedback_loop": RecommendationDefinition(
        "close_feedback_loop",
        "建立反馈闭环",
        "Close the feedback loop",
        "公关、客服运营",
        "PR, Support operations",
        "确认已核准的关注点，公布受理与回应节奏，并维护可见状态。",
        "Acknowledge the approved concern, publish an intake and response cadence, and maintain a visible status.",
        "检查受理入口、下一次更新时间和已关闭事项是否可追踪。",
        "Check that the intake path, next update time, and closed items remain traceable.",
    ),
    "review_unresolved_negative": RecommendationDefinition(
        "review_unresolved_negative",
        "人工复核未归类负面",
        "Review unresolved negative coverage",
        "舆情分析、事件责任人",
        "Analyst, incident owner",
        "人工复核排名最高的未解决记录，并决定是否需要扩展版本化行动或主题代码本。",
        "Manually review the highest-ranked unresolved record and decide whether a versioned playbook or codebook extension is warranted.",
        "记录复核结论、证据 ID，以及扩展或不扩展代码本的理由。",
        "Record the review conclusion, Evidence ID, and rationale for extending or retaining the codebook.",
    ),
}

THEME_ACTION_IDS = {
    "user_agency": "restore_user_control",
    "transparency": "explain_change",
    "feedback_effectiveness": "close_feedback_loop",
}


def _rank_records(
    records: tuple[NegativeThemeSourceRecord, ...],
) -> tuple[NegativeThemeSourceRecord, ...]:
    return tuple(
        sorted(
            records,
            key=lambda record: (
                -SEVERITY_ORDER[record.severity],
                record.negative_score is None,
                -(record.negative_score or 0),
                -record.total_engagement,
                -record.published_at.timestamp(),
                record.external_id,
            ),
        )
    )


@dataclass(frozen=True)
class RecommendationAction:
    definition: RecommendationDefinition
    priority: int
    horizon_zh: str
    horizon_en: str
    trigger_records: tuple[NegativeThemeSourceRecord, ...]
    representative: NegativeThemeSourceRecord

    def __post_init__(self) -> None:
        if self.priority < 1:
            raise ValueError("Recommendation priority must be positive")
        if not self.trigger_records:
            raise ValueError("Recommendation actions require trigger records")
        if self.representative not in self.trigger_records:
            raise ValueError("Recommendation representative must be a trigger record")

    @property
    def action_id(self) -> str:
        return self.definition.action_id

    @property
    def source_record_ids(self) -> tuple[str, ...]:
        return tuple(record.external_id for record in self.trigger_records)

    @property
    def high_critical_articles(self) -> int:
        return sum(
            record.severity in {"high", "critical"}
            for record in self.trigger_records
        )


@dataclass(frozen=True)
class RecommendationsSnapshot:
    article_count: int
    negative_article_count: int
    records: tuple[NegativeThemeSourceRecord, ...]
    query_id: str

    def __post_init__(self) -> None:
        NegativeThemesSnapshot(
            self.article_count,
            self.negative_article_count,
            self.records,
            self.query_id,
        )

    @property
    def theme_snapshot(self) -> NegativeThemesSnapshot:
        return NegativeThemesSnapshot(
            self.article_count,
            self.negative_article_count,
            self.records,
            self.query_id,
        )

    @property
    def has_data(self) -> bool:
        return self.article_count > 0

    @property
    def has_negative_articles(self) -> bool:
        return self.negative_article_count > 0

    @property
    def selected_actions(self) -> tuple[RecommendationAction, ...]:
        candidates: list[
            tuple[
                RecommendationDefinition,
                str,
                str,
                tuple[NegativeThemeSourceRecord, ...],
                NegativeThemeSourceRecord,
            ]
        ] = []
        high_risk = tuple(
            record
            for record in self.records
            if record.severity in {"high", "critical"}
        )
        if high_risk:
            ranked = _rank_records(high_risk)
            candidates.append(
                (
                    ACTION_DEFINITIONS["triage_high_risk"],
                    "立即",
                    "immediate",
                    high_risk,
                    ranked[0],
                )
            )

        for theme in self.theme_snapshot.display_themes:
            action_id = THEME_ACTION_IDS.get(theme.theme_id)
            if action_id is None:
                continue
            urgent = theme.high_critical_articles > 0 or theme.demand_articles > 0
            candidates.append(
                (
                    ACTION_DEFINITIONS[action_id],
                    "24小时内" if urgent else "72小时内",
                    "within 24 hours" if urgent else "within 72 hours",
                    theme.records,
                    theme.representative,
                )
            )

        if not candidates and self.records:
            ranked = _rank_records(self.records)
            candidates.append(
                (
                    ACTION_DEFINITIONS["review_unresolved_negative"],
                    "72小时内",
                    "within 72 hours",
                    self.records,
                    ranked[0],
                )
            )

        return tuple(
            RecommendationAction(definition, index, horizon_zh, horizon_en, records, representative)
            for index, (definition, horizon_zh, horizon_en, records, representative) in enumerate(
                candidates[:MAX_ACTIONS], start=1
            )
        )

    @property
    def candidate_action_count(self) -> int:
        return len(self.selected_actions)

    @property
    def omitted_action_count(self) -> int:
        return max(0, self.candidate_action_count - MAX_ACTIONS)

    @property
    def action_citation_ids(self) -> tuple[str, ...]:
        return tuple(
            action.representative.external_id for action in self.selected_actions
        )

    def to_evidence_set(self) -> EvidenceSet:
        unique: dict[str, Evidence] = {}
        for action in self.selected_actions:
            representative = action.representative
            unique.setdefault(representative.external_id, representative.to_evidence())
        return EvidenceSet(records=tuple(unique.values()))

    def to_fact_set(self) -> FactSet:
        negative_share = (
            Decimal(self.negative_article_count) / Decimal(self.article_count)
            if self.article_count
            else Decimal(0)
        )
        high_critical_ids = tuple(
            record.external_id
            for record in self.records
            if record.severity in {"high", "critical"}
        )
        high_critical_share = (
            Decimal(len(high_critical_ids)) / Decimal(self.negative_article_count)
            if self.negative_article_count
            else Decimal(0)
        )
        classified_ids = self.theme_snapshot.classified_record_ids
        classified_share = (
            Decimal(len(classified_ids)) / Decimal(self.negative_article_count)
            if self.negative_article_count
            else Decimal(0)
        )
        facts = [
            Fact("articles", self.article_count, f"{self.article_count:,}", self.query_id),
            Fact("negativeArticles", self.negative_article_count, f"{self.negative_article_count:,}", self.query_id),
            Fact("negativeShare", negative_share, f"{negative_share:.1%}", self.query_id),
            Fact("highCriticalNegativeArticles", len(high_critical_ids), f"{len(high_critical_ids):,}", SELECTION_SOURCE_ID, high_critical_ids),
            Fact("highCriticalNegativeShare", high_critical_share, f"{high_critical_share:.1%}", SELECTION_SOURCE_ID, high_critical_ids),
            Fact("classifiedNegativeArticles", len(classified_ids), f"{len(classified_ids):,}", SELECTION_SOURCE_ID, classified_ids),
            Fact("classifiedNegativeShare", classified_share, f"{classified_share:.1%}", SELECTION_SOURCE_ID, classified_ids),
            Fact("candidateActionCount", self.candidate_action_count, f"{self.candidate_action_count:,}", SELECTION_SOURCE_ID),
            Fact("selectedActionCount", len(self.selected_actions), f"{len(self.selected_actions):,}", SELECTION_SOURCE_ID),
            Fact("omittedActionCount", self.omitted_action_count, f"{self.omitted_action_count:,}", SELECTION_SOURCE_ID),
            Fact("maximumActions", MAX_ACTIONS, str(MAX_ACTIONS), PLAYBOOK_SOURCE_ID),
        ]
        for action in self.selected_actions:
            prefix = f"action{action.priority}"
            trigger_share = Decimal(len(action.trigger_records)) / Decimal(
                self.negative_article_count
            )
            definition = action.definition
            values = (
                ("Id", action.action_id, action.action_id, PLAYBOOK_SOURCE_ID),
                ("Priority", action.priority, str(action.priority), SELECTION_SOURCE_ID),
                ("LabelZh", definition.label_zh, definition.label_zh, PLAYBOOK_SOURCE_ID),
                ("LabelEn", definition.label_en, definition.label_en, PLAYBOOK_SOURCE_ID),
                ("HorizonZh", action.horizon_zh, action.horizon_zh, PLAYBOOK_SOURCE_ID),
                ("HorizonEn", action.horizon_en, action.horizon_en, PLAYBOOK_SOURCE_ID),
                ("OwnersZh", definition.owners_zh, definition.owners_zh, PLAYBOOK_SOURCE_ID),
                ("OwnersEn", definition.owners_en, definition.owners_en, PLAYBOOK_SOURCE_ID),
                ("ActionZh", definition.action_zh, definition.action_zh, PLAYBOOK_SOURCE_ID),
                ("ActionEn", definition.action_en, definition.action_en, PLAYBOOK_SOURCE_ID),
                ("VerificationZh", definition.verification_zh, definition.verification_zh, PLAYBOOK_SOURCE_ID),
                ("VerificationEn", definition.verification_en, definition.verification_en, PLAYBOOK_SOURCE_ID),
                ("TriggerArticles", len(action.trigger_records), f"{len(action.trigger_records):,}", SELECTION_SOURCE_ID),
                ("TriggerShare", trigger_share, f"{trigger_share:.1%}", SELECTION_SOURCE_ID),
                ("HighCriticalArticles", action.high_critical_articles, f"{action.high_critical_articles:,}", SELECTION_SOURCE_ID),
                ("RepresentativeId", action.representative.external_id, action.representative.external_id, EVIDENCE_SOURCE_ID),
            )
            facts.extend(
                Fact(
                    f"{prefix}{suffix}",
                    raw_value,
                    formatted_value,
                    source_id,
                    (action.representative.external_id,)
                    if suffix == "RepresentativeId"
                    else action.source_record_ids
                    if source_id == SELECTION_SOURCE_ID
                    else (),
                )
                for suffix, raw_value, formatted_value, source_id in values
            )
        return FactSet(facts=tuple(facts))
