from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresViewpointsRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def scoped_config(topic_tag: str) -> ReportConfig:
    raw = sample_config()
    raw["topic"] = {
        "tag": topic_tag,
        "displayName": "观点测试",
        "eventTitle": "观点测试事件",
    }
    return ReportConfig.model_validate(raw)


def test_viewpoints_sql_matches_counts_and_cross_platform_evidence() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(
        scoped_config("bilibili-dislike")
    ).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresViewpointsRepository(connection).fetch(scope)

    assert (
        snapshot.negative_articles,
        snapshot.neutral_articles,
        snapshot.positive_articles,
    ) == (7, 3, 2)
    assert snapshot.to_evidence_set().record_ids == (
        "bili-007",
        "bili-001",
        "bili-008",
        "bili-002",
        "bili-010",
        "bili-006",
    )
    assert [record.platform for record in snapshot.evidence_records] == [
        "微博",
        "B站",
        "B站",
        "微博",
        "B站",
        "新闻",
    ]
    assert snapshot.to_fact_set().get("negativeShare").formatted_value == "58.3%"
    assert snapshot.query_id == "viewpoints.v1"


def test_viewpoints_sql_returns_empty_snapshot_for_an_empty_scope() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(scoped_config("missing-topic")).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresViewpointsRepository(connection).fetch(scope)

    assert snapshot.has_data is False
    assert snapshot.article_count == 0
    assert snapshot.evidence_records == ()
