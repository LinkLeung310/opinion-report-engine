from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresMediaSocialRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def scoped_config(topic_tag: str) -> ReportConfig:
    raw = sample_config()
    raw["topic"] = {
        "tag": topic_tag,
        "displayName": "媒体社交测试",
        "eventTitle": "媒体社交测试事件",
    }
    return ReportConfig.model_validate(raw)


def test_media_social_sql_matches_the_seeded_fixture_scope() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(
        scoped_config("bilibili-dislike")
    ).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresMediaSocialRepository(connection).fetch(scope)

    assert [item.source_type for item in snapshot.rows] == ["media", "social"]
    assert [item.article_count for item in snapshot.rows] == [3, 9]
    assert [item.positive_articles for item in snapshot.rows] == [1, 1]
    assert [item.neutral_articles for item in snapshot.rows] == [1, 2]
    assert [item.negative_articles for item in snapshot.rows] == [1, 6]
    assert [item.platform_count for item in snapshot.rows] == [1, 3]
    facts = snapshot.to_fact_set()
    assert facts.get("mediaNegativeShare").formatted_value == "33.3%"
    assert facts.get("socialNegativeShare").formatted_value == "66.7%"
    assert (
        facts.get("socialMinusMediaNegativeShare").formatted_value
        == "+33.3 个百分点"
    )
    assert snapshot.query_id == "media-social.v1"


def test_media_social_sql_preserves_two_zero_rows_for_an_empty_scope() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(scoped_config("missing-topic")).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresMediaSocialRepository(connection).fetch(scope)

    assert [item.source_type for item in snapshot.rows] == ["media", "social"]
    assert [item.article_count for item in snapshot.rows] == [0, 0]
    assert snapshot.has_data is False
    assert snapshot.comparison_status == "no_data"
