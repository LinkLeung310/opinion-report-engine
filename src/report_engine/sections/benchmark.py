"""Auditable equal-window facts for an independent historical benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from report_engine.domain.facts import Fact, FactSet


SENTIMENTS = ("positive", "neutral", "negative")


class BenchmarkInputError(ValueError):
    """A safe error for invalid benchmark input."""


def parse_comparison_tag(value: object, topic_tag: str) -> str:
    if not isinstance(value, str) or not value:
        raise BenchmarkInputError("comparisonTag must be a non-blank string")
    if value != value.strip():
        raise BenchmarkInputError("comparisonTag must not have surrounding whitespace")
    if value == topic_tag:
        raise BenchmarkInputError("comparisonTag must differ from topic.tag")
    return value


@dataclass(frozen=True)
class BenchmarkCohort:
    cohort: str
    tag: str
    start_day: date | None
    end_day: date | None
    calendar_days: int
    article_count: int
    positive_articles: int
    neutral_articles: int
    negative_articles: int
    platform_count: int
    high_critical_articles: int
    total_engagement: int
    excluded_later_articles: int = 0

    def __post_init__(self) -> None:
        counts = (
            self.calendar_days,
            self.article_count,
            self.positive_articles,
            self.neutral_articles,
            self.negative_articles,
            self.platform_count,
            self.high_critical_articles,
            self.total_engagement,
            self.excluded_later_articles,
        )
        if self.cohort not in {"current", "comparison"} or not self.tag or min(counts) < 0:
            raise ValueError("Benchmark cohort fields must be valid")
        if sum(counts[2:5]) != self.article_count:
            raise ValueError("Benchmark sentiment counts must equal article count")
        if self.high_critical_articles > self.negative_articles:
            raise ValueError("High/critical count must be a negative subset")
        if (self.start_day is None) != (self.end_day is None):
            raise ValueError("Benchmark dates must be both present or both absent")
        if self.start_day is not None:
            if self.start_day > self.end_day:
                raise ValueError("Benchmark date range must be chronological")
            if (self.end_day - self.start_day).days + 1 != self.calendar_days:
                raise ValueError("Benchmark date range must match calendar days")
        elif self.article_count:
            raise ValueError("Populated benchmark cohort requires dates")

    @property
    def date_range_label(self) -> str:
        if self.start_day is None or self.end_day is None:
            return "不可用"
        return (
            f"{self.start_day.month}/{self.start_day.day}-"
            f"{self.end_day.month}/{self.end_day.day}"
        )

    @property
    def daily_average(self) -> Decimal:
        return Decimal(self.article_count) / Decimal(self.calendar_days)

    def share(self, sentiment: str) -> Decimal | None:
        if sentiment not in SENTIMENTS:
            raise ValueError("Unsupported benchmark sentiment")
        if not self.article_count:
            return None
        return Decimal(getattr(self, f"{sentiment}_articles")) / Decimal(self.article_count)

    @property
    def high_critical_share(self) -> Decimal | None:
        if not self.article_count:
            return None
        return Decimal(self.high_critical_articles) / Decimal(self.article_count)

    @property
    def engagement_per_article(self) -> Decimal | None:
        if not self.article_count:
            return None
        return Decimal(self.total_engagement) / Decimal(self.article_count)


@dataclass(frozen=True)
class BenchmarkSnapshot:
    current: BenchmarkCohort
    comparison: BenchmarkCohort
    query_id: str

    def __post_init__(self) -> None:
        if self.current.cohort != "current" or self.comparison.cohort != "comparison":
            raise ValueError("Benchmark cohorts must use fixed order")
        if self.current.tag == self.comparison.tag:
            raise ValueError("Benchmark cohorts must use distinct tags")
        if self.current.calendar_days != self.comparison.calendar_days:
            raise ValueError("Benchmark cohorts must use equal calendar days")
        if not self.query_id.strip():
            raise ValueError("Benchmark query ID cannot be blank")

    @property
    def has_data(self) -> bool:
        return self.current.article_count > 0 and self.comparison.article_count > 0

    def _delta(self, attribute: str) -> Decimal | None:
        current = getattr(self.current, attribute)
        comparison = getattr(self.comparison, attribute)
        if current is None or comparison is None:
            return None
        return current - comparison

    def to_fact_set(self) -> FactSet:
        facts: list[Fact] = []
        for prefix, cohort in (("current", self.current), ("comparison", self.comparison)):
            rate_source = "benchmark.rates.v1"
            high_share = cohort.high_critical_share
            engagement_average = cohort.engagement_per_article
            values = {
                "Tag": (cohort.tag, cohort.tag, self.query_id),
                "DateRange": (
                    None if cohort.start_day is None else f"{cohort.start_day}/{cohort.end_day}",
                    cohort.date_range_label,
                    self.query_id,
                ),
                "CalendarDays": (
                    cohort.calendar_days,
                    f"{cohort.calendar_days:,}",
                    self.query_id,
                ),
                "Articles": (
                    cohort.article_count,
                    f"{cohort.article_count:,}",
                    self.query_id,
                ),
                "DailyAverage": (
                    cohort.daily_average,
                    f"{cohort.daily_average:.1f}",
                    rate_source,
                ),
                "Platforms": (
                    cohort.platform_count,
                    f"{cohort.platform_count:,}",
                    self.query_id,
                ),
                "HighCriticalArticles": (
                    cohort.high_critical_articles,
                    f"{cohort.high_critical_articles:,}",
                    self.query_id,
                ),
                "HighCriticalShare": (
                    high_share,
                    "不可用" if high_share is None else f"{high_share:.1%}",
                    rate_source,
                ),
                "TotalEngagement": (
                    cohort.total_engagement,
                    f"{cohort.total_engagement:,}",
                    self.query_id,
                ),
                "EngagementPerArticle": (
                    engagement_average,
                    "不可用"
                    if engagement_average is None
                    else f"{engagement_average:,.1f}",
                    rate_source,
                ),
                "ExcludedLaterArticles": (
                    cohort.excluded_later_articles,
                    f"{cohort.excluded_later_articles:,}",
                    self.query_id,
                ),
            }
            for sentiment in SENTIMENTS:
                count = getattr(cohort, f"{sentiment}_articles")
                share = cohort.share(sentiment)
                values[f"{sentiment.title()}Articles"] = (
                    count,
                    f"{count:,}",
                    self.query_id,
                )
                values[f"{sentiment.title()}Share"] = (
                    share,
                    "不可用" if share is None else f"{share:.1%}",
                    rate_source,
                )
            facts.extend(
                Fact(f"{prefix}{key}", raw, formatted, source)
                for key, (raw, formatted, source) in values.items()
            )

        current_negative = self.current.share("negative")
        comparison_negative = self.comparison.share("negative")
        negative_delta = (
            current_negative - comparison_negative
            if current_negative is not None and comparison_negative is not None
            else None
        )
        deltas = {
            "articleDelta": (
                Decimal(self.current.article_count - self.comparison.article_count),
                "+,.0f",
            ),
            "dailyAverageDelta": (
                self.current.daily_average - self.comparison.daily_average,
                "+.1f",
            ),
            "negativeShareDelta": (negative_delta, None),
            "highCriticalShareDelta": (self._delta("high_critical_share"), None),
            "engagementPerArticleDelta": (self._delta("engagement_per_article"), "+,.1f"),
        }
        for key, (raw, pattern) in deltas.items():
            if raw is None:
                formatted = "不可用"
            elif key.endswith("ShareDelta"):
                formatted = f"{raw * 100:+.1f} 个百分点"
            else:
                formatted = format(raw, pattern)
            facts.append(Fact(key, raw, formatted, "benchmark.comparison.v1"))
        return FactSet(tuple(facts))
