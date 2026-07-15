"""Auditable media-versus-social volume and sentiment facts."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from report_engine.domain.facts import Fact, FactSet


SOURCE_TYPE_ORDER = ("media", "social")
SOURCE_TYPE_LABELS_ZH = {"media": "媒体内容", "social": "社交内容"}


@dataclass(frozen=True)
class MediaSocialRow:
    source_type: str
    article_count: int
    positive_articles: int
    neutral_articles: int
    negative_articles: int
    platform_count: int

    def __post_init__(self) -> None:
        if self.source_type not in SOURCE_TYPE_ORDER:
            raise ValueError("Source type must be media or social")
        values = (
            self.article_count,
            self.positive_articles,
            self.neutral_articles,
            self.negative_articles,
            self.platform_count,
        )
        if min(values) < 0:
            raise ValueError("Media/social values cannot be negative")
        sentiment_total = (
            self.positive_articles + self.neutral_articles + self.negative_articles
        )
        if sentiment_total != self.article_count:
            raise ValueError("Source-type article total must equal sentiment counts")
        if self.article_count == 0 and self.platform_count != 0:
            raise ValueError("An absent source type cannot contain platforms")
        if self.article_count > 0 and self.platform_count == 0:
            raise ValueError("A populated source type must contain a platform")

    @property
    def label_zh(self) -> str:
        return SOURCE_TYPE_LABELS_ZH[self.source_type]

    @property
    def sentiment_shares(self) -> tuple[Decimal, Decimal, Decimal] | None:
        if self.article_count == 0:
            return None
        denominator = Decimal(self.article_count)
        return (
            Decimal(self.positive_articles) / denominator,
            Decimal(self.neutral_articles) / denominator,
            Decimal(self.negative_articles) / denominator,
        )

    @property
    def negative_share(self) -> Decimal | None:
        shares = self.sentiment_shares
        return None if shares is None else shares[2]


@dataclass(frozen=True)
class MediaSocialSnapshot:
    rows: tuple[MediaSocialRow, ...]
    query_id: str

    def __post_init__(self) -> None:
        source_types = tuple(row.source_type for row in self.rows)
        if source_types != SOURCE_TYPE_ORDER:
            raise ValueError("Media/social rows must contain media then social exactly once")

    @property
    def media(self) -> MediaSocialRow:
        return self.rows[0]

    @property
    def social(self) -> MediaSocialRow:
        return self.rows[1]

    @property
    def article_count(self) -> int:
        return self.media.article_count + self.social.article_count

    @property
    def negative_articles(self) -> int:
        return self.media.negative_articles + self.social.negative_articles

    @property
    def has_data(self) -> bool:
        return self.article_count > 0

    @property
    def comparison_available(self) -> bool:
        return self.media.article_count > 0 and self.social.article_count > 0

    @property
    def comparison_status(self) -> str:
        if not self.has_data:
            return "no_data"
        if not self.comparison_available:
            return "insufficient_group_coverage"
        return "comparable"

    def article_share(self, row: MediaSocialRow) -> Decimal:
        if not self.has_data:
            return Decimal(0)
        return Decimal(row.article_count) / Decimal(self.article_count)

    def negative_population_share(self, row: MediaSocialRow) -> Decimal:
        if self.negative_articles == 0:
            return Decimal(0)
        return Decimal(row.negative_articles) / Decimal(self.negative_articles)

    @property
    def social_minus_media_negative_share(self) -> Decimal | None:
        if not self.comparison_available:
            return None
        media_share = self.media.negative_share
        social_share = self.social.negative_share
        if media_share is None or social_share is None:
            raise ValueError("Populated source types require sentiment shares")
        return social_share - media_share

    @property
    def volume_leaders(self) -> tuple[MediaSocialRow, ...]:
        if not self.has_data:
            return ()
        leading_count = max(row.article_count for row in self.rows)
        return tuple(row for row in self.rows if row.article_count == leading_count)

    @property
    def negative_share_leaders(self) -> tuple[MediaSocialRow, ...]:
        if not self.comparison_available:
            return ()
        shares = tuple(row.negative_share for row in self.rows)
        if any(share is None for share in shares):
            raise ValueError("Populated source types require sentiment shares")
        leading_share = max(share for share in shares if share is not None)
        return tuple(row for row in self.rows if row.negative_share == leading_share)

    def to_fact_set(self) -> FactSet:
        if not self.has_data:
            raise ValueError("Cannot create media/social facts for an empty snapshot")

        volume_leaders = self.volume_leaders
        facts = [
            Fact("articles", self.article_count, f"{self.article_count:,}", self.query_id),
            Fact(
                "negativeArticles",
                self.negative_articles,
                f"{self.negative_articles:,}",
                self.query_id,
            ),
            Fact(
                "comparisonStatus",
                self.comparison_status,
                self.comparison_status,
                "media-social.coverage.v1",
            ),
            Fact(
                "sourceClassification",
                "source_type",
                "数据库 source_type 存储分类",
                "media-social.classification.v1",
            ),
            Fact(
                "volumeLeaders",
                "|".join(row.source_type for row in volume_leaders),
                "、".join(row.label_zh for row in volume_leaders),
                "media-social.volume-leaders.v1",
            ),
            Fact(
                "volumeLeaderCount",
                len(volume_leaders),
                f"{len(volume_leaders):,}",
                "media-social.volume-leaders.v1",
            ),
        ]

        for row in self.rows:
            prefix = row.source_type
            facts.extend(
                (
                    Fact(
                        f"{prefix}Label",
                        row.source_type,
                        row.label_zh,
                        "media-social.classification.v1",
                    ),
                    Fact(
                        f"{prefix}Articles",
                        row.article_count,
                        f"{row.article_count:,}",
                        self.query_id,
                    ),
                    Fact(
                        f"{prefix}ArticleShare",
                        self.article_share(row),
                        f"{self.article_share(row):.1%}",
                        "media-social.article-share.v1",
                    ),
                    Fact(
                        f"{prefix}PositiveArticles",
                        row.positive_articles,
                        f"{row.positive_articles:,}",
                        self.query_id,
                    ),
                    Fact(
                        f"{prefix}NeutralArticles",
                        row.neutral_articles,
                        f"{row.neutral_articles:,}",
                        self.query_id,
                    ),
                    Fact(
                        f"{prefix}NegativeArticles",
                        row.negative_articles,
                        f"{row.negative_articles:,}",
                        self.query_id,
                    ),
                    Fact(
                        f"{prefix}PlatformCount",
                        row.platform_count,
                        f"{row.platform_count:,}",
                        self.query_id,
                    ),
                    Fact(
                        f"{prefix}NegativePopulationShare",
                        self.negative_population_share(row),
                        f"{self.negative_population_share(row):.1%}",
                        "media-social.negative-population-share.v1",
                    ),
                )
            )
            shares = row.sentiment_shares
            if shares is not None:
                for sentiment, share in zip(
                    ("Positive", "Neutral", "Negative"), shares, strict=True
                ):
                    facts.append(
                        Fact(
                            f"{prefix}{sentiment}Share",
                            share,
                            f"{share:.1%}",
                            "media-social.sentiment-share.v1",
                        )
                    )

        delta = self.social_minus_media_negative_share
        if delta is not None:
            negative_leaders = self.negative_share_leaders
            facts.extend(
                (
                    Fact(
                        "socialMinusMediaNegativeShare",
                        delta,
                        f"{delta:+.1%}",
                        "media-social.negative-share-delta.v1",
                    ),
                    Fact(
                        "negativeShareLeaders",
                        "|".join(row.source_type for row in negative_leaders),
                        "、".join(row.label_zh for row in negative_leaders),
                        "media-social.negative-share-leaders.v1",
                    ),
                    Fact(
                        "negativeShareLeaderCount",
                        len(negative_leaders),
                        f"{len(negative_leaders):,}",
                        "media-social.negative-share-leaders.v1",
                    ),
                )
            )

        return FactSet(facts=tuple(facts))
