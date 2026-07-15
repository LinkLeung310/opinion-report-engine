from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresRiskRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def scoped_config(topic_tag: str) -> ReportConfig:
    raw = sample_config()
    raw["topic"] = {
        "tag": topic_tag,
        "displayName": "风险测试",
        "eventTitle": "风险测试事件",
    }
    return ReportConfig.model_validate(raw)


def test_risk_sql_matches_seeded_fixture_signals_and_index() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(
        scoped_config("bilibili-dislike")
    ).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresRiskRepository(connection).fetch(scope)

    assert snapshot.article_count == 12
    assert snapshot.negative_articles == 7
    assert snapshot.high_critical_negative_articles == 4
    assert snapshot.platform_count == 4
    assert snapshot.negative_platform_count == 4
    assert snapshot.calendar_days == 7
    assert snapshot.negative_active_days == 6
    assert snapshot.total_engagement == 26_170
    assert snapshot.negative_engagement == 20_620
    facts = snapshot.to_fact_set()
    assert facts.get("riskSignalIndex").formatted_value == "76.0%"
    assert facts.get("highSignalCount").raw_value == 3
    assert snapshot.query_id == "risk.v1"


def test_risk_sql_returns_empty_snapshot_for_an_empty_scope() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(scoped_config("missing-topic")).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresRiskRepository(connection).fetch(scope)

    assert snapshot.has_data is False
    assert snapshot.article_count == 0
    assert snapshot.calendar_days == 7
    assert snapshot.total_engagement == 0
