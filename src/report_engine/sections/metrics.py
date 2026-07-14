"""Deterministic results for the all-network metrics section."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


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
