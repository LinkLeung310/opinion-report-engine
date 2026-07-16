from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresSpreadPathRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def scoped_config(topic_tag: str) -> ReportConfig:
    raw = sample_config()
    raw["topic"] = {
        "tag": topic_tag,
        "displayName": "传播路径测试",
        "eventTitle": "传播路径测试事件",
    }
    return ReportConfig.model_validate(raw)


def test_spread_path_sql_matches_fixture_matrix_entries_and_facts() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(
        scoped_config("bilibili-dislike")
    ).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresSpreadPathRepository(connection).fetch(scope)

    assert snapshot.article_count == 12
    assert [item.platform for item in snapshot.display_platforms] == [
        "B站",
        "微博",
        "知乎",
        "新闻",
    ]
    assert [item.first_record.external_id for item in snapshot.display_platforms] == [
        "bili-001",
        "bili-002",
        "bili-003",
        "bili-004",
    ]
    assert [item.article_count for item in snapshot.display_platforms] == [4, 4, 1, 3]
    assert [item.negative_article_count for item in snapshot.display_platforms] == [2, 3, 1, 1]
    assert [item.active_days(scope.from_inclusive.tzinfo) for item in snapshot.display_platforms] == [4, 4, 1, 3]
    assert snapshot.first_observation_interval_hours == pytest.approx(32.5)
    assert snapshot.multi_platform_days == 4
    assert snapshot.max_daily_platforms == 3
    assert snapshot.max_daily_platform_days[0].isoformat() == "2026-03-20"
    assert snapshot.to_evidence_set().record_ids == (
        "bili-001",
        "bili-002",
        "bili-003",
        "bili-004",
    )
    facts = snapshot.to_fact_set()
    assert facts.get("firstObservationIntervalHours").formatted_value == "32.5"
    assert facts.get("platform1TotalEngagement").raw_value == 6_610
    assert facts.get("platform2TotalEngagement").raw_value == 15_715


def test_spread_path_sql_returns_valid_empty_snapshot() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(scoped_config("missing-topic")).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresSpreadPathRepository(connection).fetch(scope)

    assert snapshot.has_data is False
    assert snapshot.article_count == 0
    assert snapshot.platform_count == 0
    assert len(snapshot.calendar_days) == 7
    assert snapshot.to_fact_set().get("articles").raw_value == 0
