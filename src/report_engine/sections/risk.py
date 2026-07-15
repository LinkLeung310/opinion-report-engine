"""Transparent structured pressure signals for the risk-assessment section."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from report_engine.domain.facts import Fact, FactSet


class RiskBand(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


RISK_BAND_LABELS = {
    RiskBand.LOW: "低",
    RiskBand.MEDIUM: "中",
    RiskBand.HIGH: "高",
}


@dataclass(frozen=True)
class RiskSignal:
    key: str
    label_zh: str
    ratio: Decimal
    band: RiskBand
    source_id: str

    def __post_init__(self) -> None:
        if not self.key or not self.label_zh or not self.source_id:
            raise ValueError("Risk signal identifiers cannot be blank")
        if not Decimal(0) <= self.ratio <= Decimal(1):
            raise ValueError("Risk signal ratios must be between zero and one")


@dataclass(frozen=True)
class RiskSnapshot:
    article_count: int
    negative_articles: int
    high_critical_negative_articles: int
    platform_count: int
    negative_platform_count: int
    calendar_days: int
    negative_active_days: int
    total_engagement: int
    negative_engagement: int
    query_id: str

    low_threshold = Decimal("0.40")
    high_threshold = Decimal("0.70")
    unavailable_dimensions = ("高管关联", "谣言核验")

    def __post_init__(self) -> None:
        values = (
            self.article_count,
            self.negative_articles,
            self.high_critical_negative_articles,
            self.platform_count,
            self.negative_platform_count,
            self.calendar_days,
            self.negative_active_days,
            self.total_engagement,
            self.negative_engagement,
        )
        if min(values) < 0:
            raise ValueError("Risk values cannot be negative")
        if self.calendar_days == 0:
            raise ValueError("Risk calendar range must contain at least one day")
        if self.negative_articles > self.article_count:
            raise ValueError("Negative articles cannot exceed all articles")
        if self.high_critical_negative_articles > self.negative_articles:
            raise ValueError("High/critical negatives cannot exceed negative articles")
        if self.platform_count > self.article_count:
            raise ValueError("Platform count cannot exceed article count")
        if self.negative_platform_count > self.platform_count:
            raise ValueError("Negative platforms cannot exceed all platforms")
        if self.negative_active_days > self.calendar_days:
            raise ValueError("Negative active days cannot exceed calendar days")
        if self.negative_engagement > self.total_engagement:
            raise ValueError("Negative engagement cannot exceed total engagement")
        if self.article_count and self.platform_count == 0:
            raise ValueError("A non-empty scope must contain a platform")
        if self.negative_articles and (
            self.negative_platform_count == 0 or self.negative_active_days == 0
        ):
            raise ValueError("Negative articles require a platform and active day")
        if not self.negative_articles and any(
            (
                self.high_critical_negative_articles,
                self.negative_platform_count,
                self.negative_active_days,
                self.negative_engagement,
            )
        ):
            raise ValueError("Negative-only values require a negative article")
        if not self.query_id.strip():
            raise ValueError("Risk query ID cannot be blank")

    @property
    def has_data(self) -> bool:
        return self.article_count > 0

    @staticmethod
    def _ratio(numerator: int, denominator: int) -> Decimal:
        if denominator == 0:
            return Decimal(0)
        return Decimal(numerator) / Decimal(denominator)

    @classmethod
    def band_for(cls, ratio: Decimal) -> RiskBand:
        if ratio >= cls.high_threshold:
            return RiskBand.HIGH
        if ratio >= cls.low_threshold:
            return RiskBand.MEDIUM
        return RiskBand.LOW

    @property
    def signals(self) -> tuple[RiskSignal, ...]:
        definitions = (
            (
                "sentimentPressure",
                "负面情绪",
                self._ratio(self.negative_articles, self.article_count),
                "risk.sentiment-pressure.v1",
            ),
            (
                "severityPressure",
                "高危程度",
                self._ratio(
                    self.high_critical_negative_articles,
                    self.negative_articles,
                ),
                "risk.severity-pressure.v1",
            ),
            (
                "spreadPressure",
                "平台扩散",
                self._ratio(self.negative_platform_count, self.platform_count),
                "risk.spread-pressure.v1",
            ),
            (
                "persistencePressure",
                "持续覆盖",
                self._ratio(self.negative_active_days, self.calendar_days),
                "risk.persistence-pressure.v1",
            ),
            (
                "amplificationPressure",
                "互动放大",
                self._ratio(self.negative_engagement, self.total_engagement),
                "risk.amplification-pressure.v1",
            ),
        )
        return tuple(
            RiskSignal(key, label, ratio, self.band_for(ratio), source_id)
            for key, label, ratio, source_id in definitions
        )

    @property
    def risk_signal_index(self) -> Decimal:
        ratios = tuple(signal.ratio for signal in self.signals)
        return sum(ratios, Decimal(0)) / Decimal(len(ratios))

    @property
    def risk_level(self) -> RiskBand:
        return self.band_for(self.risk_signal_index)

    def to_fact_set(self) -> FactSet:
        if not self.has_data:
            raise ValueError("Cannot create risk facts for an empty snapshot")

        query_counts = (
            ("articles", self.article_count),
            ("negativeArticles", self.negative_articles),
            (
                "highCriticalNegativeArticles",
                self.high_critical_negative_articles,
            ),
            ("platforms", self.platform_count),
            ("negativePlatforms", self.negative_platform_count),
            ("negativeActiveDays", self.negative_active_days),
            ("totalEngagement", self.total_engagement),
            ("negativeEngagement", self.negative_engagement),
        )
        facts = [
            Fact(key, value, f"{value:,}", self.query_id)
            for key, value in query_counts
        ]
        facts.append(
            Fact(
                "calendarDays",
                self.calendar_days,
                f"{self.calendar_days:,}",
                "risk.scope-calendar-days.v1",
            )
        )

        for signal in self.signals:
            facts.extend(
                (
                    Fact(
                        signal.key,
                        signal.ratio,
                        f"{signal.ratio:.1%}",
                        signal.source_id,
                    ),
                    Fact(
                        f"{signal.key}Band",
                        signal.band.value,
                        RISK_BAND_LABELS[signal.band],
                        "risk.signal-band.v1",
                    ),
                )
            )

        band_counts = {
            band: sum(signal.band is band for signal in self.signals)
            for band in RiskBand
        }
        facts.extend(
            (
                Fact(
                    "riskSignalIndex",
                    self.risk_signal_index,
                    f"{self.risk_signal_index:.1%}",
                    "risk.equal-weight-index.v1",
                ),
                Fact(
                    "riskLevel",
                    self.risk_level.value,
                    RISK_BAND_LABELS[self.risk_level],
                    "risk.signal-band.v1",
                ),
                Fact(
                    "evaluatedSignalCount",
                    len(self.signals),
                    f"{len(self.signals):,}",
                    "risk.equal-weight-index.v1",
                ),
                Fact(
                    "highSignalCount",
                    band_counts[RiskBand.HIGH],
                    f"{band_counts[RiskBand.HIGH]:,}",
                    "risk.signal-band.v1",
                ),
                Fact(
                    "mediumSignalCount",
                    band_counts[RiskBand.MEDIUM],
                    f"{band_counts[RiskBand.MEDIUM]:,}",
                    "risk.signal-band.v1",
                ),
                Fact(
                    "lowSignalCount",
                    band_counts[RiskBand.LOW],
                    f"{band_counts[RiskBand.LOW]:,}",
                    "risk.signal-band.v1",
                ),
                Fact(
                    "diagnosticKind",
                    "non_probability",
                    "非概率诊断指数",
                    "risk.methodology.v1",
                ),
                Fact(
                    "unavailableDimensions",
                    "executiveAssociation|rumorVerification",
                    "、".join(self.unavailable_dimensions),
                    "risk.schema-capability.v1",
                ),
            )
        )
        return FactSet(facts=tuple(facts))
