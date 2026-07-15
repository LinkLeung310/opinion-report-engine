from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresPlatformsRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def scoped_config(topic_tag: str) -> ReportConfig:
    raw = sample_config()
    raw["topic"] = {
        "tag": topic_tag,
        "displayName": "平台测试",
        "eventTitle": "平台测试事件",
    }
    return ReportConfig.model_validate(raw)


def test_platforms_sql_matches_the_seeded_fixture_scope() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(
        scoped_config("bilibili-dislike")
    ).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresPlatformsRepository(connection).fetch(scope)

    assert [row.platform for row in snapshot.rows] == ["微博", "B站", "新闻", "知乎"]
    assert [row.article_count for row in snapshot.rows] == [4, 4, 3, 1]
    assert [row.negative_articles for row in snapshot.rows] == [3, 2, 1, 1]
    assert [row.total_engagement for row in snapshot.rows] == [15_715, 6_610, 2_425, 1_420]
    assert snapshot.to_fact_set().get("volumeLeaders").formatted_value == "微博、B站"
    assert snapshot.to_fact_set().get("negativeLeader").formatted_value == "微博"
    assert snapshot.query_id == "platforms.v1"


def test_platforms_sql_returns_an_empty_snapshot_for_an_empty_scope() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(scoped_config("missing-topic")).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresPlatformsRepository(connection).fetch(scope)

    assert snapshot.rows == ()
    assert snapshot.has_data is False
