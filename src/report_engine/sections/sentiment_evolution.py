"""Calendar-complete sentiment phases and auditable composition facts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from report_engine.domain.facts import Fact, FactSet


DIRECTION_THRESHOLD = Decimal("0.10")


class SentimentDirection(str, Enum):
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    INSUFFICIENT = "insufficient"


DIRECTION_LABELS = {
    SentimentDirection.RISING: "负面占比上升",
    SentimentDirection.FALLING: "负面占比下降",
    SentimentDirection.STABLE: "基本稳定",
    SentimentDirection.INSUFFICIENT: "仅单阶段有数据",
}


@dataclass(frozen=True)
class DailySentimentPoint:
    day: date
    article_count: int
    positive_articles: int
    neutral_articles: int
    negative_articles: int

    def __post_init__(self) -> None:
        counts = (
            self.article_count,
            self.positive_articles,
            self.neutral_articles,
            self.negative_articles,
        )
        if min(counts) < 0:
            raise ValueError("Daily sentiment counts cannot be negative")
        if sum(counts[1:]) != self.article_count:
            raise ValueError("Daily sentiment total must equal sentiment counts")


@dataclass(frozen=True)
class SentimentPhase:
    label: str
    start_day: date
    end_day: date
    calendar_days: int
    article_count: int
    positive_articles: int
    neutral_articles: int
    negative_articles: int

    def __post_init__(self) -> None:
        counts = (
            self.calendar_days,
            self.article_count,
            self.positive_articles,
            self.neutral_articles,
            self.negative_articles,
        )
        if self.calendar_days <= 0 or min(counts[1:]) < 0:
            raise ValueError("Sentiment phase values must be valid and non-negative")
        if self.start_day > self.end_day:
            raise ValueError("Sentiment phase dates must be chronological")
        if sum(counts[2:]) != self.article_count:
            raise ValueError("Phase total must equal sentiment counts")

    @property
    def date_range_label(self) -> str:
        start = f"{self.start_day.month}/{self.start_day.day}"
        end = f"{self.end_day.month}/{self.end_day.day}"
        return start if self.start_day == self.end_day else f"{start}–{end}"

    def share(self, sentiment: str) -> Decimal:
        counts = {
            "positive": self.positive_articles,
            "neutral": self.neutral_articles,
            "negative": self.negative_articles,
        }
        if sentiment not in counts:
            raise ValueError("Unsupported phase sentiment")
        if not self.article_count:
            return Decimal(0)
        return Decimal(counts[sentiment]) / Decimal(self.article_count)


@dataclass(frozen=True)
class SentimentEvolutionSnapshot:
    points: tuple[DailySentimentPoint, ...]
    query_id: str

    def __post_init__(self) -> None:
        if not self.points:
            raise ValueError(
                "Sentiment evolution snapshot requires a complete calendar series"
            )
        days = tuple(point.day for point in self.points)
        if days != tuple(sorted(days)) or len(days) != len(set(days)):
            raise ValueError("Sentiment evolution days must be unique and chronological")
        if not self.query_id.strip():
            raise ValueError("Sentiment evolution query ID cannot be blank")

    @property
    def article_count(self) -> int:
        return sum(point.article_count for point in self.points)

    @property
    def has_data(self) -> bool:
        return self.article_count > 0

    @property
    def phases(self) -> tuple[SentimentPhase, ...]:
        phase_count = min(3, len(self.points))
        base_size, remainder = divmod(len(self.points), phase_count)
        sizes = tuple(
            base_size + (1 if index < remainder else 0)
            for index in range(phase_count)
        )
        labels = {
            1: ("全期",),
            2: ("前期", "后期"),
            3: ("前期", "中期", "后期"),
        }[phase_count]

        phases: list[SentimentPhase] = []
        offset = 0
        for label, size in zip(labels, sizes, strict=True):
            points = self.points[offset : offset + size]
            phases.append(
                SentimentPhase(
                    label=label,
                    start_day=points[0].day,
                    end_day=points[-1].day,
                    calendar_days=size,
                    article_count=sum(point.article_count for point in points),
                    positive_articles=sum(
                        point.positive_articles for point in points
                    ),
                    neutral_articles=sum(point.neutral_articles for point in points),
                    negative_articles=sum(
                        point.negative_articles for point in points
                    ),
                )
            )
            offset += size
        return tuple(phases)

    @property
    def populated_phases(self) -> tuple[SentimentPhase, ...]:
        return tuple(phase for phase in self.phases if phase.article_count > 0)

    @property
    def negative_share_delta(self) -> Decimal | None:
        populated = self.populated_phases
        if len(populated) < 2:
            return None
        return populated[-1].share("negative") - populated[0].share("negative")

    @property
    def direction(self) -> SentimentDirection:
        delta = self.negative_share_delta
        if delta is None:
            return SentimentDirection.INSUFFICIENT
        if delta >= DIRECTION_THRESHOLD:
            return SentimentDirection.RISING
        if delta <= -DIRECTION_THRESHOLD:
            return SentimentDirection.FALLING
        return SentimentDirection.STABLE

    def to_fact_set(self) -> FactSet:
        if not self.has_data:
            raise ValueError("Cannot create sentiment evolution facts for empty data")

        populated = self.populated_phases
        first = populated[0]
        last = populated[-1]
        delta = self.negative_share_delta
        delta_display = (
            f"{delta * 100:+.1f} 个百分点" if delta is not None else "不可比较"
        )
        facts = [
            Fact("articles", self.article_count, f"{self.article_count:,}", self.query_id),
            Fact("calendarDays", len(self.points), f"{len(self.points):,}", self.query_id),
            Fact("phaseCount", len(self.phases), f"{len(self.phases):,}", "sentiment-evolution.phases.v1"),
            Fact(
                "populatedPhaseCount",
                len(populated),
                f"{len(populated):,}",
                "sentiment-evolution.phases.v1",
            ),
        ]
        for index, phase in enumerate(self.phases, start=1):
            prefix = f"phase{index}"
            phase_source = "sentiment-evolution.phases.v1"
            facts.extend(
                (
                    Fact(f"{prefix}Label", phase.label, phase.label, phase_source),
                    Fact(
                        f"{prefix}DateRange",
                        f"{phase.start_day.isoformat()}/{phase.end_day.isoformat()}",
                        phase.date_range_label,
                        phase_source,
                    ),
                    Fact(
                        f"{prefix}Articles",
                        phase.article_count,
                        f"{phase.article_count:,}",
                        self.query_id,
                    ),
                    Fact(
                        f"{prefix}PositiveArticles",
                        phase.positive_articles,
                        f"{phase.positive_articles:,}",
                        self.query_id,
                    ),
                    Fact(
                        f"{prefix}NeutralArticles",
                        phase.neutral_articles,
                        f"{phase.neutral_articles:,}",
                        self.query_id,
                    ),
                    Fact(
                        f"{prefix}NegativeArticles",
                        phase.negative_articles,
                        f"{phase.negative_articles:,}",
                        self.query_id,
                    ),
                )
            )
            for sentiment in ("positive", "neutral", "negative"):
                share = phase.share(sentiment)
                facts.append(
                    Fact(
                        f"{prefix}{sentiment.title()}Share",
                        share,
                        f"{share:.1%}",
                        "sentiment-evolution.phase-shares.v1",
                    )
                )
        facts.extend(
            (
                Fact("firstPhaseLabel", first.label, first.label, "sentiment-evolution.comparison.v1"),
                Fact("firstPhaseDateRange", f"{first.start_day.isoformat()}/{first.end_day.isoformat()}", first.date_range_label, "sentiment-evolution.comparison.v1"),
                Fact("firstPhaseArticles", first.article_count, f"{first.article_count:,}", self.query_id),
                Fact("firstPhaseNegativeShare", first.share("negative"), f"{first.share('negative'):.1%}", "sentiment-evolution.comparison.v1"),
                Fact("lastPhaseLabel", last.label, last.label, "sentiment-evolution.comparison.v1"),
                Fact("lastPhaseDateRange", f"{last.start_day.isoformat()}/{last.end_day.isoformat()}", last.date_range_label, "sentiment-evolution.comparison.v1"),
                Fact("lastPhaseArticles", last.article_count, f"{last.article_count:,}", self.query_id),
                Fact("lastPhaseNegativeShare", last.share("negative"), f"{last.share('negative'):.1%}", "sentiment-evolution.comparison.v1"),
                Fact("negativeShareDelta", delta, delta_display, "sentiment-evolution.comparison.v1"),
                Fact("direction", self.direction.value, DIRECTION_LABELS[self.direction], "sentiment-evolution.direction.v1"),
            )
        )
        return FactSet(facts=tuple(facts))
