"""Deterministic daily series and facts for the heat-trend section."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from report_engine.domain.facts import Fact, FactSet


@dataclass(frozen=True)
class DailyTrendPoint:
    day: date
    article_count: int
    positive_articles: int
    neutral_articles: int
    negative_articles: int

    def __post_init__(self) -> None:
        sentiment_total = (
            self.positive_articles + self.neutral_articles + self.negative_articles
        )
        if self.article_count != sentiment_total:
            raise ValueError("Daily trend total must equal its sentiment counts")
        if min(
            self.article_count,
            self.positive_articles,
            self.neutral_articles,
            self.negative_articles,
        ) < 0:
            raise ValueError("Daily trend counts cannot be negative")


@dataclass(frozen=True)
class TrendSnapshot:
    points: tuple[DailyTrendPoint, ...]
    query_id: str

    def __post_init__(self) -> None:
        if not self.points:
            raise ValueError("Trend snapshot requires a complete calendar series")
        days = tuple(point.day for point in self.points)
        if days != tuple(sorted(days)) or len(days) != len(set(days)):
            raise ValueError("Trend days must be unique and chronological")

    @property
    def article_count(self) -> int:
        return sum(point.article_count for point in self.points)

    @property
    def has_data(self) -> bool:
        return self.article_count > 0

    @property
    def active_days(self) -> int:
        return sum(point.article_count > 0 for point in self.points)

    @property
    def peak(self) -> DailyTrendPoint | None:
        if not self.has_data:
            return None
        peak_count = max(point.article_count for point in self.points)
        return next(point for point in self.points if point.article_count == peak_count)

    @property
    def peak_share(self) -> Decimal | None:
        peak = self.peak
        if peak is None:
            return None
        return Decimal(peak.article_count) / Decimal(self.article_count)

    @property
    def final_vs_peak_ratio(self) -> Decimal | None:
        peak = self.peak
        if peak is None:
            return None
        return Decimal(self.points[-1].article_count) / Decimal(peak.article_count)

    def to_fact_set(self) -> FactSet:
        peak = self.peak
        peak_share = self.peak_share
        final_ratio = self.final_vs_peak_ratio
        if peak is None or peak_share is None or final_ratio is None:
            raise ValueError("Cannot create trend facts for an empty series")

        final = self.points[-1]
        return FactSet(
            facts=(
                Fact("articles", self.article_count, f"{self.article_count:,}", self.query_id),
                Fact("calendarDays", len(self.points), f"{len(self.points):,}", self.query_id),
                Fact("activeDays", self.active_days, f"{self.active_days:,}", "trend.active-days.v1"),
                Fact("peakDay", peak.day, f"{peak.day.month}/{peak.day.day}", self.query_id),
                Fact("peakArticles", peak.article_count, f"{peak.article_count:,}", self.query_id),
                Fact("peakShare", peak_share, f"{peak_share:.1%}", "trend.peak-share.v1"),
                Fact("finalDay", final.day, f"{final.day.month}/{final.day.day}", self.query_id),
                Fact("finalDayArticles", final.article_count, f"{final.article_count:,}", self.query_id),
                Fact("finalVsPeakRatio", final_ratio, f"{final_ratio:.1%}", "trend.final-vs-peak.v1"),
            )
        )
