from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from report_engine.domain.user_context import VerificationStatus
from report_engine.sections.biz_impact import (
    BIZ_IMPACT_NOTES_SOURCE_ID,
    BizImpactInputError,
    BizImpactSnapshot,
    parse_biz_impact_notes,
)


def fixture_snapshot() -> BizImpactSnapshot:
    return BizImpactSnapshot(
        start_day=date(2026, 3, 17),
        end_day=date(2026, 3, 23),
        article_count=12,
        positive_articles=2,
        neutral_articles=3,
        negative_articles=7,
        platform_count=4,
        active_days=7,
        peak_day=date(2026, 3, 20),
        peak_article_count=3,
        high_critical_negative_articles=4,
        likes=15_460,
        comments=4_705,
        shares=4_620,
        favorites=1_385,
        query_id="biz-impact.v1",
    )


def empty_snapshot() -> BizImpactSnapshot:
    return BizImpactSnapshot(
        start_day=date(2026, 3, 17),
        end_day=date(2026, 3, 23),
        article_count=0,
        positive_articles=0,
        neutral_articles=0,
        negative_articles=0,
        platform_count=0,
        active_days=0,
        peak_day=None,
        peak_article_count=0,
        high_critical_negative_articles=0,
        likes=0,
        comments=0,
        shares=0,
        favorites=0,
        query_id="biz-impact.v1",
    )


def test_notes_are_normalized_into_separate_unverified_context() -> None:
    context = parse_biz_impact_notes(
        "  销量下降 20%\n\t需要结合内部转化数据核验  "
    )

    assert context.key == "notes"
    assert context.text == "销量下降 20% 需要结合内部转化数据核验"
    assert context.source_id == BIZ_IMPACT_NOTES_SOURCE_ID
    assert context.verification_status is VerificationStatus.UNVERIFIED
    with pytest.raises(KeyError):
        fixture_snapshot().to_fact_set().get("notes")


@pytest.mark.parametrize(
    "value",
    (None, 1, "", " \n\t ", "a" * 1_001, "text\x00", "text\x01", "text\x7f"),
)
def test_notes_reject_missing_unbounded_or_control_values(value: object) -> None:
    with pytest.raises(BizImpactInputError, match="notes"):
        parse_biz_impact_notes(value)


def test_notes_accept_exact_limit_and_fold_whitespace_controls() -> None:
    assert len(parse_biz_impact_notes("a" * 1_000).text) == 1_000
    assert parse_biz_impact_notes("业务\x85背景").text == "业务 背景"


def test_business_impact_facts_preserve_pressure_and_coverage_math() -> None:
    snapshot = fixture_snapshot()
    facts = snapshot.to_fact_set()

    assert snapshot.has_data is True
    assert snapshot.active_day_coverage == Decimal(1)
    assert snapshot.peak_share == Decimal(3) / Decimal(12)
    assert snapshot.high_critical_negative_share == Decimal(4) / Decimal(7)
    assert snapshot.high_critical_all_share == Decimal(4) / Decimal(12)
    assert facts.get("negativeShare").formatted_value == "58.3%"
    assert facts.get("highCriticalNegativeShare").formatted_value == "57.1%"
    assert facts.get("highCriticalAllShare").formatted_value == "33.3%"
    assert facts.get("activeDayCoverage").formatted_value == "100.0%"
    assert facts.get("peakDay").formatted_value == "3/20"
    assert facts.get("peakShare").formatted_value == "25.0%"


def test_business_impact_facts_keep_interactions_descriptive_and_unscored() -> None:
    facts = fixture_snapshot().to_fact_set()

    assert facts.get("totalStoredInteraction").raw_value == 26_170
    assert facts.get("commentsAndShares").raw_value == 9_325
    assert facts.get("storedInteractionPerArticle").formatted_value == "2,180.8"
    assert facts.get("reputationPressureLens").formatted_value == "舆情声誉压力"
    assert (
        facts.get("businessOutcomeVerificationStatus").formatted_value
        == "缺少已验证业务结果序列"
    )
    assert facts.get("causalClaimStatus").raw_value == "not_established"
    assert all("score" not in fact.key.lower() for fact in facts.facts)


def test_empty_scope_retains_zero_facts_and_unavailable_denominators() -> None:
    snapshot = empty_snapshot()
    facts = snapshot.to_fact_set()

    assert snapshot.has_data is False
    assert facts.get("articles").raw_value == 0
    assert facts.get("negativeShare").formatted_value == "不可用"
    assert facts.get("highCriticalNegativeShare").formatted_value == "不可用"
    assert facts.get("peakShare").formatted_value == "不可用"
    assert facts.get("storedInteractionPerArticle").formatted_value == "不可用"


def test_non_empty_zero_negative_scope_keeps_measured_zero_and_subset_gap() -> None:
    values = fixture_snapshot().__dict__
    snapshot = BizImpactSnapshot(
        **{
            **values,
            "article_count": 2,
            "positive_articles": 2,
            "neutral_articles": 0,
            "negative_articles": 0,
            "platform_count": 1,
            "active_days": 1,
            "peak_day": date(2026, 3, 17),
            "peak_article_count": 2,
            "high_critical_negative_articles": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "favorites": 0,
        }
    )
    facts = snapshot.to_fact_set()

    assert snapshot.has_data is True
    assert facts.get("negativeShare").formatted_value == "0.0%"
    assert facts.get("highCriticalNegativeShare").formatted_value == "不可用"
    assert facts.get("highCriticalAllShare").formatted_value == "0.0%"


def test_snapshot_rejects_inconsistent_counts_and_peak() -> None:
    values = fixture_snapshot().__dict__
    with pytest.raises(ValueError, match="sentiment counts"):
        BizImpactSnapshot(**{**values, "negative_articles": 6})
    with pytest.raises(ValueError, match="negative subset"):
        BizImpactSnapshot(
            **{**values, "high_critical_negative_articles": 8}
        )
    with pytest.raises(ValueError, match="inside the scope"):
        BizImpactSnapshot(**{**values, "peak_day": date(2026, 3, 24)})
