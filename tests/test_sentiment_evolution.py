from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from report_engine.sections.sentiment_evolution import (
    DailySentimentPoint,
    SentimentDirection,
    SentimentEvolutionSnapshot,
)


def point(
    offset: int,
    positive: int,
    neutral: int,
    negative: int,
) -> DailySentimentPoint:
    return DailySentimentPoint(
        day=date(2026, 3, 17) + timedelta(days=offset),
        article_count=positive + neutral + negative,
        positive_articles=positive,
        neutral_articles=neutral,
        negative_articles=negative,
    )


def fixture_snapshot() -> SentimentEvolutionSnapshot:
    return SentimentEvolutionSnapshot(
        points=(
            point(0, 0, 1, 1),
            point(1, 0, 1, 1),
            point(2, 1, 0, 1),
            point(3, 0, 1, 2),
            point(4, 1, 0, 0),
            point(5, 0, 0, 1),
            point(6, 0, 0, 1),
        ),
        query_id="sentiment-evolution.v1",
    )


def empty_snapshot() -> SentimentEvolutionSnapshot:
    return SentimentEvolutionSnapshot(
        points=tuple(point(offset, 0, 0, 0) for offset in range(7)),
        query_id="sentiment-evolution.v1",
    )


def test_balanced_phases_preserve_calendar_and_sentiment_totals() -> None:
    phases = fixture_snapshot().phases

    assert [phase.label for phase in phases] == ["前期", "中期", "后期"]
    assert [phase.calendar_days for phase in phases] == [3, 2, 2]
    assert [phase.article_count for phase in phases] == [6, 4, 2]
    assert [
        (
            phase.positive_articles,
            phase.neutral_articles,
            phase.negative_articles,
        )
        for phase in phases
    ] == [(1, 2, 3), (1, 1, 2), (0, 0, 2)]
    assert phases[0].date_range_label == "3/17-3/19"
    assert phases[-1].share("negative") == Decimal(1)


def test_facts_report_sample_sizes_signed_delta_and_direction() -> None:
    snapshot = fixture_snapshot()
    facts = snapshot.to_fact_set()

    assert snapshot.negative_share_delta == Decimal("0.5")
    assert snapshot.direction is SentimentDirection.RISING
    assert facts.get("firstPhaseArticles").formatted_value == "6"
    assert facts.get("firstPhaseNegativeShare").formatted_value == "50.0%"
    assert facts.get("lastPhaseArticles").formatted_value == "2"
    assert facts.get("lastPhaseNegativeShare").formatted_value == "100.0%"
    assert facts.get("negativeShareDelta").formatted_value == "+50.0 个百分点"
    assert facts.get("direction").formatted_value == "负面占比上升"


def test_one_populated_phase_is_complete_but_not_temporally_comparable() -> None:
    snapshot = SentimentEvolutionSnapshot(
        points=(
            point(0, 1, 0, 0),
            point(1, 0, 0, 0),
            point(2, 0, 0, 0),
        ),
        query_id="sentiment-evolution.v1",
    )
    facts = snapshot.to_fact_set()

    assert snapshot.has_data is True
    assert snapshot.direction is SentimentDirection.INSUFFICIENT
    assert facts.get("negativeShareDelta").raw_value is None
    assert facts.get("negativeShareDelta").formatted_value == "不可比较"
    assert facts.get("direction").formatted_value == "仅单阶段有数据"


def test_empty_series_is_valid_no_data_and_keeps_zero_phases() -> None:
    snapshot = empty_snapshot()

    assert snapshot.has_data is False
    assert [phase.article_count for phase in snapshot.phases] == [0, 0, 0]
    with pytest.raises(ValueError, match="empty data"):
        snapshot.to_fact_set()


def test_snapshot_rejects_invalid_daily_counts_or_day_order() -> None:
    with pytest.raises(ValueError, match="must equal"):
        DailySentimentPoint(date(2026, 3, 17), 2, 0, 0, 1)

    with pytest.raises(ValueError, match="unique and chronological"):
        SentimentEvolutionSnapshot(
            points=(point(1, 0, 0, 1), point(0, 0, 0, 1)),
            query_id="sentiment-evolution.v1",
        )
