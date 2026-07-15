"""Auditable interaction composition, concentration, and ranked source evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from report_engine.domain.evidence import Evidence, EvidenceSet
from report_engine.domain.facts import Fact, FactSet


SENTIMENTS = ("positive", "neutral", "negative")
SENTIMENT_LABELS = {
    "positive": "正面",
    "neutral": "中性",
    "negative": "负面",
}


@dataclass(frozen=True)
class EngagementRecord:
    external_id: str
    title: str
    summary: str
    platform: str
    published_at: datetime
    sentiment: str
    likes: int
    comments: int
    shares: int
    favorites: int
    engagement_rank: int

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (self.external_id, self.title, self.summary, self.platform)
        ):
            raise ValueError("Engagement record text fields cannot be blank")
        if self.published_at.utcoffset() is None:
            raise ValueError("Engagement record publication time must be timezone-aware")
        if self.sentiment not in SENTIMENTS:
            raise ValueError("Unsupported engagement-record sentiment")
        if min(self.likes, self.comments, self.shares, self.favorites) < 0:
            raise ValueError("Engagement counters cannot be negative")
        if self.total_engagement <= 0:
            raise ValueError("Ranked engagement records must have positive engagement")
        if not 1 <= self.engagement_rank <= 5:
            raise ValueError("Engagement rank must be between one and five")

    @property
    def total_engagement(self) -> int:
        return self.likes + self.comments + self.shares + self.favorites

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
class EngagementSnapshot:
    article_count: int
    positive_total_engagement_articles: int
    zero_engagement_articles: int
    likes: int
    comments: int
    shares: int
    favorites: int
    leading_record_count: int
    records: tuple[EngagementRecord, ...]
    query_id: str

    chart_record_limit = 5
    evidence_record_limit = 3

    def __post_init__(self) -> None:
        values = (
            self.article_count,
            self.positive_total_engagement_articles,
            self.zero_engagement_articles,
            self.likes,
            self.comments,
            self.shares,
            self.favorites,
            self.leading_record_count,
        )
        if min(values) < 0:
            raise ValueError("Engagement snapshot values cannot be negative")
        if (
            self.positive_total_engagement_articles + self.zero_engagement_articles
            != self.article_count
        ):
            raise ValueError("Positive and zero engagement counts must equal articles")
        expected_records = min(
            self.chart_record_limit,
            self.positive_total_engagement_articles,
        )
        if len(self.records) != expected_records:
            raise ValueError("Engagement records must contain the complete display set")

        ids = [record.external_id for record in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("Engagement record IDs must be unique")
        ranks = [record.engagement_rank for record in self.records]
        if ranks != list(range(1, len(ranks) + 1)):
            raise ValueError("Engagement ranks must be contiguous")
        expected_order = sorted(
            self.records,
            key=lambda record: (
                -record.total_engagement,
                -record.published_at.timestamp(),
                record.external_id,
            ),
        )
        if list(self.records) != expected_order:
            raise ValueError("Engagement records must use deterministic rank order")
        for field in ("likes", "comments", "shares", "favorites"):
            if sum(getattr(record, field) for record in self.records) > getattr(
                self, field
            ):
                raise ValueError(
                    "Displayed engagement counters cannot exceed aggregate totals"
                )

        if self.total_engagement == 0:
            if self.leading_record_count or self.records:
                raise ValueError("Zero engagement cannot have leaders or ranked records")
        else:
            if not 1 <= self.leading_record_count <= self.positive_total_engagement_articles:
                raise ValueError("Positive engagement requires a valid leader count")
            leading_total = self.records[0].total_engagement
            visible_leaders = min(self.leading_record_count, len(self.records))
            if any(
                record.total_engagement != leading_total
                for record in self.records[:visible_leaders]
            ):
                raise ValueError("Leading engagement records must share the maximum")
            if (
                self.leading_record_count < len(self.records)
                and self.records[self.leading_record_count].total_engagement
                >= leading_total
            ):
                raise ValueError("Non-leading records must be below the maximum")
        if not self.query_id.strip():
            raise ValueError("Engagement query ID cannot be blank")

    @property
    def has_articles(self) -> bool:
        return self.article_count > 0

    @property
    def has_engagement(self) -> bool:
        return self.total_engagement > 0

    @property
    def total_engagement(self) -> int:
        return self.likes + self.comments + self.shares + self.favorites

    @property
    def comments_and_shares(self) -> int:
        return self.comments + self.shares

    def action_share(self, count: int) -> Decimal:
        if count < 0:
            raise ValueError("Engagement action count cannot be negative")
        if not self.total_engagement:
            return Decimal(0)
        return Decimal(count) / Decimal(self.total_engagement)

    @property
    def comments_and_shares_share(self) -> Decimal:
        return self.action_share(self.comments_and_shares)

    @property
    def engagement_per_article(self) -> Decimal:
        if not self.article_count:
            return Decimal(0)
        return Decimal(self.total_engagement) / Decimal(self.article_count)

    @property
    def evidence_records(self) -> tuple[EngagementRecord, ...]:
        return self.records[: self.evidence_record_limit]

    @property
    def top_record_share(self) -> Decimal:
        if not self.has_engagement:
            return Decimal(0)
        return self.action_share(self.records[0].total_engagement)

    @property
    def top_three_records(self) -> tuple[EngagementRecord, ...]:
        return self.records[: self.evidence_record_limit]

    @property
    def top_three_records_share(self) -> Decimal:
        return self.action_share(
            sum(record.total_engagement for record in self.top_three_records)
        )

    def to_evidence_set(self) -> EvidenceSet:
        return EvidenceSet(
            records=tuple(record.to_evidence() for record in self.evidence_records)
        )

    def to_fact_set(self) -> FactSet:
        if not self.has_articles:
            raise ValueError("Cannot create engagement facts for an empty snapshot")

        action_counts = (
            ("likes", self.likes),
            ("comments", self.comments),
            ("shares", self.shares),
            ("favorites", self.favorites),
        )
        facts = [
            Fact("articles", self.article_count, f"{self.article_count:,}", self.query_id),
            Fact(
                "positiveTotalEngagementArticles",
                self.positive_total_engagement_articles,
                f"{self.positive_total_engagement_articles:,}",
                self.query_id,
            ),
            Fact(
                "zeroEngagementArticles",
                self.zero_engagement_articles,
                f"{self.zero_engagement_articles:,}",
                self.query_id,
            ),
            Fact(
                "totalEngagement",
                self.total_engagement,
                f"{self.total_engagement:,}",
                self.query_id,
            ),
        ]
        for key, count in action_counts:
            facts.extend(
                (
                    Fact(key, count, f"{count:,}", self.query_id),
                    Fact(
                        f"{key}Share",
                        self.action_share(count),
                        f"{self.action_share(count):.1%}",
                        "engagement.action-share.v1",
                    ),
                )
            )
        facts.extend(
            (
                Fact(
                    "commentsAndShares",
                    self.comments_and_shares,
                    f"{self.comments_and_shares:,}",
                    "engagement.comments-shares.v1",
                ),
                Fact(
                    "commentsAndSharesShare",
                    self.comments_and_shares_share,
                    f"{self.comments_and_shares_share:.1%}",
                    "engagement.comments-shares-share.v1",
                ),
                Fact(
                    "engagementPerArticle",
                    self.engagement_per_article,
                    f"{self.engagement_per_article:,.1f}",
                    "engagement.per-article.v1",
                ),
                Fact(
                    "leadingRecordCount",
                    self.leading_record_count,
                    f"{self.leading_record_count:,}",
                    "engagement.leaders.v1",
                ),
                Fact(
                    "leadingRecordId",
                    self.records[0].external_id
                    if self.has_engagement and self.leading_record_count == 1
                    else None,
                    self.records[0].external_id
                    if self.has_engagement and self.leading_record_count == 1
                    else "并列" if self.has_engagement else "暂无",
                    "engagement.leaders.v1",
                    source_record_ids=(self.records[0].external_id,)
                    if self.has_engagement and self.leading_record_count == 1
                    else (),
                ),
                Fact(
                    "leadingRecordTotal",
                    self.records[0].total_engagement if self.has_engagement else 0,
                    f"{self.records[0].total_engagement:,}"
                    if self.has_engagement
                    else "0",
                    self.query_id,
                    source_record_ids=(self.records[0].external_id,)
                    if self.has_engagement and self.leading_record_count == 1
                    else (),
                ),
                Fact(
                    "topRecordShare",
                    self.top_record_share,
                    f"{self.top_record_share:.1%}",
                    "engagement.concentration.v1",
                    source_record_ids=(self.records[0].external_id,)
                    if self.has_engagement
                    else (),
                ),
                Fact(
                    "topThreeRecordCount",
                    len(self.top_three_records),
                    f"{len(self.top_three_records):,}",
                    "engagement.concentration.v1",
                ),
                Fact(
                    "topThreeRecordsShare",
                    self.top_three_records_share,
                    f"{self.top_three_records_share:.1%}",
                    "engagement.concentration.v1",
                    source_record_ids=tuple(
                        record.external_id for record in self.top_three_records
                    ),
                ),
                Fact(
                    "displayRecordCount",
                    len(self.records),
                    f"{len(self.records):,}",
                    "engagement.ranking.v1",
                    source_record_ids=tuple(
                        record.external_id for record in self.records
                    ),
                ),
                Fact(
                    "evidenceCount",
                    len(self.evidence_records),
                    f"{len(self.evidence_records):,}",
                    "engagement.evidence-selection.v1",
                    source_record_ids=tuple(
                        record.external_id for record in self.evidence_records
                    ),
                ),
            )
        )
        for record in self.records:
            prefix = f"record{record.engagement_rank}"
            source_ids = (record.external_id,)
            record_values = (
                ("Rank", record.engagement_rank, f"{record.engagement_rank}"),
                ("Id", record.external_id, record.external_id),
                ("Title", record.title, record.title),
                ("Platform", record.platform, record.platform),
                ("Sentiment", record.sentiment, SENTIMENT_LABELS[record.sentiment]),
                ("Likes", record.likes, f"{record.likes:,}"),
                ("Comments", record.comments, f"{record.comments:,}"),
                ("Shares", record.shares, f"{record.shares:,}"),
                ("Favorites", record.favorites, f"{record.favorites:,}"),
                ("Total", record.total_engagement, f"{record.total_engagement:,}"),
            )
            facts.extend(
                Fact(
                    f"{prefix}{suffix}",
                    raw_value,
                    formatted_value,
                    self.query_id,
                    source_record_ids=source_ids,
                )
                for suffix, raw_value, formatted_value in record_values
            )
            share = self.action_share(record.total_engagement)
            facts.append(
                Fact(
                    f"{prefix}Share",
                    share,
                    f"{share:.1%}",
                    "engagement.record-share.v1",
                    source_record_ids=source_ids,
                )
            )
        return FactSet(facts=tuple(facts))
