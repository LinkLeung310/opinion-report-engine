from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from report_engine.sections.engagement import EngagementRecord, EngagementSnapshot


TIMEZONE = ZoneInfo("Asia/Shanghai")


def record(
    external_id: str,
    rank: int,
    total: tuple[int, int, int, int],
    day: int,
    sentiment: str = "negative",
) -> EngagementRecord:
    likes, comments, shares, favorites = total
    return EngagementRecord(
        external_id=external_id,
        title=f"标题 {external_id}",
        summary=f"摘要 {external_id}",
        platform="微博" if rank <= 2 else "B站",
        published_at=datetime(2026, 3, day, 10, tzinfo=TIMEZONE),
        sentiment=sentiment,
        likes=likes,
        comments=comments,
        shares=shares,
        favorites=favorites,
        engagement_rank=rank,
    )


def fixture_snapshot() -> EngagementSnapshot:
    return EngagementSnapshot(
        article_count=12,
        positive_total_engagement_articles=12,
        zero_engagement_articles=0,
        likes=15_460,
        comments=4_705,
        shares=4_620,
        favorites=1_385,
        leading_record_count=1,
        records=(
            record("bili-007", 1, (5_200, 1_800, 2_600, 420), 20),
            record("bili-005", 2, (2_100, 640, 390, 180), 19),
            record("bili-010", 3, (1_400, 330, 260, 150), 21, "positive"),
            record("bili-001", 4, (1_200, 380, 210, 95), 17),
            record("bili-011", 5, (1_100, 270, 190, 75), 22),
        ),
        query_id="engagement.v1",
    )


def test_engagement_facts_preserve_components_and_unrounded_concentration() -> None:
    snapshot = fixture_snapshot()
    facts = snapshot.to_fact_set()

    assert snapshot.total_engagement == 26_170
    assert facts.get("likes").formatted_value == "15,460"
    assert facts.get("likesShare").raw_value == Decimal(15_460) / Decimal(26_170)
    assert facts.get("likesShare").formatted_value == "59.1%"
    assert facts.get("commentsAndShares").raw_value == 9_325
    assert facts.get("commentsAndSharesShare").formatted_value == "35.6%"
    assert facts.get("engagementPerArticle").formatted_value == "2,180.8"
    assert facts.get("topRecordShare").formatted_value == "38.3%"
    assert facts.get("topThreeRecordsShare").raw_value == Decimal(15_470) / Decimal(
        26_170
    )
    assert facts.get("topThreeRecordsShare").formatted_value == "59.1%"


def test_ranked_records_and_evidence_keep_real_source_ids_and_fields() -> None:
    snapshot = fixture_snapshot()
    facts = snapshot.to_fact_set()
    evidence = snapshot.to_evidence_set()

    assert [row.external_id for row in snapshot.records] == [
        "bili-007",
        "bili-005",
        "bili-010",
        "bili-001",
        "bili-011",
    ]
    assert evidence.record_ids == ("bili-007", "bili-005", "bili-010")
    assert evidence.records[0].title == "标题 bili-007"
    assert facts.get("record1Total").formatted_value == "10,020"
    assert facts.get("record3Sentiment").formatted_value == "正面"
    assert facts.get("record5Id").source_record_ids == ("bili-011",)
    assert facts.get("evidenceCount").source_record_ids == evidence.record_ids


def test_nonempty_zero_engagement_is_complete_factual_snapshot() -> None:
    snapshot = EngagementSnapshot(
        article_count=2,
        positive_total_engagement_articles=0,
        zero_engagement_articles=2,
        likes=0,
        comments=0,
        shares=0,
        favorites=0,
        leading_record_count=0,
        records=(),
        query_id="engagement.v1",
    )

    facts = snapshot.to_fact_set()
    assert snapshot.has_articles is True
    assert snapshot.has_engagement is False
    assert snapshot.to_evidence_set().records == ()
    assert facts.get("totalEngagement").formatted_value == "0"
    assert facts.get("topThreeRecordsShare").formatted_value == "0.0%"
    assert facts.get("leadingRecordId").formatted_value == "暂无"


def test_leader_tie_count_can_exceed_the_five_displayed_records() -> None:
    snapshot = EngagementSnapshot(
        article_count=6,
        positive_total_engagement_articles=6,
        zero_engagement_articles=0,
        likes=60,
        comments=0,
        shares=0,
        favorites=0,
        leading_record_count=6,
        records=tuple(
            record(f"tie-{rank}", rank, (10, 0, 0, 0), 20)
            for rank in range(1, 6)
        ),
        query_id="engagement.v1",
    )

    facts = snapshot.to_fact_set()
    assert len(snapshot.records) == 5
    assert facts.get("leadingRecordCount").raw_value == 6
    assert facts.get("leadingRecordId").formatted_value == "并列"
    assert facts.get("leadingRecordTotal").source_record_ids == ()


def test_empty_snapshot_is_no_data_and_has_no_fact_set() -> None:
    snapshot = EngagementSnapshot(
        article_count=0,
        positive_total_engagement_articles=0,
        zero_engagement_articles=0,
        likes=0,
        comments=0,
        shares=0,
        favorites=0,
        leading_record_count=0,
        records=(),
        query_id="engagement.v1",
    )

    assert snapshot.has_articles is False
    with pytest.raises(ValueError, match="empty snapshot"):
        snapshot.to_fact_set()


def test_snapshot_rejects_inconsistent_counts_order_and_leaders() -> None:
    with pytest.raises(ValueError, match="must equal articles"):
        EngagementSnapshot(
            article_count=2,
            positive_total_engagement_articles=1,
            zero_engagement_articles=0,
            likes=1,
            comments=0,
            shares=0,
            favorites=0,
            leading_record_count=1,
            records=(record("a", 1, (1, 0, 0, 0), 17),),
            query_id="engagement.v1",
        )

    with pytest.raises(ValueError, match="deterministic rank order"):
        EngagementSnapshot(
            article_count=2,
            positive_total_engagement_articles=2,
            zero_engagement_articles=0,
            likes=5,
            comments=0,
            shares=0,
            favorites=0,
            leading_record_count=1,
            records=(
                record("lower", 1, (2, 0, 0, 0), 18),
                record("higher", 2, (3, 0, 0, 0), 17),
            ),
            query_id="engagement.v1",
        )

    with pytest.raises(ValueError, match="share the maximum"):
        EngagementSnapshot(
            article_count=2,
            positive_total_engagement_articles=2,
            zero_engagement_articles=0,
            likes=5,
            comments=0,
            shares=0,
            favorites=0,
            leading_record_count=2,
            records=(
                record("leader", 1, (3, 0, 0, 0), 18),
                record("follower", 2, (2, 0, 0, 0), 17),
            ),
            query_id="engagement.v1",
        )

    with pytest.raises(ValueError, match="cannot exceed aggregate totals"):
        EngagementSnapshot(
            article_count=1,
            positive_total_engagement_articles=1,
            zero_engagement_articles=0,
            likes=1,
            comments=0,
            shares=0,
            favorites=0,
            leading_record_count=1,
            records=(record("over-counted", 1, (2, 0, 0, 0), 17),),
            query_id="engagement.v1",
        )
