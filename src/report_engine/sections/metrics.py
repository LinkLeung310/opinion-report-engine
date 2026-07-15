"""Deterministic results for the all-network metrics section."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from report_engine.domain.facts import Fact, FactSet


@dataclass(frozen=True)
class MetricsSnapshot:
    article_count: int
    positive_articles: int
    neutral_articles: int
    negative_articles: int
    platform_count: int
    likes: int
    comments: int
    shares: int
    favorites: int
    peak_day: date | None
    peak_article_count: int
    query_id: str

    @property
    def total_engagement(self) -> int:
        return self.likes + self.comments + self.shares + self.favorites

    @property
    def negative_ratio(self) -> Decimal | None:
        if self.article_count == 0:
            return None
        return Decimal(self.negative_articles) / Decimal(self.article_count)

    @property
    def has_data(self) -> bool:
        return self.article_count > 0

    def to_fact_set(self) -> FactSet:
        """Create the single source of numeric truth for this section."""

        negative_ratio = self.negative_ratio
        peak_day_display = (
            f"{self.peak_day.month}/{self.peak_day.day}" if self.peak_day else "暂无"
        )
        values = (
            ("articles", self.article_count, f"{self.article_count:,}"),
            ("positiveArticles", self.positive_articles, f"{self.positive_articles:,}"),
            ("neutralArticles", self.neutral_articles, f"{self.neutral_articles:,}"),
            ("negativeArticles", self.negative_articles, f"{self.negative_articles:,}"),
            (
                "negativeRatio",
                negative_ratio,
                f"{negative_ratio:.1%}" if negative_ratio is not None else "暂无",
            ),
            ("platforms", self.platform_count, f"{self.platform_count:,}"),
            ("engagement", self.total_engagement, f"{self.total_engagement:,}"),
            ("peakDay", self.peak_day, peak_day_display),
            ("peakArticles", self.peak_article_count, f"{self.peak_article_count:,}"),
        )
        return FactSet(
            facts=tuple(
                Fact(
                    key=key,
                    raw_value=raw_value,
                    formatted_value=formatted_value,
                    source_id=self.query_id,
                )
                for key, raw_value, formatted_value in values
            )
        )
