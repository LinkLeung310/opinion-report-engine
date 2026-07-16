from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresBizImpactRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def fetch_snapshot(topic_tag: str):
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    raw = sample_config()
    raw["topic"] = {
        "tag": topic_tag,
        "displayName": "B站猜你不喜欢算法调整",
        "eventTitle": "B站猜你不喜欢算法调整事件",
    }
    scope = ReportPlanner(default_registry()).build(
        ReportConfig.model_validate(raw)
    ).scope
    with psycopg.connect(dsn, connect_timeout=5) as connection:
        return PostgresBizImpactRepository(connection).fetch(scope)


def test_biz_impact_sql_matches_the_synthetic_fixture_scope() -> None:
    snapshot = fetch_snapshot("bilibili-dislike")
    facts = snapshot.to_fact_set()

    assert snapshot.query_id == "biz-impact.v1"
    assert snapshot.article_count == 12
    assert (
        snapshot.positive_articles,
        snapshot.neutral_articles,
        snapshot.negative_articles,
    ) == (2, 3, 7)
    assert snapshot.platform_count == 4
    assert snapshot.active_days == 7
    assert snapshot.peak_day.isoformat() == "2026-03-20"
    assert snapshot.peak_article_count == 3
    assert snapshot.high_critical_negative_articles == 4
    assert (snapshot.likes, snapshot.comments, snapshot.shares, snapshot.favorites) == (
        15_460,
        4_705,
        4_620,
        1_385,
    )
    assert snapshot.total_stored_interaction == 26_170
    assert snapshot.comments_and_shares == 9_325
    assert facts.get("negativeShare").formatted_value == "58.3%"
    assert facts.get("highCriticalNegativeShare").formatted_value == "57.1%"


def test_biz_impact_sql_keeps_empty_scope_auditable() -> None:
    snapshot = fetch_snapshot("missing-biz-impact-topic")
    facts = snapshot.to_fact_set()

    assert snapshot.has_data is False
    assert snapshot.article_count == 0
    assert snapshot.active_days == 0
    assert snapshot.peak_day is None
    assert snapshot.total_stored_interaction == 0
    assert facts.get("negativeShare").formatted_value == "不可用"
