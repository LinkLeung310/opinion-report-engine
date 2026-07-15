from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from report_engine.sections.trend import DailyTrendPoint, TrendSnapshot


def point(day: int, total: int, positive: int = 0, neutral: int = 0) -> DailyTrendPoint:
    return DailyTrendPoint(
        day=date(2026, 3, day),
        article_count=total,
        positive_articles=positive,
        neutral_articles=neutral,
        negative_articles=total - positive - neutral,
    )


def test_trend_derives_peak_coverage_and_final_change() -> None:
    snapshot = TrendSnapshot(
        points=(point(17, 2), point(18, 3), point(19, 3), point(20, 1)),
        query_id="trend.v1",
    )

    assert snapshot.article_count == 9
    assert snapshot.active_days == 4
    assert snapshot.peak.day == date(2026, 3, 18)
    assert snapshot.peak_share == Decimal(3) / Decimal(9)
    assert snapshot.final_vs_peak_ratio == Decimal(1) / Decimal(3)


def test_trend_keeps_zero_days_and_fact_provenance() -> None:
    snapshot = TrendSnapshot(
        points=(point(17, 2), point(18, 0), point(19, 1)),
        query_id="trend.v1",
    )

    facts = snapshot.to_fact_set()

    assert len(snapshot.points) == 3
    assert snapshot.active_days == 2
    assert facts.get("calendarDays").raw_value == 3
    assert facts.get("peakDay").formatted_value == "3/17"
    assert facts.get("finalVsPeakRatio").formatted_value == "50.0%"
    assert facts.get("activeDays").source_id == "trend.active-days.v1"


def test_all_zero_trend_has_no_peak_or_invented_facts() -> None:
    snapshot = TrendSnapshot(
        points=tuple(point(17 + offset, 0) for offset in range(3)),
        query_id="trend.v1",
    )

    assert snapshot.has_data is False
    assert snapshot.peak is None
    with pytest.raises(ValueError, match="empty series"):
        snapshot.to_fact_set()


def test_trend_rejects_invalid_or_non_chronological_points() -> None:
    with pytest.raises(ValueError, match="sentiment counts"):
        DailyTrendPoint(date(2026, 3, 17), 2, 0, 0, 1)

    later = point(18, 1)
    earlier = point(17, 1)
    with pytest.raises(ValueError, match="chronological"):
        TrendSnapshot(points=(later, earlier), query_id="trend.v1")
