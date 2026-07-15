"""Auditable viewpoint facts and deterministic source evidence."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from report_engine.domain.evidence import Evidence, EvidenceSet
from report_engine.domain.facts import Fact, FactSet


SENTIMENT_ORDER = ("negative", "neutral", "positive")
VIEWPOINT_CATEGORY_LABELS = {
    "negative": "质疑/反对",
    "neutral": "中性/解释",
    "positive": "支持/缓和",
}


@dataclass(frozen=True)
class ViewpointEvidenceRecord:
    external_id: str
    title: str
    summary: str
    platform: str
    published_at: datetime
    sentiment: str
    total_engagement: int
    evidence_rank: int

    def __post_init__(self) -> None:
        required_text = (
            self.external_id,
            self.title,
            self.summary,
            self.platform,
        )
        if any(not value.strip() for value in required_text):
            raise ValueError("Viewpoint evidence text fields cannot be blank")
        if self.sentiment not in SENTIMENT_ORDER:
            raise ValueError("Unsupported viewpoint sentiment")
        if self.total_engagement < 0:
            raise ValueError("Evidence engagement cannot be negative")
        if self.evidence_rank not in (1, 2):
            raise ValueError("Evidence rank must be one or two")

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
class ViewpointsSnapshot:
    article_count: int
    positive_articles: int
    neutral_articles: int
    negative_articles: int
    evidence_records: tuple[ViewpointEvidenceRecord, ...]
    query_id: str

    def __post_init__(self) -> None:
        counts = (
            self.article_count,
            self.positive_articles,
            self.neutral_articles,
            self.negative_articles,
        )
        if min(counts) < 0:
            raise ValueError("Viewpoint counts cannot be negative")
        if sum(counts[1:]) != self.article_count:
            raise ValueError("Sentiment counts must equal the article count")
        if len(self.evidence_records) > 6:
            raise ValueError("Viewpoint evidence is limited to six records")
        if len(self.evidence_records) > self.article_count:
            raise ValueError("Evidence count cannot exceed article count")
        evidence_ids = [record.external_id for record in self.evidence_records]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("Viewpoint evidence IDs must be unique")

        evidence_counts = Counter(
            record.sentiment for record in self.evidence_records
        )
        population_counts = {
            "positive": self.positive_articles,
            "neutral": self.neutral_articles,
            "negative": self.negative_articles,
        }
        for sentiment in SENTIMENT_ORDER:
            if evidence_counts[sentiment] > 2:
                raise ValueError("Each sentiment is limited to two evidence records")
            if evidence_counts[sentiment] > population_counts[sentiment]:
                raise ValueError("Evidence cannot exceed its sentiment population")

        expected_order = sorted(
            self.evidence_records,
            key=lambda record: (
                SENTIMENT_ORDER.index(record.sentiment),
                record.evidence_rank,
            ),
        )
        if list(self.evidence_records) != expected_order:
            raise ValueError("Viewpoint evidence must use the fixed display order")
        for sentiment in SENTIMENT_ORDER:
            ranks = [
                record.evidence_rank
                for record in self.evidence_records
                if record.sentiment == sentiment
            ]
            if ranks != list(range(1, len(ranks) + 1)):
                raise ValueError("Evidence ranks must be contiguous within sentiment")
        if not self.query_id.strip():
            raise ValueError("Viewpoints query ID cannot be blank")

    @property
    def has_data(self) -> bool:
        return self.article_count > 0

    def sentiment_share(self, sentiment: str) -> Decimal:
        if sentiment not in SENTIMENT_ORDER:
            raise ValueError("Unsupported sentiment")
        if not self.article_count:
            return Decimal(0)
        count = {
            "positive": self.positive_articles,
            "neutral": self.neutral_articles,
            "negative": self.negative_articles,
        }[sentiment]
        return Decimal(count) / Decimal(self.article_count)

    def to_evidence_set(self) -> EvidenceSet:
        return EvidenceSet(
            records=tuple(record.to_evidence() for record in self.evidence_records)
        )

    def to_fact_set(self) -> FactSet:
        if not self.has_data:
            raise ValueError("Cannot create viewpoint facts for an empty snapshot")

        evidence_ids = tuple(
            record.external_id for record in self.evidence_records
        )
        evidence_counts = Counter(
            record.sentiment for record in self.evidence_records
        )
        platform_count = len(
            {record.platform for record in self.evidence_records}
        )
        facts = [
            Fact("articleCount", self.article_count, f"{self.article_count:,}", self.query_id),
            Fact(
                "positiveArticles",
                self.positive_articles,
                f"{self.positive_articles:,}",
                self.query_id,
            ),
            Fact(
                "neutralArticles",
                self.neutral_articles,
                f"{self.neutral_articles:,}",
                self.query_id,
            ),
            Fact(
                "negativeArticles",
                self.negative_articles,
                f"{self.negative_articles:,}",
                self.query_id,
            ),
        ]
        for sentiment in ("positive", "neutral", "negative"):
            share = self.sentiment_share(sentiment)
            facts.append(
                Fact(
                    f"{sentiment}Share",
                    share,
                    f"{share:.1%}",
                    "viewpoints.sentiment-share.v1",
                )
            )
        facts.extend(
            (
                Fact(
                    "evidenceCount",
                    len(evidence_ids),
                    f"{len(evidence_ids):,}",
                    "viewpoints.evidence-selection.v1",
                    source_record_ids=evidence_ids,
                ),
                Fact(
                    "negativeEvidenceCount",
                    evidence_counts["negative"],
                    f"{evidence_counts['negative']:,}",
                    "viewpoints.evidence-selection.v1",
                ),
                Fact(
                    "neutralEvidenceCount",
                    evidence_counts["neutral"],
                    f"{evidence_counts['neutral']:,}",
                    "viewpoints.evidence-selection.v1",
                ),
                Fact(
                    "positiveEvidenceCount",
                    evidence_counts["positive"],
                    f"{evidence_counts['positive']:,}",
                    "viewpoints.evidence-selection.v1",
                ),
                Fact(
                    "evidencePlatformCount",
                    platform_count,
                    f"{platform_count:,}",
                    "viewpoints.evidence-selection.v1",
                ),
            )
        )
        return FactSet(facts=tuple(facts))
