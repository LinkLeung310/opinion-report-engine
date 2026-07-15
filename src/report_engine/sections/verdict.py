"""Deterministic facts and judgment rules for the executive verdict section."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from report_engine.domain.facts import Fact, FactSet


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Momentum(StrEnum):
    COOLING = "cooling"
    EASING = "easing"
    SUSTAINED = "sustained"


@dataclass(frozen=True)
class VerdictSnapshot:
    article_count: int
    negative_articles: int
    high_risk_negative_articles: int
    critical_negative_articles: int
    peak_day: date | None
    peak_article_count: int
    final_day_article_count: int
    query_id: str

    @property
    def has_data(self) -> bool:
        return self.article_count > 0

    @property
    def negative_ratio(self) -> Decimal | None:
        if not self.has_data:
            return None
        return Decimal(self.negative_articles) / Decimal(self.article_count)

    @property
    def high_risk_negative_ratio(self) -> Decimal | None:
        if self.negative_articles == 0:
            return None
        return Decimal(self.high_risk_negative_articles) / Decimal(
            self.negative_articles
        )

    @property
    def latest_vs_peak_ratio(self) -> Decimal | None:
        if self.peak_article_count == 0:
            return None
        return Decimal(self.final_day_article_count) / Decimal(self.peak_article_count)

    @property
    def risk_level(self) -> RiskLevel | None:
        negative_ratio = self.negative_ratio
        if negative_ratio is None:
            return None
        high_risk_ratio = self.high_risk_negative_ratio or Decimal(0)
        if negative_ratio >= Decimal("0.5") and high_risk_ratio >= Decimal("0.4"):
            return RiskLevel.HIGH
        if negative_ratio >= Decimal("0.3") or self.critical_negative_articles > 0:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    @property
    def momentum(self) -> Momentum | None:
        ratio = self.latest_vs_peak_ratio
        if ratio is None:
            return None
        if ratio < Decimal("0.5"):
            return Momentum.COOLING
        if ratio < Decimal("0.8"):
            return Momentum.EASING
        return Momentum.SUSTAINED

    def to_fact_set(self) -> FactSet:
        if not self.has_data:
            raise ValueError("Cannot create verdict facts for an empty scope")

        negative_ratio = self.negative_ratio
        high_risk_ratio = self.high_risk_negative_ratio
        latest_ratio = self.latest_vs_peak_ratio
        risk_level = self.risk_level
        momentum = self.momentum
        assert negative_ratio is not None
        assert latest_ratio is not None
        assert risk_level is not None
        assert momentum is not None

        peak_day_display = (
            f"{self.peak_day.month}/{self.peak_day.day}" if self.peak_day else "暂无"
        )
        facts = (
            Fact("articles", self.article_count, f"{self.article_count:,}", self.query_id),
            Fact(
                "negativeArticles",
                self.negative_articles,
                f"{self.negative_articles:,}",
                self.query_id,
            ),
            Fact(
                "negativeRatio",
                negative_ratio,
                f"{negative_ratio:.1%}",
                "verdict.negative-ratio.v1",
            ),
            Fact(
                "highRiskNegativeArticles",
                self.high_risk_negative_articles,
                f"{self.high_risk_negative_articles:,}",
                self.query_id,
            ),
            Fact(
                "highRiskNegativeRatio",
                high_risk_ratio,
                f"{high_risk_ratio:.1%}" if high_risk_ratio is not None else "暂无",
                "verdict.high-risk-negative-ratio.v1",
            ),
            Fact(
                "criticalNegativeArticles",
                self.critical_negative_articles,
                f"{self.critical_negative_articles:,}",
                self.query_id,
            ),
            Fact("peakDay", self.peak_day, peak_day_display, self.query_id),
            Fact(
                "peakArticles",
                self.peak_article_count,
                f"{self.peak_article_count:,}",
                self.query_id,
            ),
            Fact(
                "finalDayArticles",
                self.final_day_article_count,
                f"{self.final_day_article_count:,}",
                self.query_id,
            ),
            Fact(
                "latestVsPeakRatio",
                latest_ratio,
                f"{latest_ratio:.1%}",
                "verdict.latest-vs-peak-ratio.v1",
            ),
            Fact(
                "riskLevel",
                risk_level.value,
                risk_level.value,
                "verdict.risk-rule.v1",
            ),
            Fact(
                "momentum",
                momentum.value,
                momentum.value,
                "verdict.momentum-rule.v1",
            ),
        )
        return FactSet(facts=facts)
