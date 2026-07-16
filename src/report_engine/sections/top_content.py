"""Auditable cross-signal representative-content facts and evidence."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from report_engine.domain.evidence import Evidence, EvidenceSet
from report_engine.domain.facts import Fact, FactSet


CATEGORIES = ("dual_signal", "engagement_only", "risk_only")
CATEGORY_LABELS = {
    "dual_signal": "双信号代表",
    "engagement_only": "仅高互动代表",
    "risk_only": "仅高风险代表",
}
SENTIMENT_LABELS = {
    "positive": "正面",
    "neutral": "中性",
    "negative": "负面",
}
SEVERITY_LABELS = {
    None: "未分类",
    "low": "低",
    "medium": "中",
    "high": "高",
    "critical": "危",
}


@dataclass(frozen=True)
class TopContentRecord:
    external_id: str
    title: str
    summary: str
    platform: str
    published_at: datetime
    sentiment: str
    severity: str | None
    negative_score: int | None
    likes: int
    comments: int
    shares: int
    favorites: int
    engagement_rank: int | None
    risk_rank: int | None

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (self.external_id, self.title, self.summary, self.platform)
        ):
            raise ValueError("Top-content source text fields cannot be blank")
        if self.published_at.utcoffset() is None:
            raise ValueError("Top-content publication time must be timezone-aware")
        if self.sentiment not in SENTIMENT_LABELS:
            raise ValueError("Unsupported top-content sentiment")
        if self.severity not in SEVERITY_LABELS:
            raise ValueError("Unsupported top-content severity")
        if self.negative_score is not None and not 1 <= self.negative_score <= 5:
            raise ValueError("Top-content negative score must be between one and five")
        if min(self.likes, self.comments, self.shares, self.favorites) < 0:
            raise ValueError("Top-content engagement counters cannot be negative")
        if self.engagement_rank is not None and self.engagement_rank < 1:
            raise ValueError("Top-content engagement rank must be positive")
        if self.risk_rank is not None and self.risk_rank < 1:
            raise ValueError("Top-content risk rank must be positive")
        if not self.is_engagement_representative and not self.is_risk_representative:
            raise ValueError("Top-content record must belong to a selected signal")
        if self.is_engagement_representative and self.total_engagement <= 0:
            raise ValueError("Engagement representative requires positive counters")
        if self.is_risk_representative and not self.has_high_risk_signal:
            raise ValueError("Risk representative requires an explicit high-risk signal")

    @property
    def total_engagement(self) -> int:
        return self.likes + self.comments + self.shares + self.favorites

    @property
    def is_engagement_representative(self) -> bool:
        return self.engagement_rank is not None and self.engagement_rank <= 3

    @property
    def is_risk_representative(self) -> bool:
        return self.risk_rank is not None and self.risk_rank <= 3

    @property
    def has_high_risk_signal(self) -> bool:
        return self.sentiment == "negative" and (
            self.severity in {"high", "critical"}
            or (self.negative_score is not None and self.negative_score >= 4)
        )

    @property
    def category(self) -> str:
        if self.is_engagement_representative and self.is_risk_representative:
            return "dual_signal"
        if self.is_engagement_representative:
            return "engagement_only"
        return "risk_only"

    @property
    def category_label(self) -> str:
        return CATEGORY_LABELS[self.category]

    @property
    def severity_label(self) -> str:
        if self.sentiment != "negative":
            return "不适用"
        return SEVERITY_LABELS[self.severity]

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
class TopContentSnapshot:
    article_count: int
    positive_engagement_articles: int
    high_risk_signal_articles: int
    total_engagement: int
    records: tuple[TopContentRecord, ...]
    query_id: str

    def __post_init__(self) -> None:
        counts = (
            self.article_count,
            self.positive_engagement_articles,
            self.high_risk_signal_articles,
            self.total_engagement,
        )
        if min(counts) < 0:
            raise ValueError("Top-content aggregate values cannot be negative")
        if self.positive_engagement_articles > self.article_count:
            raise ValueError("Positive-engagement count cannot exceed articles")
        if self.high_risk_signal_articles > self.article_count:
            raise ValueError("High-risk-signal count cannot exceed articles")
        if not self.query_id.strip():
            raise ValueError("Top-content query ID cannot be blank")

        ids = [record.external_id for record in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("Top-content record IDs must be unique")
        if len(self.records) > min(6, self.article_count):
            raise ValueError("Top-content shortlist exceeds its limit")
        if sum(record.total_engagement for record in self.records) > self.total_engagement:
            raise ValueError("Selected engagement cannot exceed the scoped total")

        engagement_records = sum(
            record.is_engagement_representative for record in self.records
        )
        risk_records = sum(record.is_risk_representative for record in self.records)
        if engagement_records != min(3, self.positive_engagement_articles):
            raise ValueError("Top-content engagement shortlist is incomplete")
        if risk_records != min(3, self.high_risk_signal_articles):
            raise ValueError("Top-content risk shortlist is incomplete")

        engagement_ranks = [
            record.engagement_rank
            for record in self.records
            if record.engagement_rank is not None
        ]
        risk_ranks = [
            record.risk_rank for record in self.records if record.risk_rank is not None
        ]
        if len(engagement_ranks) != len(set(engagement_ranks)):
            raise ValueError("Top-content engagement ranks must be unique")
        if len(risk_ranks) != len(set(risk_ranks)):
            raise ValueError("Top-content risk ranks must be unique")

        expected_order = sorted(
            self.records,
            key=lambda record: (
                CATEGORIES.index(record.category),
                record.risk_rank if record.risk_rank is not None else 10**9,
                record.engagement_rank
                if record.engagement_rank is not None
                else 10**9,
                record.external_id,
            ),
        )
        if list(self.records) != expected_order:
            raise ValueError("Top-content records must use the fixed display order")

        if not self.article_count:
            if any(counts[1:]) or self.records:
                raise ValueError("Empty top-content scope cannot have signals")
        elif not self.positive_engagement_articles and not self.high_risk_signal_articles:
            if self.records:
                raise ValueError("No-signal top-content scope cannot have records")

    @property
    def has_articles(self) -> bool:
        return self.article_count > 0

    @property
    def has_selected_records(self) -> bool:
        return bool(self.records)

    @property
    def selected_engagement(self) -> int:
        return sum(record.total_engagement for record in self.records)

    @property
    def selected_engagement_share(self) -> Decimal:
        if not self.total_engagement:
            return Decimal(0)
        return Decimal(self.selected_engagement) / Decimal(self.total_engagement)

    @property
    def category_counts(self) -> Counter[str]:
        return Counter(record.category for record in self.records)

    def to_evidence_set(self) -> EvidenceSet:
        return EvidenceSet(records=tuple(record.to_evidence() for record in self.records))

    def to_fact_set(self) -> FactSet:
        if not self.has_articles:
            raise ValueError("Cannot create top-content facts for an empty snapshot")

        selected_ids = tuple(record.external_id for record in self.records)
        counts = self.category_counts
        facts = [
            Fact("articles", self.article_count, f"{self.article_count:,}", self.query_id),
            Fact(
                "positiveEngagementArticles",
                self.positive_engagement_articles,
                f"{self.positive_engagement_articles:,}",
                self.query_id,
            ),
            Fact(
                "highRiskSignalArticles",
                self.high_risk_signal_articles,
                f"{self.high_risk_signal_articles:,}",
                self.query_id,
            ),
            Fact(
                "totalEngagement",
                self.total_engagement,
                f"{self.total_engagement:,}",
                self.query_id,
            ),
            Fact(
                "selectedCount",
                len(self.records),
                f"{len(self.records):,}",
                "top-content.selection.v1",
                source_record_ids=selected_ids,
            ),
            Fact(
                "dualSignalCount",
                counts["dual_signal"],
                f"{counts['dual_signal']:,}",
                "top-content.selection.v1",
            ),
            Fact(
                "engagementOnlyCount",
                counts["engagement_only"],
                f"{counts['engagement_only']:,}",
                "top-content.selection.v1",
            ),
            Fact(
                "riskOnlyCount",
                counts["risk_only"],
                f"{counts['risk_only']:,}",
                "top-content.selection.v1",
            ),
            Fact(
                "selectedEngagement",
                self.selected_engagement,
                f"{self.selected_engagement:,}",
                "top-content.selected-engagement.v1",
                source_record_ids=selected_ids,
            ),
            Fact(
                "selectedEngagementShare",
                self.selected_engagement_share,
                f"{self.selected_engagement_share:.1%}",
                "top-content.selected-engagement-share.v1",
                source_record_ids=selected_ids,
            ),
        ]
        for index, record in enumerate(self.records, start=1):
            prefix = f"record{index}"
            source_ids = (record.external_id,)
            values = (
                ("Id", record.external_id, record.external_id),
                ("Category", record.category, record.category_label),
                ("Platform", record.platform, record.platform),
                ("Sentiment", record.sentiment, SENTIMENT_LABELS[record.sentiment]),
                (
                    "EngagementRank",
                    record.engagement_rank,
                    str(record.engagement_rank)
                    if record.engagement_rank is not None
                    else "未排名",
                ),
                (
                    "RiskRank",
                    record.risk_rank,
                    str(record.risk_rank) if record.risk_rank is not None else "未排名",
                ),
                ("Likes", record.likes, f"{record.likes:,}"),
                ("Comments", record.comments, f"{record.comments:,}"),
                ("Shares", record.shares, f"{record.shares:,}"),
                ("Favorites", record.favorites, f"{record.favorites:,}"),
                ("TotalEngagement", record.total_engagement, f"{record.total_engagement:,}"),
                ("Severity", record.severity, record.severity_label),
                (
                    "NegativeScore",
                    record.negative_score,
                    str(record.negative_score)
                    if record.negative_score is not None
                    else "未提供",
                ),
            )
            facts.extend(
                Fact(
                    f"{prefix}{suffix}",
                    raw_value,
                    formatted_value,
                    self.query_id,
                    source_record_ids=source_ids,
                )
                for suffix, raw_value, formatted_value in values
            )
        return FactSet(facts=tuple(facts))
