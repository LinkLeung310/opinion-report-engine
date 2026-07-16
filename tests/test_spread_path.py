from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from report_engine.sections.spread_path import SpreadPathSnapshot, SpreadPathSourceRecord


TIMEZONE = ZoneInfo("Asia/Shanghai")


def record(
    external_id: str,
    platform: str,
    day: int,
    hour: int,
    *,
    sentiment: str = "neutral",
    engagement: int = 100,
) -> SpreadPathSourceRecord:
    return SpreadPathSourceRecord(
        external_id=external_id,
        title=f"标题 {external_id}",
        summary=f"摘要 {external_id}",
        platform=platform,
        published_at=datetime(2026, 3, 17, hour, tzinfo=TIMEZONE)
        + timedelta(days=day),
        sentiment=sentiment,
        likes=engagement,
        comments=0,
        shares=0,
        favorites=0,
    )


def fixture_snapshot() -> SpreadPathSnapshot:
    records = (
        record("bili-001", "B站", 0, 9, sentiment="negative", engagement=1_885),
        record("bili-002", "微博", 0, 14, engagement=750),
        record("bili-003", "知乎", 1, 11, sentiment="negative", engagement=1_420),
        record("bili-004", "新闻", 1, 17, engagement=355),
        record("bili-005", "微博", 2, 8, sentiment="negative", engagement=3_310),
        record("bili-006", "新闻", 2, 19, sentiment="positive", engagement=705),
        record("bili-007", "微博", 3, 10, sentiment="negative", engagement=10_020),
        record("bili-008", "B站", 3, 13, engagement=1_600),
        record("bili-009", "新闻", 3, 20, sentiment="negative", engagement=1_365),
        record("bili-010", "B站", 4, 16, sentiment="positive", engagement=2_140),
        record("bili-011", "微博", 5, 12, sentiment="negative", engagement=1_635),
        record("bili-012", "B站", 6, 18, sentiment="negative", engagement=985),
    )
    return SpreadPathSnapshot(
        date(2026, 3, 17),
        date(2026, 3, 23),
        records,
        "Asia/Shanghai",
        "spread-path.v1",
    )


def test_snapshot_builds_complete_daily_platform_matrix_and_entry_order() -> None:
    snapshot = fixture_snapshot()

    assert snapshot.article_count == 12
    assert snapshot.platform_count == 4
    assert [item.platform for item in snapshot.display_platforms] == [
        "B站",
        "微博",
        "知乎",
        "新闻",
    ]
    assert [item.entry_wave for item in snapshot.display_platforms] == [1, 2, 3, 4]
    assert snapshot.multi_platform_days == 4
    assert snapshot.max_daily_platforms == 3
    assert snapshot.max_daily_platform_days == (date(2026, 3, 20),)
    assert snapshot.daily_platform_counts[date(2026, 3, 20)] == {
        "微博": 1,
        "B站": 1,
        "新闻": 1,
    }


def test_facts_and_evidence_preserve_first_records_and_denominators() -> None:
    snapshot = fixture_snapshot()
    facts = snapshot.to_fact_set()

    assert facts.get("firstObservationIntervalHours").formatted_value == "32.0"
    assert facts.get("multiPlatformDays").raw_value == 4
    assert facts.get("platform1Name").formatted_value == "B站"
    assert facts.get("platform1Articles").raw_value == 4
    assert facts.get("platform1NegativeArticles").raw_value == 2
    assert facts.get("platform1ActiveDays").raw_value == 4
    assert facts.get("platform1FirstRecordId").source_record_ids == ("bili-001",)
    assert facts.get("relationshipEdges").formatted_value == "不可用"
    assert snapshot.to_evidence_set().record_ids == (
        "bili-001",
        "bili-002",
        "bili-003",
        "bili-004",
    )


def test_exact_time_ties_share_an_entry_wave_without_semantic_order() -> None:
    tied_time = datetime(2026, 3, 17, 9, tzinfo=TIMEZONE)
    records = (
        record("a", "甲平台", 0, 9),
        SpreadPathSourceRecord(
            "b", "标题 b", "摘要 b", "乙平台", tied_time, "neutral", 1, 0, 0, 0
        ),
    )
    snapshot = SpreadPathSnapshot(
        date(2026, 3, 17),
        date(2026, 3, 17),
        records,
        "Asia/Shanghai",
        "spread-path.v1",
    )

    assert [item.entry_wave for item in snapshot.display_platforms] == [1, 1]
    assert snapshot.entry_wave_count == 1
    assert snapshot.earliest_platforms == ("乙平台", "甲平台")
    assert snapshot.first_observation_interval_hours == 0


def test_material_selection_is_bounded_then_rendered_by_first_observation() -> None:
    records = tuple(
        record(f"id-{index}", f"平台{index}", index, 9, engagement=100 + index)
        for index in range(7)
    ) + (record("extra", "平台6", 6, 10, engagement=500),)
    snapshot = SpreadPathSnapshot(
        date(2026, 3, 17),
        date(2026, 3, 23),
        records,
        "Asia/Shanghai",
        "spread-path.v1",
    )

    assert len(snapshot.display_platforms) == 6
    assert "平台6" in {item.platform for item in snapshot.display_platforms}
    assert snapshot.to_fact_set().get("omittedPlatformCount").raw_value == 1


def test_empty_and_single_platform_snapshots_keep_auditable_base_facts() -> None:
    empty = SpreadPathSnapshot(
        date(2026, 3, 17), date(2026, 3, 23), (), "Asia/Shanghai", "spread-path.v1"
    )
    assert empty.has_data is False
    assert empty.to_fact_set().get("articles").raw_value == 0
    assert empty.to_evidence_set().records == ()

    single = SpreadPathSnapshot(
        date(2026, 3, 17),
        date(2026, 3, 23),
        (record("one", "单平台", 0, 9),),
        "Asia/Shanghai",
        "spread-path.v1",
    )
    assert single.platform_count == 1
    assert single.first_observation_interval_hours == 0
    assert single.entry_wave_count == 1


def test_snapshot_rejects_duplicate_ids_unstable_order_or_out_of_range_records() -> None:
    first = record("first", "平台", 0, 9)
    second = record("second", "平台", 1, 9)
    with pytest.raises(ValueError, match="unique"):
        SpreadPathSnapshot(
            date(2026, 3, 17),
            date(2026, 3, 23),
            (first, first),
            "Asia/Shanghai",
            "spread-path.v1",
        )
    with pytest.raises(ValueError, match="chronological"):
        SpreadPathSnapshot(
            date(2026, 3, 17),
            date(2026, 3, 23),
            (second, first),
            "Asia/Shanghai",
            "spread-path.v1",
        )
    with pytest.raises(ValueError, match="outside"):
        SpreadPathSnapshot(
            date(2026, 3, 18),
            date(2026, 3, 23),
            (first,),
            "Asia/Shanghai",
            "spread-path.v1",
        )
