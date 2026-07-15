"""Deterministic platform comparison rows and auditable leader facts."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from report_engine.domain.facts import Fact, FactSet


@dataclass(frozen=True)
class PlatformRow:
    platform: str
    article_count: int
    positive_articles: int
    neutral_articles: int
    negative_articles: int
    likes: int
    comments: int
    shares: int
    favorites: int

    def __post_init__(self) -> None:
        if not self.platform.strip():
            raise ValueError("Platform label cannot be blank")
        values = (
            self.article_count,
            self.positive_articles,
            self.neutral_articles,
            self.negative_articles,
            self.likes,
            self.comments,
            self.shares,
            self.favorites,
        )
        if min(values) < 0:
            raise ValueError("Platform values cannot be negative")
        sentiment_total = (
            self.positive_articles + self.neutral_articles + self.negative_articles
        )
        if sentiment_total != self.article_count:
            raise ValueError("Platform article total must equal its sentiment counts")

    @property
    def total_engagement(self) -> int:
        return self.likes + self.comments + self.shares + self.favorites

    @property
    def negative_ratio(self) -> Decimal:
        if self.article_count == 0:
            return Decimal(0)
        return Decimal(self.negative_articles) / Decimal(self.article_count)

    @property
    def engagement_per_article(self) -> Decimal:
        if self.article_count == 0:
            return Decimal(0)
        return Decimal(self.total_engagement) / Decimal(self.article_count)


@dataclass(frozen=True)
class PlatformsSnapshot:
    rows: tuple[PlatformRow, ...]
    query_id: str

    chart_platform_limit = 7

    def __post_init__(self) -> None:
        labels = [row.platform for row in self.rows]
        if len(labels) != len(set(labels)):
            raise ValueError("Platform labels must be unique")
        if any(row.article_count == 0 for row in self.rows):
            raise ValueError("Platform query rows must contain at least one article")

    @property
    def has_data(self) -> bool:
        return bool(self.rows)

    @property
    def article_count(self) -> int:
        return sum(row.article_count for row in self.rows)

    @property
    def negative_articles(self) -> int:
        return sum(row.negative_articles for row in self.rows)

    @property
    def total_engagement(self) -> int:
        return sum(row.total_engagement for row in self.rows)

    @property
    def ranked_rows(self) -> tuple[PlatformRow, ...]:
        return tuple(
            sorted(
                self.rows,
                key=lambda row: (-row.article_count, -row.total_engagement, row.platform),
            )
        )

    @property
    def volume_leaders(self) -> tuple[PlatformRow, ...]:
        if not self.rows:
            return ()
        leading_count = max(row.article_count for row in self.rows)
        return tuple(row for row in self.ranked_rows if row.article_count == leading_count)

    @property
    def negative_leader(self) -> PlatformRow | None:
        if self.negative_articles == 0:
            return None
        return min(
            self.rows,
            key=lambda row: (
                -row.negative_articles,
                -row.negative_ratio,
                -row.total_engagement,
                row.platform,
            ),
        )

    @property
    def engagement_leader(self) -> PlatformRow | None:
        if not self.rows:
            return None
        return min(
            self.rows,
            key=lambda row: (-row.total_engagement, -row.article_count, row.platform),
        )

    @property
    def display_rows(self) -> tuple[PlatformRow, ...]:
        ranked = self.ranked_rows
        if len(ranked) <= self.chart_platform_limit:
            return ranked
        head = ranked[: self.chart_platform_limit]
        tail = ranked[self.chart_platform_limit :]
        other = PlatformRow(
            platform="其他",
            article_count=sum(row.article_count for row in tail),
            positive_articles=sum(row.positive_articles for row in tail),
            neutral_articles=sum(row.neutral_articles for row in tail),
            negative_articles=sum(row.negative_articles for row in tail),
            likes=sum(row.likes for row in tail),
            comments=sum(row.comments for row in tail),
            shares=sum(row.shares for row in tail),
            favorites=sum(row.favorites for row in tail),
        )
        return (*head, other)

    def to_fact_set(self) -> FactSet:
        if not self.has_data:
            raise ValueError("Cannot create platform facts for an empty snapshot")

        leaders = self.volume_leaders
        engagement_leader = self.engagement_leader
        if not leaders or engagement_leader is None:
            raise ValueError("Platform leaders require non-empty rows")

        leading_count = leaders[0].article_count
        leading_share = Decimal(leading_count) / Decimal(self.article_count)
        engagement_share = Decimal(engagement_leader.total_engagement) / Decimal(
            self.total_engagement
        ) if self.total_engagement else Decimal(0)
        facts = [
            Fact("articles", self.article_count, f"{self.article_count:,}", self.query_id),
            Fact("platformCount", len(self.rows), f"{len(self.rows):,}", self.query_id),
            Fact(
                "totalEngagement",
                self.total_engagement,
                f"{self.total_engagement:,}",
                self.query_id,
            ),
            Fact(
                "volumeLeaders",
                "|".join(row.platform for row in leaders),
                "、".join(row.platform for row in leaders),
                "platforms.volume-leaders.v1",
            ),
            Fact(
                "volumeLeaderCount",
                len(leaders),
                f"{len(leaders):,}",
                "platforms.volume-leaders.v1",
            ),
            Fact(
                "leadingArticleCount",
                leading_count,
                f"{leading_count:,}",
                self.query_id,
            ),
            Fact(
                "leadingArticleShare",
                leading_share,
                f"{leading_share:.1%}",
                "platforms.article-share.v1",
            ),
            Fact(
                "engagementLeader",
                engagement_leader.platform,
                engagement_leader.platform,
                "platforms.engagement-leader.v1",
            ),
            Fact(
                "engagementLeaderTotal",
                engagement_leader.total_engagement,
                f"{engagement_leader.total_engagement:,}",
                self.query_id,
            ),
            Fact(
                "engagementLeaderShare",
                engagement_share,
                f"{engagement_share:.1%}",
                "platforms.engagement-share.v1",
            ),
            Fact(
                "engagementLeaderPerArticle",
                engagement_leader.engagement_per_article,
                f"{engagement_leader.engagement_per_article:,.1f}",
                "platforms.engagement-per-article.v1",
            ),
        ]

        negative_leader = self.negative_leader
        if negative_leader is not None:
            negative_share = Decimal(negative_leader.negative_articles) / Decimal(
                self.negative_articles
            )
            facts.extend(
                (
                    Fact(
                        "negativeLeader",
                        negative_leader.platform,
                        negative_leader.platform,
                        "platforms.negative-leader.v1",
                    ),
                    Fact(
                        "negativeLeaderArticles",
                        negative_leader.negative_articles,
                        f"{negative_leader.negative_articles:,}",
                        self.query_id,
                    ),
                    Fact(
                        "negativeLeaderShare",
                        negative_share,
                        f"{negative_share:.1%}",
                        "platforms.negative-share.v1",
                    ),
                    Fact(
                        "negativeLeaderRatio",
                        negative_leader.negative_ratio,
                        f"{negative_leader.negative_ratio:.1%}",
                        "platforms.negative-ratio.v1",
                    ),
                )
            )

        return FactSet(facts=tuple(facts))
