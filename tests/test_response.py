from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from report_engine.sections.response import (
    ResponseInputError,
    ResponseObservation,
    ResponseSnapshot,
    ResponseWindow,
    parse_response_date,
)


def observation(
    day: int,
    sentiment: str,
    response_tagged: bool = False,
) -> ResponseObservation:
    return ResponseObservation(
        day=date(2026, 3, day),
        sentiment=sentiment,
        response_tagged=response_tagged,
    )


def fixture_snapshot() -> ResponseSnapshot:
    return ResponseSnapshot(
        window=ResponseWindow.build(
            date(2026, 3, 17),
            date(2026, 3, 23),
            date(2026, 3, 19),
        ),
        observations=(
            observation(17, "negative"),
            observation(17, "neutral"),
            observation(18, "negative"),
            observation(18, "neutral"),
            observation(19, "negative"),
            observation(19, "positive", response_tagged=True),
            observation(20, "negative"),
            observation(20, "negative"),
            observation(20, "neutral"),
            observation(21, "positive"),
            observation(22, "negative"),
            observation(23, "negative"),
        ),
        query_id="response.v1",
    )


def test_balanced_windows_exclude_response_day_and_unmatched_tail() -> None:
    snapshot = fixture_snapshot()

    assert snapshot.window.window_days == 2
    assert (snapshot.pre.start_day, snapshot.pre.end_day) == (
        date(2026, 3, 17),
        date(2026, 3, 18),
    )
    assert (snapshot.post.start_day, snapshot.post.end_day) == (
        date(2026, 3, 20),
        date(2026, 3, 21),
    )
    assert snapshot.article_count == 12
    assert snapshot.comparison_articles == 8
    assert snapshot.response_day_articles == 2
    assert snapshot.response_day_official_tagged_articles == 1
    assert snapshot.outside_matched_windows_articles == 2


def test_facts_keep_exact_volume_sentiment_and_noncausal_deltas() -> None:
    snapshot = fixture_snapshot()
    facts = snapshot.to_fact_set()

    assert snapshot.pre.article_count == snapshot.post.article_count == 4
    assert snapshot.pre.daily_average == snapshot.post.daily_average == Decimal(2)
    assert snapshot.pre.negative_articles == snapshot.post.negative_articles == 2
    assert snapshot.pre.share("negative") == Decimal("0.5")
    assert snapshot.post.share("negative") == Decimal("0.5")
    assert facts.get("preDateRange").formatted_value == "3/17-3/18"
    assert facts.get("postDateRange").formatted_value == "3/20-3/21"
    assert facts.get("articleDelta").formatted_value == "+0"
    assert facts.get("articlePercentChange").formatted_value == "+0.0%"
    assert facts.get("positiveShareDelta").formatted_value == "+25.0 个百分点"
    assert facts.get("neutralShareDelta").formatted_value == "-25.0 个百分点"
    assert facts.get("negativeShareDelta").formatted_value == "+0.0 个百分点"


def test_zero_sample_side_keeps_denominator_facts_unavailable() -> None:
    snapshot = ResponseSnapshot(
        window=ResponseWindow.build(
            date(2026, 3, 17),
            date(2026, 3, 23),
            date(2026, 3, 19),
        ),
        observations=(observation(20, "negative"),),
        query_id="response.v1",
    )
    facts = snapshot.to_fact_set()

    assert snapshot.has_comparison_data is True
    assert snapshot.pre.article_count == 0
    assert snapshot.post.article_count == 1
    assert snapshot.article_percent_change is None
    assert snapshot.share_delta("negative") is None
    assert facts.get("preNegativeShare").raw_value is None
    assert facts.get("preNegativeShare").formatted_value == "不可用"
    assert facts.get("articlePercentChange").formatted_value == "不可用"
    assert facts.get("negativeShareDelta").formatted_value == "不可用"


def test_scoped_records_without_matched_window_records_are_no_comparison_data() -> None:
    snapshot = ResponseSnapshot(
        window=ResponseWindow.build(
            date(2026, 3, 17),
            date(2026, 3, 23),
            date(2026, 3, 19),
        ),
        observations=(
            observation(19, "positive", response_tagged=True),
            observation(23, "negative"),
        ),
        query_id="response.v1",
    )
    facts = snapshot.to_fact_set()

    assert snapshot.has_scoped_data is True
    assert snapshot.has_comparison_data is False
    assert facts.get("responseDayArticles").raw_value == 1
    assert facts.get("outsideMatchedWindowsArticles").raw_value == 1


@pytest.mark.parametrize(
    "value",
    (None, 20260319, "", " 2026-03-19", "2026-3-19", "2026-02-30"),
)
def test_response_date_parser_is_strict_and_actionable(value: object) -> None:
    with pytest.raises(ResponseInputError, match="responseDate"):
        parse_response_date(value)

    assert parse_response_date("2026-03-19") == date(2026, 3, 19)


@pytest.mark.parametrize(
    "response_date",
    (
        date(2026, 3, 16),
        date(2026, 3, 17),
        date(2026, 3, 23),
        date(2026, 3, 24),
    ),
)
def test_response_date_must_leave_a_complete_day_on_each_side(
    response_date: date,
) -> None:
    with pytest.raises(ResponseInputError, match="strictly inside"):
        ResponseWindow.build(
            date(2026, 3, 17),
            date(2026, 3, 23),
            response_date,
        )


def test_window_is_capped_at_seven_days_and_rejects_out_of_scope_rows() -> None:
    window = ResponseWindow.build(
        date(2026, 3, 1),
        date(2026, 3, 31),
        date(2026, 3, 15),
    )

    assert window.window_days == 7
    assert (window.pre_start, window.pre_end) == (
        date(2026, 3, 8),
        date(2026, 3, 14),
    )
    assert (window.post_start, window.post_end) == (
        date(2026, 3, 16),
        date(2026, 3, 22),
    )
    with pytest.raises(ValueError, match="outside the report scope"):
        ResponseSnapshot(
            window=window,
            observations=(
                ResponseObservation(date(2026, 4, 1), "negative", False),
            ),
            query_id="response.v1",
        )
