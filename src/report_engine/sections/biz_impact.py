"""Auditable public-opinion signals for bounded business-impact analysis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from report_engine.domain.facts import Fact, FactSet
from report_engine.domain.user_context import UserContext


BIZ_IMPACT_NOTES_SOURCE_ID = (
    "report-config.sections[biz-impact].input.notes"
)
MAX_BIZ_IMPACT_NOTES_LENGTH = 1_000
SENTIMENTS = ("positive", "neutral", "negative")


class BizImpactInputError(ValueError):
    """A safe, actionable error for invalid business-impact input."""


def parse_biz_impact_notes(value: object) -> UserContext:
    """Normalize bounded prose without treating its contents as instructions."""

    if not isinstance(value, str):
        raise BizImpactInputError("notes must be a string")
    for character in value:
        codepoint = ord(character)
        is_c0_or_c1 = codepoint < 32 or 127 <= codepoint <= 159
        if character == "\x00" or (is_c0_or_c1 and not character.isspace()):
            raise BizImpactInputError("notes must not contain control characters")

    normalized = " ".join(value.split())
    if not normalized:
        raise BizImpactInputError("notes must not be blank")
    if len(normalized) > MAX_BIZ_IMPACT_NOTES_LENGTH:
        raise BizImpactInputError(
            f"notes must contain at most {MAX_BIZ_IMPACT_NOTES_LENGTH} characters"
        )
    return UserContext(
        key="notes",
        text=normalized,
        source_id=BIZ_IMPACT_NOTES_SOURCE_ID,
    )


@dataclass(frozen=True)
class BizImpactSnapshot:
    start_day: date
    end_day: date
    article_count: int
    positive_articles: int
    neutral_articles: int
    negative_articles: int
    platform_count: int
    active_days: int
    peak_day: date | None
    peak_article_count: int
    high_critical_negative_articles: int
    likes: int
    comments: int
    shares: int
    favorites: int
    query_id: str

    def __post_init__(self) -> None:
        counts = (
            self.article_count,
            self.positive_articles,
            self.neutral_articles,
            self.negative_articles,
            self.platform_count,
            self.active_days,
            self.peak_article_count,
            self.high_critical_negative_articles,
            self.likes,
            self.comments,
            self.shares,
            self.favorites,
        )
        if self.start_day > self.end_day or min(counts) < 0:
            raise ValueError("Business-impact snapshot values must be valid")
        if sum(counts[1:4]) != self.article_count:
            raise ValueError("Business-impact sentiment counts must equal articles")
        if self.high_critical_negative_articles > self.negative_articles:
            raise ValueError("High/critical articles must be a negative subset")
        if self.platform_count > self.article_count:
            raise ValueError("Business-impact platform count cannot exceed articles")
        if self.active_days > self.calendar_days:
            raise ValueError("Business-impact active days cannot exceed calendar days")
        if self.peak_article_count > self.article_count:
            raise ValueError("Business-impact peak cannot exceed all articles")
        if self.peak_day is not None and not self.start_day <= self.peak_day <= self.end_day:
            raise ValueError("Business-impact peak day must be inside the scope")
        if not self.query_id.strip():
            raise ValueError("Business-impact query ID cannot be blank")

        if self.article_count:
            if not self.platform_count or not self.active_days:
                raise ValueError("Non-empty business-impact data needs coverage")
            if self.peak_day is None or not self.peak_article_count:
                raise ValueError("Non-empty business-impact data needs a peak")
        elif any(counts[4:]) or self.peak_day is not None:
            raise ValueError("Empty business-impact data must keep zero observations")

    @property
    def calendar_days(self) -> int:
        return (self.end_day - self.start_day).days + 1

    @property
    def has_data(self) -> bool:
        return self.article_count > 0

    @staticmethod
    def _ratio(numerator: int, denominator: int) -> Decimal | None:
        if not denominator:
            return None
        return Decimal(numerator) / Decimal(denominator)

    def sentiment_share(self, sentiment: str) -> Decimal | None:
        if sentiment not in SENTIMENTS:
            raise ValueError("Unsupported business-impact sentiment")
        return self._ratio(
            getattr(self, f"{sentiment}_articles"),
            self.article_count,
        )

    @property
    def active_day_coverage(self) -> Decimal:
        return Decimal(self.active_days) / Decimal(self.calendar_days)

    @property
    def peak_share(self) -> Decimal | None:
        return self._ratio(self.peak_article_count, self.article_count)

    @property
    def high_critical_negative_share(self) -> Decimal | None:
        return self._ratio(
            self.high_critical_negative_articles,
            self.negative_articles,
        )

    @property
    def high_critical_all_share(self) -> Decimal | None:
        return self._ratio(
            self.high_critical_negative_articles,
            self.article_count,
        )

    @property
    def total_stored_interaction(self) -> int:
        return self.likes + self.comments + self.shares + self.favorites

    @property
    def stored_interaction_per_article(self) -> Decimal | None:
        if not self.article_count:
            return None
        return Decimal(self.total_stored_interaction) / Decimal(self.article_count)

    @property
    def comments_and_shares(self) -> int:
        return self.comments + self.shares

    @staticmethod
    def _percentage(value: Decimal | None) -> str:
        return "不可用" if value is None else f"{value:.1%}"

    def to_fact_set(self) -> FactSet:
        query_source = self.query_id
        scope_source = "biz-impact.scope.v1"
        sentiment_source = "biz-impact.sentiment-shares.v1"
        pressure_source = "biz-impact.pressure.v1"
        interaction_source = "biz-impact.interaction-snapshot.v1"
        methodology_source = "biz-impact.methodology.v1"

        peak_day_display = (
            f"{self.peak_day.month}/{self.peak_day.day}"
            if self.peak_day is not None
            else "不可用"
        )
        facts = [
            Fact("articles", self.article_count, f"{self.article_count:,}", query_source),
            Fact(
                "platforms",
                self.platform_count,
                f"{self.platform_count:,}",
                query_source,
            ),
            Fact(
                "dateRange",
                f"{self.start_day.isoformat()}/{self.end_day.isoformat()}",
                f"{self.start_day.isoformat()} 至 {self.end_day.isoformat()}",
                scope_source,
            ),
            Fact(
                "calendarDays",
                self.calendar_days,
                f"{self.calendar_days:,}",
                scope_source,
            ),
            Fact("activeDays", self.active_days, f"{self.active_days:,}", query_source),
            Fact(
                "activeDayCoverage",
                self.active_day_coverage,
                f"{self.active_day_coverage:.1%}",
                "biz-impact.coverage.v1",
            ),
            Fact("peakDay", self.peak_day, peak_day_display, query_source),
            Fact(
                "peakArticles",
                self.peak_article_count,
                f"{self.peak_article_count:,}",
                query_source,
            ),
            Fact(
                "peakShare",
                self.peak_share,
                self._percentage(self.peak_share),
                pressure_source,
            ),
            Fact(
                "highCriticalNegativeArticles",
                self.high_critical_negative_articles,
                f"{self.high_critical_negative_articles:,}",
                query_source,
            ),
            Fact(
                "highCriticalNegativeShare",
                self.high_critical_negative_share,
                self._percentage(self.high_critical_negative_share),
                pressure_source,
            ),
            Fact(
                "highCriticalAllShare",
                self.high_critical_all_share,
                self._percentage(self.high_critical_all_share),
                pressure_source,
            ),
        ]
        for sentiment in SENTIMENTS:
            count = getattr(self, f"{sentiment}_articles")
            share = self.sentiment_share(sentiment)
            facts.extend(
                (
                    Fact(
                        f"{sentiment}Articles",
                        count,
                        f"{count:,}",
                        query_source,
                    ),
                    Fact(
                        f"{sentiment}Share",
                        share,
                        self._percentage(share),
                        sentiment_source,
                    ),
                )
            )

        interactions = (
            ("likes", self.likes),
            ("comments", self.comments),
            ("shares", self.shares),
            ("favorites", self.favorites),
            ("totalStoredInteraction", self.total_stored_interaction),
            ("commentsAndShares", self.comments_and_shares),
        )
        facts.extend(
            Fact(key, value, f"{value:,}", interaction_source)
            for key, value in interactions
        )
        interaction_average = self.stored_interaction_per_article
        facts.extend(
            (
                Fact(
                    "storedInteractionPerArticle",
                    interaction_average,
                    "不可用"
                    if interaction_average is None
                    else f"{interaction_average:,.1f}",
                    interaction_source,
                ),
                Fact(
                    "reputationPressureLens",
                    "descriptive",
                    "舆情声誉压力",
                    methodology_source,
                ),
                Fact(
                    "responseComplexityLens",
                    "descriptive",
                    "公开讨论应对复杂度",
                    methodology_source,
                ),
                Fact(
                    "businessOutcomeVerificationStatus",
                    "unavailable",
                    "缺少已验证业务结果序列",
                    "biz-impact.schema-capability.v1",
                ),
                Fact(
                    "causalClaimStatus",
                    "not_established",
                    "未建立因果关系",
                    methodology_source,
                ),
            )
        )
        return FactSet(tuple(facts))
