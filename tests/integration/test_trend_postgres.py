from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresTrendRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def scoped_config(topic_tag: str) -> ReportConfig:
    raw = sample_config()
    raw["topic"] = {
        "tag": topic_tag,
        "displayName": "趋势测试",
        "eventTitle": "趋势测试事件",
    }
    return ReportConfig.model_validate(raw)


def test_trend_sql_matches_every_seeded_fixture_day() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(
        scoped_config("bilibili-dislike")
    ).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresTrendRepository(connection).fetch(scope)

    assert [point.article_count for point in snapshot.points] == [2, 2, 2, 3, 1, 1, 1]
    assert [point.negative_articles for point in snapshot.points] == [1, 1, 1, 2, 0, 1, 1]
    assert snapshot.article_count == 12
    assert snapshot.active_days == 7
    assert snapshot.peak.day.isoformat() == "2026-03-20"
    assert snapshot.to_fact_set().get("peakShare").formatted_value == "25.0%"
    assert snapshot.to_fact_set().get("finalVsPeakRatio").formatted_value == "33.3%"


def test_trend_sql_returns_explicit_zero_rows_for_an_empty_scope() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(scoped_config("missing-topic")).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresTrendRepository(connection).fetch(scope)

    assert len(snapshot.points) == 7
    assert all(point.article_count == 0 for point in snapshot.points)
    assert snapshot.has_data is False
