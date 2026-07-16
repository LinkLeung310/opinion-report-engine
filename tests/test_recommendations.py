from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from report_engine.sections.negative_themes import NegativeThemeSourceRecord
from report_engine.sections.recommendations import RecommendationsSnapshot


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


def fixture_snapshot() -> RecommendationsSnapshot:
    rows = (
        ("bili-001", "用户发现负反馈入口层级变化，担心表达不喜欢变得更困难。", "medium", 3, 1_885, "B站"),
        ("bili-003", "讨论认为减少负反馈入口可能影响推荐透明度和用户控制感。", "high", 4, 1_420, "知乎"),
        ("bili-005", "评论集中表达对选择权被削弱的不满，并要求恢复原入口。", "high", 4, 3_310, "微博"),
        ("bili-007", "大量转发将事件描述为平台不愿听取负面反馈，情绪明显升温。", "critical", 5, 10_020, "微博"),
        ("bili-009", "报道归纳用户担忧：推荐原因不透明、纠偏成本增加、反馈是否生效。", "high", 4, 1_365, "新闻"),
        ("bili-011", "负面讨论回落，但用户继续要求平台说明实验范围和反馈机制。", "medium", 2, 1_635, "微博"),
        ("bili-012", "讨论量趋缓，核心诉求从恢复入口转向公开推荐与实验规则。", "low", 2, 985, "B站"),
    )
    records = tuple(
        record(external_id, summary, index, severity=severity, score=score, engagement=engagement, platform=platform)
        for index, (external_id, summary, severity, score, engagement, platform) in enumerate(rows)
    )
    return RecommendationsSnapshot(12, 7, records, "recommendations.v1")


def test_playbook_selects_four_actions_with_deterministic_evidence() -> None:
    snapshot = fixture_snapshot()
    actions = snapshot.selected_actions

    assert [action.action_id for action in actions] == [
        "triage_high_risk",
        "restore_user_control",
        "explain_change",
        "close_feedback_loop",
    ]
    assert [action.horizon_zh for action in actions] == [
        "立即",
        "24小时内",
        "24小时内",
        "24小时内",
    ]
    assert snapshot.action_citation_ids == (
        "bili-007",
        "bili-005",
        "bili-003",
        "bili-007",
    )
    assert snapshot.to_evidence_set().record_ids == (
        "bili-007",
        "bili-005",
        "bili-003",
    )


def test_facts_preserve_triggers_coverage_and_playbook_text() -> None:
    facts = fixture_snapshot().to_fact_set()

    assert facts.get("articles").raw_value == 12
    assert facts.get("negativeShare").formatted_value == "58.3%"
    assert facts.get("highCriticalNegativeShare").formatted_value == "57.1%"
    assert facts.get("classifiedNegativeShare").formatted_value == "100.0%"
    assert facts.get("selectedActionCount").raw_value == 4
    assert facts.get("maximumActions").raw_value == 4
    assert facts.get("action1TriggerArticles").source_record_ids == (
        "bili-003",
        "bili-005",
        "bili-007",
        "bili-009",
    )
    assert facts.get("action2RepresentativeId").source_record_ids == ("bili-005",)
    assert facts.get("action3OwnersEn").formatted_value == "Product, PR"


def test_fallback_is_used_only_when_no_primary_action_qualifies() -> None:
    records = (
        record("one", "没有命中行动代码本的单篇负面。", 0, severity="low", score=2),
        record("two", "另一条也没有明确指标。", 1, severity="medium", score=3),
    )
    snapshot = RecommendationsSnapshot(2, 2, records, "recommendations.v1")

    assert [action.action_id for action in snapshot.selected_actions] == [
        "review_unresolved_negative"
    ]
    assert snapshot.selected_actions[0].horizon_en == "within 72 hours"
    assert snapshot.action_citation_ids == ("two",)


def test_empty_and_zero_negative_snapshots_select_no_actions() -> None:
    empty = RecommendationsSnapshot(0, 0, (), "recommendations.v1")
    no_negative = RecommendationsSnapshot(3, 0, (), "recommendations.v1")

    assert empty.selected_actions == ()
    assert no_negative.selected_actions == ()
    assert no_negative.to_evidence_set().records == ()
    assert no_negative.to_fact_set().get("selectedActionCount").raw_value == 0


def test_snapshot_reuses_negative_record_validation() -> None:
    first = record("first", "选择权受到影响。", 0)
    second = record("second", "要求恢复入口。", 1)
    with pytest.raises(ValueError, match="must equal"):
        RecommendationsSnapshot(2, 1, (first, second), "recommendations.v1")
    with pytest.raises(ValueError, match="chronological"):
        RecommendationsSnapshot(2, 2, (second, first), "recommendations.v1")
