from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresTopContentRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def scoped_config(topic_tag: str) -> ReportConfig:
    raw = sample_config()
    raw["topic"] = {
        "tag": topic_tag,
        "displayName": "代表性内容测试",
        "eventTitle": "代表性内容测试事件",
    }
    return ReportConfig.model_validate(raw)


def test_top_content_sql_matches_cross_signal_fixture_shortlist() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(
        scoped_config("bilibili-dislike")
    ).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresTopContentRepository(connection).fetch(scope)

    assert snapshot.article_count == 12
    assert snapshot.positive_engagement_articles == 12
    assert snapshot.high_risk_signal_articles == 4
    assert snapshot.total_engagement == 26_170
    assert snapshot.to_evidence_set().record_ids == (
        "bili-007",
        "bili-005",
        "bili-010",
        "bili-003",
    )
    assert [item.category for item in snapshot.records] == [
        "dual_signal",
        "dual_signal",
        "engagement_only",
        "risk_only",
    ]
    assert [item.engagement_rank for item in snapshot.records] == [1, 2, 3, 7]
    assert [item.risk_rank for item in snapshot.records] == [1, 2, None, 3]
    facts = snapshot.to_fact_set()
    assert facts.get("selectedEngagement").raw_value == 16_890
    assert facts.get("selectedEngagementShare").formatted_value == "64.5%"
    assert snapshot.query_id == "top-content.v1"


def test_top_content_sql_returns_valid_empty_snapshot() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(scoped_config("missing-topic")).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresTopContentRepository(connection).fetch(scope)

    assert snapshot.has_articles is False
    assert snapshot.article_count == 0
    assert snapshot.records == ()
    assert snapshot.to_evidence_set().records == ()
