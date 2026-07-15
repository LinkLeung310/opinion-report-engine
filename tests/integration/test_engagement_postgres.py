from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresEngagementRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def scoped_config(topic_tag: str) -> ReportConfig:
    raw = sample_config()
    raw["topic"] = {
        "tag": topic_tag,
        "displayName": "互动测试",
        "eventTitle": "互动测试事件",
    }
    return ReportConfig.model_validate(raw)


def test_engagement_sql_matches_fixture_totals_and_ranked_evidence() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(
        scoped_config("bilibili-dislike")
    ).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresEngagementRepository(connection).fetch(scope)

    assert snapshot.article_count == 12
    assert snapshot.positive_total_engagement_articles == 12
    assert snapshot.zero_engagement_articles == 0
    assert (snapshot.likes, snapshot.comments, snapshot.shares, snapshot.favorites) == (
        15_460,
        4_705,
        4_620,
        1_385,
    )
    assert snapshot.total_engagement == 26_170
    assert snapshot.leading_record_count == 1
    assert [record.external_id for record in snapshot.records] == [
        "bili-007",
        "bili-005",
        "bili-010",
        "bili-001",
        "bili-011",
    ]
    assert [record.total_engagement for record in snapshot.records] == [
        10_020,
        3_310,
        2_140,
        1_885,
        1_635,
    ]
    assert snapshot.to_evidence_set().record_ids == (
        "bili-007",
        "bili-005",
        "bili-010",
    )
    facts = snapshot.to_fact_set()
    assert facts.get("commentsAndSharesShare").formatted_value == "35.6%"
    assert facts.get("topRecordShare").formatted_value == "38.3%"
    assert facts.get("topThreeRecordsShare").formatted_value == "59.1%"
    assert snapshot.query_id == "engagement.v1"


def test_engagement_sql_returns_valid_empty_snapshot() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(scoped_config("missing-topic")).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresEngagementRepository(connection).fetch(scope)

    assert snapshot.has_articles is False
    assert snapshot.total_engagement == 0
    assert snapshot.leading_record_count == 0
    assert snapshot.records == ()
    assert snapshot.to_evidence_set().records == ()
