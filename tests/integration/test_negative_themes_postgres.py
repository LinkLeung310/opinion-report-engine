from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresNegativeThemesRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def scoped_config(topic_tag: str) -> ReportConfig:
    raw = sample_config()
    raw["topic"] = {
        "tag": topic_tag,
        "displayName": "负面议题测试",
        "eventTitle": "负面议题测试事件",
    }
    return ReportConfig.model_validate(raw)


def test_negative_themes_sql_matches_fixture_codebook_cross_tabs() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(
        scoped_config("bilibili-dislike")
    ).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresNegativeThemesRepository(connection).fetch(scope)

    assert snapshot.article_count == 12
    assert snapshot.negative_article_count == 7
    assert [theme.theme_id for theme in snapshot.display_themes] == [
        "user_agency",
        "transparency",
        "feedback_effectiveness",
    ]
    assert [theme.article_count for theme in snapshot.display_themes] == [5, 4, 3]
    assert [theme.concern_articles for theme in snapshot.display_themes] == [4, 2, 2]
    assert [theme.demand_articles for theme in snapshot.display_themes] == [2, 2, 1]
    assert [theme.high_critical_articles for theme in snapshot.display_themes] == [3, 2, 2]
    assert snapshot.representative_ids == ("bili-005", "bili-003", "bili-007")
    assert snapshot.unclassified_record_ids == ()
    assert snapshot.to_fact_set().get("theme1Share").formatted_value == "71.4%"
    assert snapshot.query_id == "negative-themes.v1"


def test_negative_themes_sql_returns_valid_empty_snapshot() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(scoped_config("missing-topic")).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresNegativeThemesRepository(connection).fetch(scope)

    assert snapshot.article_count == 0
    assert snapshot.negative_article_count == 0
    assert snapshot.records == ()
    assert snapshot.display_themes == ()
    assert snapshot.to_fact_set().get("negativeArticles").raw_value == 0
