from __future__ import annotations

from decimal import Decimal

import pytest

from report_engine.sections.risk import RiskBand, RiskSnapshot


def fixture_snapshot() -> RiskSnapshot:
    return RiskSnapshot(
        article_count=12,
        negative_articles=7,
        high_critical_negative_articles=4,
        platform_count=4,
        negative_platform_count=4,
        calendar_days=7,
        negative_active_days=6,
        total_engagement=26_170,
        negative_engagement=20_620,
        query_id="risk.v1",
    )


def empty_snapshot() -> RiskSnapshot:
    return RiskSnapshot(
        article_count=0,
        negative_articles=0,
        high_critical_negative_articles=0,
        platform_count=0,
        negative_platform_count=0,
        calendar_days=7,
        negative_active_days=0,
        total_engagement=0,
        negative_engagement=0,
        query_id="risk.v1",
    )


def test_risk_facts_keep_unrounded_equal_weight_signals_and_explicit_bands() -> None:
    snapshot = fixture_snapshot()
    facts = snapshot.to_fact_set()

    expected_index = sum(
        (
            Decimal(7) / Decimal(12),
            Decimal(4) / Decimal(7),
            Decimal(1),
            Decimal(6) / Decimal(7),
            Decimal(20_620) / Decimal(26_170),
        ),
        Decimal(0),
    ) / Decimal(5)
    assert snapshot.risk_signal_index == expected_index
    assert facts.get("sentimentPressure").formatted_value == "58.3%"
    assert facts.get("severityPressure").formatted_value == "57.1%"
    assert facts.get("spreadPressure").formatted_value == "100.0%"
    assert facts.get("persistencePressure").formatted_value == "85.7%"
    assert facts.get("amplificationPressure").formatted_value == "78.8%"
    assert facts.get("riskSignalIndex").raw_value == expected_index
    assert facts.get("riskSignalIndex").formatted_value == "76.0%"
    assert facts.get("riskLevel").raw_value == RiskBand.HIGH.value
    assert facts.get("riskLevel").formatted_value == "高"
    assert facts.get("highSignalCount").raw_value == 3
    assert facts.get("mediumSignalCount").raw_value == 2
    assert facts.get("lowSignalCount").raw_value == 0


def test_risk_facts_disclose_non_probability_method_and_schema_limit() -> None:
    facts = fixture_snapshot().to_fact_set()

    assert facts.get("evaluatedSignalCount").raw_value == 5
    assert facts.get("diagnosticKind").formatted_value == "非概率诊断指数"
    assert facts.get("unavailableDimensions").formatted_value == "高管关联、谣言核验"
    assert facts.get("unavailableDimensions").source_id == "risk.schema-capability.v1"


def test_non_empty_scope_with_zero_negatives_is_complete_low_pressure_data() -> None:
    snapshot = RiskSnapshot(
        article_count=2,
        negative_articles=0,
        high_critical_negative_articles=0,
        platform_count=1,
        negative_platform_count=0,
        calendar_days=7,
        negative_active_days=0,
        total_engagement=100,
        negative_engagement=0,
        query_id="risk.v1",
    )
    facts = snapshot.to_fact_set()

    assert snapshot.has_data is True
    assert all(signal.ratio == 0 for signal in snapshot.signals)
    assert all(signal.band is RiskBand.LOW for signal in snapshot.signals)
    assert facts.get("riskSignalIndex").formatted_value == "0.0%"
    assert facts.get("lowSignalCount").raw_value == 5


def test_empty_risk_snapshot_is_no_data_and_cannot_create_facts() -> None:
    snapshot = empty_snapshot()

    assert snapshot.has_data is False
    with pytest.raises(ValueError, match="empty snapshot"):
        snapshot.to_fact_set()


def test_risk_snapshot_rejects_inconsistent_negative_dimensions() -> None:
    with pytest.raises(ValueError, match="Negative platforms"):
        RiskSnapshot(
            article_count=1,
            negative_articles=1,
            high_critical_negative_articles=0,
            platform_count=1,
            negative_platform_count=2,
            calendar_days=1,
            negative_active_days=1,
            total_engagement=0,
            negative_engagement=0,
            query_id="risk.v1",
        )
