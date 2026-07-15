from __future__ import annotations

from datetime import date
from decimal import Decimal

from report_engine.sections.metrics import MetricsSnapshot


def test_metrics_derived_values_are_computed_deterministically() -> None:
    snapshot = MetricsSnapshot(
        article_count=12,
        positive_articles=2,
        neutral_articles=3,
        negative_articles=7,
        platform_count=4,
        likes=15_460,
        comments=4_705,
        shares=4_620,
        favorites=1_385,
        peak_day=date(2026, 3, 20),
        peak_article_count=3,
        query_id="metrics.v1",
    )

    assert snapshot.total_engagement == 26_170
    assert snapshot.negative_ratio == Decimal(7) / Decimal(12)
    assert snapshot.has_data is True


def test_empty_metrics_do_not_invent_a_zero_percent_finding() -> None:
    snapshot = MetricsSnapshot(
        article_count=0,
        positive_articles=0,
        neutral_articles=0,
        negative_articles=0,
        platform_count=0,
        likes=0,
        comments=0,
        shares=0,
        favorites=0,
        peak_day=None,
        peak_article_count=0,
        query_id="metrics.v1",
    )

    assert snapshot.negative_ratio is None
    assert snapshot.has_data is False
