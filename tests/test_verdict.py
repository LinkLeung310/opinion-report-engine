from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from report_engine.sections.verdict import Momentum, RiskLevel, VerdictSnapshot


def snapshot(**overrides) -> VerdictSnapshot:
    values = {
        "article_count": 12,
        "negative_articles": 7,
        "high_risk_negative_articles": 4,
        "critical_negative_articles": 1,
        "peak_day": date(2026, 3, 20),
        "peak_article_count": 3,
        "final_day_article_count": 1,
        "query_id": "verdict.v1",
    }
    values.update(overrides)
    return VerdictSnapshot(**values)


def test_verdict_rules_use_unrounded_fixture_values() -> None:
    result = snapshot()

    assert result.negative_ratio == Decimal(7) / Decimal(12)
    assert result.high_risk_negative_ratio == Decimal(4) / Decimal(7)
    assert result.latest_vs_peak_ratio == Decimal(1) / Decimal(3)
    assert result.risk_level is RiskLevel.HIGH
    assert result.momentum is Momentum.COOLING


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        (
            {
                "negative_articles": 4,
                "high_risk_negative_articles": 1,
                "critical_negative_articles": 0,
            },
            RiskLevel.MEDIUM,
        ),
        (
            {
                "negative_articles": 2,
                "high_risk_negative_articles": 0,
                "critical_negative_articles": 0,
            },
            RiskLevel.LOW,
        ),
    ],
)
def test_verdict_risk_thresholds_are_deterministic(overrides, expected) -> None:
    assert snapshot(**overrides).risk_level is expected


@pytest.mark.parametrize(
    ("final_day_articles", "expected"),
    [(1, Momentum.COOLING), (2, Momentum.EASING), (3, Momentum.SUSTAINED)],
)
def test_verdict_momentum_thresholds_are_deterministic(
    final_day_articles: int,
    expected: Momentum,
) -> None:
    assert snapshot(final_day_article_count=final_day_articles).momentum is expected


def test_verdict_fact_set_keeps_query_and_rule_provenance() -> None:
    facts = snapshot().to_fact_set()

    assert facts.get("articles").source_id == "verdict.v1"
    assert facts.get("negativeRatio").formatted_value == "58.3%"
    assert facts.get("highRiskNegativeRatio").formatted_value == "57.1%"
    assert facts.get("latestVsPeakRatio").formatted_value == "33.3%"
    assert facts.get("riskLevel").source_id == "verdict.risk-rule.v1"
    assert facts.get("momentum").raw_value == "cooling"


def test_empty_verdict_has_no_judgment_or_invented_fact_set() -> None:
    empty = snapshot(
        article_count=0,
        negative_articles=0,
        high_risk_negative_articles=0,
        critical_negative_articles=0,
        peak_day=None,
        peak_article_count=0,
        final_day_article_count=0,
    )

    assert empty.has_data is False
    assert empty.risk_level is None
    assert empty.momentum is None
    with pytest.raises(ValueError, match="empty scope"):
        empty.to_fact_set()


def test_non_negative_scope_does_not_invent_a_zero_percent_denominator() -> None:
    facts = snapshot(
        negative_articles=0,
        high_risk_negative_articles=0,
        critical_negative_articles=0,
    ).to_fact_set()

    assert facts.get("highRiskNegativeRatio").raw_value is None
    assert facts.get("highRiskNegativeRatio").formatted_value == "暂无"
    assert facts.get("riskLevel").raw_value == "low"
