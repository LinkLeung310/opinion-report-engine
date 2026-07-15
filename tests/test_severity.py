from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from report_engine.sections.severity import (
    SeverityEvidenceRecord,
    SeveritySnapshot,
)


def evidence(
    external_id: str,
    severity: str,
    score: int,
    engagement: int,
) -> SeverityEvidenceRecord:
    return SeverityEvidenceRecord(
        external_id=external_id,
        title=f"标题 {external_id}",
        summary=f"摘要 {external_id}",
        platform="测试平台",
        published_at=datetime(2026, 3, 20, 10, tzinfo=ZoneInfo("Asia/Shanghai")),
        sentiment="negative",
        negative_score=score,
        severity=severity,
        total_engagement=engagement,
    )


def fixture_snapshot() -> SeveritySnapshot:
    return SeveritySnapshot(
        negative_articles=7,
        low_articles=1,
        medium_articles=2,
        high_articles=3,
        critical_articles=1,
        missing_severity_articles=0,
        score_1_articles=0,
        score_2_articles=2,
        score_3_articles=1,
        score_4_articles=3,
        score_5_articles=1,
        scored_negative_articles=7,
        missing_score_articles=0,
        average_negative_score=Decimal(24) / Decimal(7),
        negative_engagement=20_620,
        high_critical_engagement=16_115,
        evidence_records=(
            evidence("bili-007", "critical", 5, 10_020),
            evidence("bili-005", "high", 4, 3_310),
            evidence("bili-003", "high", 4, 1_420),
        ),
        query_id="severity.v1",
    )


def empty_snapshot() -> SeveritySnapshot:
    return SeveritySnapshot(
        negative_articles=0,
        low_articles=0,
        medium_articles=0,
        high_articles=0,
        critical_articles=0,
        missing_severity_articles=0,
        score_1_articles=0,
        score_2_articles=0,
        score_3_articles=0,
        score_4_articles=0,
        score_5_articles=0,
        scored_negative_articles=0,
        missing_score_articles=0,
        average_negative_score=None,
        negative_engagement=0,
        high_critical_engagement=0,
        evidence_records=(),
        query_id="severity.v1",
    )


def test_severity_facts_preserve_raw_values_and_format_only_for_display() -> None:
    facts = fixture_snapshot().to_fact_set()

    assert facts.get("negativeArticles").raw_value == 7
    assert facts.get("averageNegativeScore").raw_value == Decimal(24) / Decimal(7)
    assert facts.get("averageNegativeScore").formatted_value == "3.4"
    assert facts.get("highCriticalArticles").raw_value == 4
    assert facts.get("highCriticalRatio").formatted_value == "57.1%"
    assert facts.get("criticalRatio").formatted_value == "14.3%"
    assert facts.get("highCriticalEngagementShare").formatted_value == "78.2%"
    assert facts.get("highestObservedSeverity").raw_value == "critical"
    assert facts.get("highestObservedSeverity").formatted_value == "危急"


def test_severity_evidence_keeps_real_fields_and_source_ids() -> None:
    snapshot = fixture_snapshot()
    evidence_set = snapshot.to_evidence_set()

    assert evidence_set.record_ids == ("bili-007", "bili-005", "bili-003")
    assert evidence_set.records[0].title == "标题 bili-007"
    assert evidence_set.records[0].summary == "摘要 bili-007"
    assert evidence_set.records[0].sentiment == "negative"
    assert snapshot.to_fact_set().get("evidenceCount").source_record_ids == (
        "bili-007",
        "bili-005",
        "bili-003",
    )


def test_empty_severity_snapshot_is_valid_no_data_without_facts_or_evidence() -> None:
    snapshot = empty_snapshot()

    assert snapshot.has_data is False
    assert snapshot.to_evidence_set().records == ()
    with pytest.raises(ValueError, match="empty snapshot"):
        snapshot.to_fact_set()


def test_severity_snapshot_rejects_inconsistent_distributions() -> None:
    with pytest.raises(ValueError, match="Severity counts"):
        SeveritySnapshot(
            negative_articles=1,
            low_articles=0,
            medium_articles=0,
            high_articles=0,
            critical_articles=0,
            missing_severity_articles=0,
            score_1_articles=1,
            score_2_articles=0,
            score_3_articles=0,
            score_4_articles=0,
            score_5_articles=0,
            scored_negative_articles=1,
            missing_score_articles=0,
            average_negative_score=Decimal(1),
            negative_engagement=0,
            high_critical_engagement=0,
            evidence_records=(),
            query_id="severity.v1",
        )
