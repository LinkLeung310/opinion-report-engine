from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from report_engine.sections.timeline import TimelineRoleRecord, TimelineSnapshot


TIMEZONE = ZoneInfo("Asia/Shanghai")


def role_record(
    role: str,
    external_id: str,
    day: int,
    hour: int,
    *,
    engagement: int = 100,
    response_tagged: bool = False,
) -> TimelineRoleRecord:
    published_at = datetime(2026, 3, day, hour, tzinfo=TIMEZONE)
    return TimelineRoleRecord(
        role=role,
        external_id=external_id,
        title=f"标题 {external_id}",
        summary=f"摘要 {external_id}",
        platform="测试平台",
        published_at=published_at,
        published_day=published_at.date(),
        sentiment="negative",
        total_engagement=engagement,
        response_tagged=response_tagged,
    )


def fixture_snapshot() -> TimelineSnapshot:
    return TimelineSnapshot(
        article_count=12,
        peak_day=date(2026, 3, 20),
        peak_articles=3,
        response_tagged_articles=1,
        role_records=(
            role_record("first_observed", "bili-001", 17, 9),
            role_record(
                "tagged_response",
                "bili-006",
                19,
                19,
                response_tagged=True,
            ),
            role_record(
                "peak_day_representative",
                "bili-007",
                20,
                10,
                engagement=10_020,
            ),
            role_record("last_observed", "bili-012", 23, 18),
        ),
        timezone_name="Asia/Shanghai",
        query_id="timeline.v1",
    )


def test_timeline_facts_and_evidence_preserve_chronology_and_sources() -> None:
    snapshot = fixture_snapshot()
    facts = snapshot.to_fact_set()

    assert snapshot.to_evidence_set().record_ids == (
        "bili-001",
        "bili-006",
        "bili-007",
        "bili-012",
    )
    assert facts.get("articles").raw_value == 12
    assert facts.get("peakDay").formatted_value == "3/20"
    assert facts.get("peakArticles").raw_value == 3
    assert facts.get("responseTaggedArticles").raw_value == 1
    assert facts.get("observedCalendarDays").raw_value == 7
    assert facts.get("milestoneCount").source_record_ids == (
        "bili-001",
        "bili-006",
        "bili-007",
        "bili-012",
    )
    assert facts.get("milestone3Roles").formatted_value == "峰值日代表"
    assert facts.get("milestone3PeakEngagement").formatted_value == "10,020"


def test_timeline_merges_multiple_roles_for_one_evidence_record() -> None:
    shared = role_record("first_observed", "one", 20, 10)
    snapshot = TimelineSnapshot(
        article_count=1,
        peak_day=date(2026, 3, 20),
        peak_articles=1,
        response_tagged_articles=0,
        role_records=(
            shared,
            role_record("peak_day_representative", "one", 20, 10),
            role_record("last_observed", "one", 20, 10),
        ),
        timezone_name="Asia/Shanghai",
        query_id="timeline.v1",
    )

    assert len(snapshot.milestones) == 1
    assert snapshot.milestones[0].roles == (
        "first_observed",
        "peak_day_representative",
        "last_observed",
    )
    assert snapshot.milestones[0].role_display == "首次收录、峰值日代表、最后收录"
    assert snapshot.observed_calendar_days == 1
    assert snapshot.to_fact_set().get("milestoneCount").raw_value == 1


def test_timeline_without_response_tag_remains_complete_and_ordered() -> None:
    snapshot = TimelineSnapshot(
        article_count=3,
        peak_day=date(2026, 3, 20),
        peak_articles=1,
        response_tagged_articles=0,
        role_records=(
            role_record("first_observed", "first", 18, 10),
            role_record("peak_day_representative", "peak", 20, 10),
            role_record("last_observed", "last", 22, 10),
        ),
        timezone_name="Asia/Shanghai",
        query_id="timeline.v1",
    )

    assert snapshot.has_data is True
    assert [milestone.external_id for milestone in snapshot.milestones] == [
        "first",
        "peak",
        "last",
    ]
    assert snapshot.to_fact_set().get("responseTaggedArticles").raw_value == 0


def test_empty_timeline_is_valid_no_data_without_facts() -> None:
    snapshot = TimelineSnapshot(
        article_count=0,
        peak_day=None,
        peak_articles=0,
        response_tagged_articles=0,
        role_records=(),
        timezone_name="Asia/Shanghai",
        query_id="timeline.v1",
    )

    assert snapshot.has_data is False
    assert snapshot.milestones == ()
    assert snapshot.to_evidence_set().records == ()
    with pytest.raises(ValueError, match="empty snapshot"):
        snapshot.to_fact_set()


def test_timeline_rejects_incomplete_roles_and_mismatched_duplicate_payloads() -> None:
    with pytest.raises(ValueError, match="complete fixed order"):
        TimelineSnapshot(
            article_count=2,
            peak_day=date(2026, 3, 20),
            peak_articles=1,
            response_tagged_articles=0,
            role_records=(
                role_record("first_observed", "first", 19, 10),
                role_record("last_observed", "last", 21, 10),
            ),
            timezone_name="Asia/Shanghai",
            query_id="timeline.v1",
        )

    with pytest.raises(ValueError, match="preserve source fields"):
        TimelineSnapshot(
            article_count=1,
            peak_day=date(2026, 3, 20),
            peak_articles=1,
            response_tagged_articles=0,
            role_records=(
                role_record("first_observed", "one", 20, 10),
                role_record(
                    "peak_day_representative",
                    "one",
                    20,
                    10,
                    engagement=999,
                ),
                role_record("last_observed", "one", 20, 10),
            ),
            timezone_name="Asia/Shanghai",
            query_id="timeline.v1",
        )
