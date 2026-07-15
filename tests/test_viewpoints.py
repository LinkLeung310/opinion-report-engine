from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from report_engine.sections.viewpoints import (
    ViewpointEvidenceRecord,
    ViewpointsSnapshot,
)


def evidence(
    external_id: str,
    sentiment: str,
    rank: int,
    platform: str,
) -> ViewpointEvidenceRecord:
    return ViewpointEvidenceRecord(
        external_id=external_id,
        title=f"标题 {external_id}",
        summary=f"摘要 {external_id}",
        platform=platform,
        published_at=datetime(2026, 3, 20, 10, tzinfo=ZoneInfo("Asia/Shanghai")),
        sentiment=sentiment,
        total_engagement=100,
        evidence_rank=rank,
    )


def fixture_snapshot() -> ViewpointsSnapshot:
    return ViewpointsSnapshot(
        article_count=12,
        positive_articles=2,
        neutral_articles=3,
        negative_articles=7,
        evidence_records=(
            evidence("bili-007", "negative", 1, "微博"),
            evidence("bili-001", "negative", 2, "B站"),
            evidence("bili-008", "neutral", 1, "B站"),
            evidence("bili-002", "neutral", 2, "微博"),
            evidence("bili-010", "positive", 1, "B站"),
            evidence("bili-006", "positive", 2, "新闻"),
        ),
        query_id="viewpoints.v1",
    )


def empty_snapshot() -> ViewpointsSnapshot:
    return ViewpointsSnapshot(
        article_count=0,
        positive_articles=0,
        neutral_articles=0,
        negative_articles=0,
        evidence_records=(),
        query_id="viewpoints.v1",
    )


def test_viewpoint_facts_separate_population_shares_from_evidence_sample() -> None:
    facts = fixture_snapshot().to_fact_set()

    assert facts.get("articleCount").raw_value == 12
    assert facts.get("negativeShare").raw_value == Decimal(7) / Decimal(12)
    assert facts.get("negativeShare").formatted_value == "58.3%"
    assert facts.get("neutralShare").formatted_value == "25.0%"
    assert facts.get("positiveShare").formatted_value == "16.7%"
    assert facts.get("negativeEvidenceCount").raw_value == 2
    assert facts.get("evidencePlatformCount").raw_value == 3


def test_viewpoint_evidence_preserves_real_fields_and_ordered_source_ids() -> None:
    snapshot = fixture_snapshot()
    evidence_set = snapshot.to_evidence_set()

    assert evidence_set.record_ids == (
        "bili-007",
        "bili-001",
        "bili-008",
        "bili-002",
        "bili-010",
        "bili-006",
    )
    assert evidence_set.records[0].title == "标题 bili-007"
    assert evidence_set.records[-1].summary == "摘要 bili-006"
    assert snapshot.to_fact_set().get("evidenceCount").source_record_ids == (
        "bili-007",
        "bili-001",
        "bili-008",
        "bili-002",
        "bili-010",
        "bili-006",
    )


def test_empty_viewpoint_snapshot_is_valid_no_data_without_facts() -> None:
    snapshot = empty_snapshot()

    assert snapshot.has_data is False
    assert snapshot.to_evidence_set().records == ()
    with pytest.raises(ValueError, match="empty snapshot"):
        snapshot.to_fact_set()


def test_viewpoint_snapshot_rejects_wrong_order_or_inconsistent_counts() -> None:
    with pytest.raises(ValueError, match="fixed display order"):
        ViewpointsSnapshot(
            article_count=2,
            positive_articles=1,
            neutral_articles=0,
            negative_articles=1,
            evidence_records=(
                evidence("positive", "positive", 1, "B站"),
                evidence("negative", "negative", 1, "微博"),
            ),
            query_id="viewpoints.v1",
        )

    with pytest.raises(ValueError, match="Sentiment counts"):
        ViewpointsSnapshot(
            article_count=2,
            positive_articles=0,
            neutral_articles=0,
            negative_articles=1,
            evidence_records=(),
            query_id="viewpoints.v1",
        )
