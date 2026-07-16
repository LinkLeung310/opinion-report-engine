from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from report_engine.sections.negative_themes import (
    NegativeThemesSnapshot,
    NegativeThemeSourceRecord,
)


TIMEZONE = ZoneInfo("Asia/Shanghai")


def record(
    external_id: str,
    summary: str,
    index: int,
    *,
    severity: str | None = "high",
    score: int | None = 4,
    engagement: int = 100,
    platform: str = "测试平台",
) -> NegativeThemeSourceRecord:
    return NegativeThemeSourceRecord(
        external_id=external_id,
        title=f"标题 {external_id}",
        summary=summary,
        platform=platform,
        published_at=datetime(2026, 3, 17, 9, tzinfo=TIMEZONE)
        + timedelta(days=index),
        sentiment="negative",
        severity=severity,
        negative_score=score,
        likes=engagement,
        comments=0,
        shares=0,
        favorites=0,
    )


def fixture_snapshot() -> NegativeThemesSnapshot:
    summaries = (
        ("bili-001", "用户发现负反馈入口层级变化，担心表达不喜欢变得更困难。", "medium", 3, 1_885, "B站"),
        ("bili-003", "讨论认为减少负反馈入口可能影响推荐透明度和用户控制感。", "high", 4, 1_420, "知乎"),
        ("bili-005", "评论集中表达对选择权被削弱的不满，并要求恢复原入口。", "high", 4, 3_310, "微博"),
        ("bili-007", "大量转发将事件描述为平台不愿听取负面反馈，情绪明显升温。", "critical", 5, 10_020, "微博"),
        ("bili-009", "报道归纳用户担忧：推荐原因不透明、纠偏成本增加、反馈是否生效。", "high", 4, 1_365, "新闻"),
        ("bili-011", "负面讨论回落，但用户继续要求平台说明实验范围和反馈机制。", "medium", 2, 1_635, "微博"),
        ("bili-012", "讨论量趋缓，核心诉求从恢复入口转向公开推荐与实验规则。", "low", 2, 985, "B站"),
    )
    records = tuple(
        record(
            external_id,
            summary,
            index,
            severity=severity,
            score=score,
            engagement=engagement,
            platform=platform,
        )
        for index, (external_id, summary, severity, score, engagement, platform) in enumerate(summaries)
    )
    return NegativeThemesSnapshot(12, 7, records, "negative-themes.v1")


def test_codebook_builds_ranked_overlapping_theme_cross_tabs() -> None:
    snapshot = fixture_snapshot()
    themes = snapshot.display_themes

    assert [theme.theme_id for theme in themes] == [
        "user_agency",
        "transparency",
        "feedback_effectiveness",
    ]
    assert [theme.article_count for theme in themes] == [5, 4, 3]
    assert [theme.concern_articles for theme in themes] == [4, 2, 2]
    assert [theme.demand_articles for theme in themes] == [2, 2, 1]
    assert [theme.high_critical_articles for theme in themes] == [3, 2, 2]
    assert [theme.total_engagement for theme in themes] == [8_965, 5_405, 13_020]
    assert snapshot.total_theme_memberships == 12
    assert snapshot.classified_record_ids == tuple(
        record.external_id for record in snapshot.records
    )


def test_facts_preserve_negative_denominators_roles_and_source_ids() -> None:
    facts = fixture_snapshot().to_fact_set()

    assert facts.get("articles").raw_value == 12
    assert facts.get("negativeArticles").raw_value == 7
    assert facts.get("classifiedNegativeShare").formatted_value == "100.0%"
    assert facts.get("unclassifiedNegativeArticles").raw_value == 0
    assert facts.get("theme1Share").formatted_value == "71.4%"
    assert facts.get("theme1HighCriticalShare").formatted_value == "60.0%"
    assert facts.get("theme1Articles").source_record_ids == (
        "bili-001",
        "bili-003",
        "bili-005",
        "bili-009",
        "bili-012",
    )
    assert facts.get("theme2RepresentativeId").source_record_ids == ("bili-003",)


def test_representatives_and_evidence_are_deterministic_and_real() -> None:
    snapshot = fixture_snapshot()

    assert snapshot.representative_ids == ("bili-005", "bili-003", "bili-007")
    assert snapshot.to_evidence_set().record_ids == (
        "bili-005",
        "bili-003",
        "bili-007",
    )
    assert snapshot.to_evidence_set().records[0].summary == snapshot.records[2].summary


def test_zero_negative_and_no_qualifying_theme_snapshots_keep_auditable_facts() -> None:
    empty = NegativeThemesSnapshot(0, 0, (), "negative-themes.v1")
    assert empty.has_negative_articles is False
    assert empty.to_fact_set().get("negativeArticles").raw_value == 0

    records = (
        record("one", "单篇仅有选择权表达。", 0),
        record("two", "另一篇没有代码本指标。", 1),
    )
    no_theme = NegativeThemesSnapshot(2, 2, records, "negative-themes.v1")
    assert no_theme.has_display_themes is False
    assert no_theme.classified_record_ids == ("one",)
    assert no_theme.unclassified_record_ids == ("two",)
    assert no_theme.to_evidence_set().records == ()
    assert no_theme.to_fact_set().get("classifiedNegativeShare").formatted_value == "50.0%"


def test_snapshot_rejects_count_mismatch_or_unstable_order() -> None:
    first = record("first", "选择权受到影响。", 0)
    second = record("second", "要求恢复入口。", 1)
    with pytest.raises(ValueError, match="must equal"):
        NegativeThemesSnapshot(2, 1, (first, second), "negative-themes.v1")
    with pytest.raises(ValueError, match="chronological"):
        NegativeThemesSnapshot(2, 2, (second, first), "negative-themes.v1")
