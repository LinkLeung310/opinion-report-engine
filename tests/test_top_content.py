from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from report_engine.sections.top_content import TopContentRecord, TopContentSnapshot


TIMEZONE = ZoneInfo("Asia/Shanghai")


def record(
    external_id: str,
    engagement_rank: int | None,
    risk_rank: int | None,
    *,
    sentiment: str = "negative",
    severity: str | None = "high",
    negative_score: int | None = 4,
    total: int = 100,
) -> TopContentRecord:
    return TopContentRecord(
        external_id=external_id,
        title=f"标题 {external_id}",
        summary=f"摘要 {external_id}",
        platform="测试平台",
        published_at=datetime(2026, 3, 20, 10, tzinfo=TIMEZONE),
        sentiment=sentiment,
        severity=severity,
        negative_score=negative_score,
        likes=total,
        comments=0,
        shares=0,
        favorites=0,
        engagement_rank=engagement_rank,
        risk_rank=risk_rank,
    )


def fixture_snapshot() -> TopContentSnapshot:
    return TopContentSnapshot(
        article_count=12,
        positive_engagement_articles=12,
        high_risk_signal_articles=4,
        total_engagement=26_170,
        records=(
            record("bili-007", 1, 1, severity="critical", negative_score=5, total=10_020),
            record("bili-005", 2, 2, total=3_310),
            record(
                "bili-010",
                3,
                None,
                sentiment="positive",
                severity=None,
                negative_score=None,
                total=2_140,
            ),
            record("bili-003", 7, 3, total=1_420),
        ),
        query_id="top-content.v1",
    )


def empty_snapshot() -> TopContentSnapshot:
    return TopContentSnapshot(0, 0, 0, 0, (), "top-content.v1")


def test_top_content_facts_preserve_cross_signal_counts_and_denominator() -> None:
    snapshot = fixture_snapshot()
    facts = snapshot.to_fact_set()

    assert [item.category for item in snapshot.records] == [
        "dual_signal",
        "dual_signal",
        "engagement_only",
        "risk_only",
    ]
    assert facts.get("dualSignalCount").raw_value == 2
    assert facts.get("engagementOnlyCount").raw_value == 1
    assert facts.get("riskOnlyCount").raw_value == 1
    assert facts.get("selectedEngagement").raw_value == 16_890
    assert facts.get("selectedEngagementShare").formatted_value == "64.5%"
    assert facts.get("record3Severity").formatted_value == "不适用"
    assert facts.get("record4EngagementRank").raw_value == 7


def test_top_content_evidence_preserves_fixed_order_and_exact_sources() -> None:
    snapshot = fixture_snapshot()

    assert snapshot.to_evidence_set().record_ids == (
        "bili-007",
        "bili-005",
        "bili-010",
        "bili-003",
    )
    assert snapshot.to_evidence_set().records[0].title == "标题 bili-007"
    assert snapshot.to_fact_set().get("selectedCount").source_record_ids == (
        "bili-007",
        "bili-005",
        "bili-010",
        "bili-003",
    )


def test_nonempty_scope_without_qualifying_signals_has_auditable_zero_facts() -> None:
    snapshot = TopContentSnapshot(
        article_count=2,
        positive_engagement_articles=0,
        high_risk_signal_articles=0,
        total_engagement=0,
        records=(),
        query_id="top-content.v1",
    )

    assert snapshot.has_articles is True
    assert snapshot.has_selected_records is False
    assert snapshot.to_evidence_set().records == ()
    assert snapshot.to_fact_set().get("selectedEngagementShare").formatted_value == "0.0%"


def test_empty_scope_is_no_data_without_facts() -> None:
    snapshot = empty_snapshot()

    assert snapshot.has_articles is False
    with pytest.raises(ValueError, match="empty snapshot"):
        snapshot.to_fact_set()


def test_top_content_rejects_incomplete_shortlists_or_wrong_order() -> None:
    with pytest.raises(ValueError, match="engagement shortlist is incomplete"):
        TopContentSnapshot(
            article_count=4,
            positive_engagement_articles=4,
            high_risk_signal_articles=1,
            total_engagement=500,
            records=(record("dual", 1, 1),),
            query_id="top-content.v1",
        )

    with pytest.raises(ValueError, match="fixed display order"):
        TopContentSnapshot(
            article_count=2,
            positive_engagement_articles=1,
            high_risk_signal_articles=1,
            total_engagement=200,
            records=(
                record("risk", None, 1),
                record(
                    "engagement",
                    1,
                    None,
                    sentiment="positive",
                    severity=None,
                    negative_score=None,
                ),
            ),
            query_id="top-content.v1",
        )
