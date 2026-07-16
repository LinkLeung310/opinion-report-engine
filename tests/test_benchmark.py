from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from report_engine.sections.benchmark import (
    BenchmarkCohort,
    BenchmarkInputError,
    BenchmarkSnapshot,
    parse_comparison_tag,
)


def cohort(label: str, populated: bool = True) -> BenchmarkCohort:
    if label == "current":
        return BenchmarkCohort(
            label,
            "bilibili-dislike",
            date(2026, 3, 17),
            date(2026, 3, 23),
            7,
            12,
            2,
            3,
            7,
            4,
            4,
            26170,
        )
    return BenchmarkCohort(
        label,
        "legacy-feed-controls",
        date(2026, 2, 10) if populated else None,
        date(2026, 2, 16) if populated else None,
        7,
        8 if populated else 0,
        1 if populated else 0,
        2 if populated else 0,
        5 if populated else 0,
        4 if populated else 0,
        3 if populated else 0,
        9500 if populated else 0,
    )


def fixture_snapshot() -> BenchmarkSnapshot:
    return BenchmarkSnapshot(cohort("current"), cohort("comparison"), "benchmark.v1")


@pytest.mark.parametrize("value", (None, 1, "", " ", " padded", "padded "))
def test_comparison_tag_parser_rejects_missing_or_padded_values(value) -> None:
    with pytest.raises(BenchmarkInputError, match="comparisonTag"):
        parse_comparison_tag(value, "bilibili-dislike")

    with pytest.raises(BenchmarkInputError, match="differ"):
        parse_comparison_tag("bilibili-dislike", "bilibili-dislike")
    assert (
        parse_comparison_tag("legacy-feed-controls", "bilibili-dislike")
        == "legacy-feed-controls"
    )


def test_equal_window_facts_preserve_exact_cohort_differences() -> None:
    snapshot = fixture_snapshot()
    facts = snapshot.to_fact_set()

    assert snapshot.has_data is True
    assert snapshot.current.daily_average == Decimal(12) / Decimal(7)
    assert snapshot.comparison.daily_average == Decimal(8) / Decimal(7)
    assert facts.get("currentDateRange").formatted_value == "3/17-3/23"
    assert facts.get("comparisonDateRange").formatted_value == "2/10-2/16"
    assert facts.get("currentNegativeShare").formatted_value == "58.3%"
    assert facts.get("comparisonNegativeShare").formatted_value == "62.5%"
    assert facts.get("articleDelta").formatted_value == "+4"
    assert facts.get("dailyAverageDelta").formatted_value == "+0.6"
    assert facts.get("negativeShareDelta").formatted_value == "-4.2 个百分点"
    assert facts.get("highCriticalShareDelta").formatted_value == "-4.2 个百分点"
    assert facts.get("engagementPerArticleDelta").formatted_value == "+993.3"


def test_empty_comparison_keeps_denominator_values_unavailable() -> None:
    snapshot = BenchmarkSnapshot(
        cohort("current"), cohort("comparison", populated=False), "benchmark.v1"
    )
    facts = snapshot.to_fact_set()

    assert snapshot.has_data is False
    assert facts.get("comparisonNegativeShare").formatted_value == "不可用"
    assert facts.get("comparisonEngagementPerArticle").formatted_value == "不可用"
    assert facts.get("negativeShareDelta").formatted_value == "不可用"
    assert facts.get("engagementPerArticleDelta").formatted_value == "不可用"


def test_cohorts_reject_bad_totals_order_and_unequal_windows() -> None:
    with pytest.raises(ValueError, match="sentiment counts"):
        BenchmarkCohort(
            "comparison", "tag", date(2026, 2, 10), date(2026, 2, 16),
            7, 2, 0, 0, 1, 1, 0, 0,
        )
    with pytest.raises(ValueError, match="fixed order"):
        BenchmarkSnapshot(cohort("comparison"), cohort("current"), "benchmark.v1")
    comparison = cohort("comparison")
    unequal = BenchmarkCohort(
        comparison.cohort, comparison.tag, comparison.start_day,
        date(2026, 2, 17), 8, comparison.article_count,
        comparison.positive_articles, comparison.neutral_articles,
        comparison.negative_articles, comparison.platform_count,
        comparison.high_critical_articles, comparison.total_engagement,
    )
    with pytest.raises(ValueError, match="equal calendar"):
        BenchmarkSnapshot(cohort("current"), unequal, "benchmark.v1")
