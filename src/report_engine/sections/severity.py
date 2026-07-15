"""Auditable negative-severity facts and deterministic source evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from report_engine.domain.evidence import Evidence, EvidenceSet
from report_engine.domain.facts import Fact, FactSet


SEVERITY_LABELS = {
    "low": "低",
    "medium": "中",
    "high": "高",
    "critical": "危急",
}


@dataclass(frozen=True)
class SeverityEvidenceRecord:
    external_id: str
    title: str
    summary: str
    platform: str
    published_at: datetime
    sentiment: str
    negative_score: int | None
    severity: str | None
    total_engagement: int

    def __post_init__(self) -> None:
        required_text = (
            self.external_id,
            self.title,
            self.summary,
            self.platform,
        )
        if any(not value.strip() for value in required_text):
            raise ValueError("Severity evidence text fields cannot be blank")
        if self.sentiment != "negative":
            raise ValueError("Severity evidence must have negative sentiment")
        if self.severity not in {*SEVERITY_LABELS, None}:
            raise ValueError("Unsupported severity label")
        if self.negative_score is not None and not 1 <= self.negative_score <= 5:
            raise ValueError("Negative score must be between 1 and 5")
        if self.total_engagement < 0:
            raise ValueError("Evidence engagement cannot be negative")

    def to_evidence(self) -> Evidence:
        return Evidence(
            record_id=self.external_id,
            title=self.title,
            summary=self.summary,
            platform=self.platform,
            published_at=self.published_at,
            sentiment=self.sentiment,
        )


@dataclass(frozen=True)
class SeveritySnapshot:
    negative_articles: int
    low_articles: int
    medium_articles: int
    high_articles: int
    critical_articles: int
    missing_severity_articles: int
    score_1_articles: int
    score_2_articles: int
    score_3_articles: int
    score_4_articles: int
    score_5_articles: int
    scored_negative_articles: int
    missing_score_articles: int
    average_negative_score: Decimal | None
    negative_engagement: int
    high_critical_engagement: int
    evidence_records: tuple[SeverityEvidenceRecord, ...]
    query_id: str

    def __post_init__(self) -> None:
        counts = (
            self.negative_articles,
            self.low_articles,
            self.medium_articles,
            self.high_articles,
            self.critical_articles,
            self.missing_severity_articles,
            self.score_1_articles,
            self.score_2_articles,
            self.score_3_articles,
            self.score_4_articles,
            self.score_5_articles,
            self.scored_negative_articles,
            self.missing_score_articles,
            self.negative_engagement,
            self.high_critical_engagement,
        )
        if min(counts) < 0:
            raise ValueError("Severity values cannot be negative")
        severity_total = (
            self.low_articles
            + self.medium_articles
            + self.high_articles
            + self.critical_articles
            + self.missing_severity_articles
        )
        if severity_total != self.negative_articles:
            raise ValueError("Severity counts must equal the negative article count")
        score_total = (
            self.score_1_articles
            + self.score_2_articles
            + self.score_3_articles
            + self.score_4_articles
            + self.score_5_articles
        )
        if score_total != self.scored_negative_articles:
            raise ValueError("Score buckets must equal the scored article count")
        if (
            self.scored_negative_articles + self.missing_score_articles
            != self.negative_articles
        ):
            raise ValueError(
                "Scored and missing-score counts must equal negative articles"
            )
        if (self.average_negative_score is None) != (
            self.scored_negative_articles == 0
        ):
            raise ValueError("Average score presence must match scored articles")
        if self.average_negative_score is not None and not (
            Decimal(1) <= self.average_negative_score <= Decimal(5)
        ):
            raise ValueError("Average negative score must be between 1 and 5")
        if self.high_critical_engagement > self.negative_engagement:
            raise ValueError(
                "High/critical engagement cannot exceed negative engagement"
            )
        if len(self.evidence_records) > 3:
            raise ValueError("Severity evidence is limited to three records")
        evidence_ids = [record.external_id for record in self.evidence_records]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("Severity evidence IDs must be unique")
        if len(evidence_ids) > self.negative_articles:
            raise ValueError("Evidence count cannot exceed negative articles")
        if not self.query_id.strip():
            raise ValueError("Severity query ID cannot be blank")

    @property
    def has_data(self) -> bool:
        return self.negative_articles > 0

    @property
    def high_critical_articles(self) -> int:
        return self.high_articles + self.critical_articles

    @property
    def high_critical_ratio(self) -> Decimal:
        if not self.negative_articles:
            return Decimal(0)
        return Decimal(self.high_critical_articles) / Decimal(self.negative_articles)

    @property
    def critical_ratio(self) -> Decimal:
        if not self.negative_articles:
            return Decimal(0)
        return Decimal(self.critical_articles) / Decimal(self.negative_articles)

    @property
    def high_critical_engagement_share(self) -> Decimal:
        if not self.negative_engagement:
            return Decimal(0)
        return Decimal(self.high_critical_engagement) / Decimal(
            self.negative_engagement
        )

    @property
    def highest_observed_severity(self) -> str | None:
        for severity, count in (
            ("critical", self.critical_articles),
            ("high", self.high_articles),
            ("medium", self.medium_articles),
            ("low", self.low_articles),
        ):
            if count:
                return severity
        return None

    def to_evidence_set(self) -> EvidenceSet:
        return EvidenceSet(
            records=tuple(record.to_evidence() for record in self.evidence_records)
        )

    def to_fact_set(self) -> FactSet:
        if not self.has_data:
            raise ValueError("Cannot create severity facts for an empty snapshot")

        highest = self.highest_observed_severity
        evidence_ids = tuple(record.external_id for record in self.evidence_records)
        query_counts = (
            ("negativeArticles", self.negative_articles),
            ("lowArticles", self.low_articles),
            ("mediumArticles", self.medium_articles),
            ("highArticles", self.high_articles),
            ("criticalArticles", self.critical_articles),
            ("missingSeverityArticles", self.missing_severity_articles),
            ("score1Articles", self.score_1_articles),
            ("score2Articles", self.score_2_articles),
            ("score3Articles", self.score_3_articles),
            ("score4Articles", self.score_4_articles),
            ("score5Articles", self.score_5_articles),
            ("scoredNegativeArticles", self.scored_negative_articles),
            ("missingScoreArticles", self.missing_score_articles),
        )
        facts = [
            Fact(key, value, f"{value:,}", self.query_id)
            for key, value in query_counts
        ]
        facts.extend(
            (
                Fact(
                    "averageNegativeScore",
                    self.average_negative_score,
                    f"{self.average_negative_score:.1f}"
                    if self.average_negative_score is not None
                    else "暂无",
                    self.query_id,
                ),
                Fact(
                    "highCriticalArticles",
                    self.high_critical_articles,
                    f"{self.high_critical_articles:,}",
                    "severity.high-critical.v1",
                ),
                Fact(
                    "highCriticalRatio",
                    self.high_critical_ratio,
                    f"{self.high_critical_ratio:.1%}",
                    "severity.high-critical-ratio.v1",
                ),
                Fact(
                    "criticalRatio",
                    self.critical_ratio,
                    f"{self.critical_ratio:.1%}",
                    "severity.critical-ratio.v1",
                ),
                Fact(
                    "negativeEngagement",
                    self.negative_engagement,
                    f"{self.negative_engagement:,}",
                    self.query_id,
                ),
                Fact(
                    "highCriticalEngagement",
                    self.high_critical_engagement,
                    f"{self.high_critical_engagement:,}",
                    self.query_id,
                ),
                Fact(
                    "highCriticalEngagementShare",
                    self.high_critical_engagement_share,
                    f"{self.high_critical_engagement_share:.1%}",
                    "severity.high-critical-engagement-share.v1",
                ),
                Fact(
                    "highestObservedSeverity",
                    highest,
                    SEVERITY_LABELS[highest] if highest is not None else "暂无",
                    "severity.highest-observed.v1",
                ),
                Fact(
                    "evidenceCount",
                    len(evidence_ids),
                    f"{len(evidence_ids):,}",
                    "severity.evidence-ranking.v1",
                    source_record_ids=evidence_ids,
                ),
            )
        )
        return FactSet(facts=tuple(facts))
