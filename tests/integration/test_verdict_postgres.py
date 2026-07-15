from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresVerdictRepository
from report_engine.sections.registry import default_registry
from report_engine.sections.verdict import Momentum, RiskLevel
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def test_verdict_sql_matches_the_seeded_fixture_scope() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")

    raw = sample_config()
    raw["topic"] = {
        "tag": "bilibili-dislike",
        "displayName": "B站猜你不喜欢算法调整",
        "eventTitle": "B站猜你不喜欢算法调整事件",
    }
    plan = ReportPlanner(default_registry()).build(ReportConfig.model_validate(raw))

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresVerdictRepository(connection).fetch(plan.scope)

    assert snapshot.article_count == 12
    assert snapshot.negative_articles == 7
    assert snapshot.high_risk_negative_articles == 4
    assert snapshot.critical_negative_articles == 1
    assert snapshot.peak_day.isoformat() == "2026-03-20"
    assert snapshot.peak_article_count == 3
    assert snapshot.final_day_article_count == 1
    assert snapshot.risk_level is RiskLevel.HIGH
    assert snapshot.momentum is Momentum.COOLING
    assert snapshot.query_id == "verdict.v1"


def test_verdict_sql_returns_an_explicit_empty_snapshot() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")

    raw = sample_config()
    raw["topic"] = {
        "tag": "missing-topic",
        "displayName": "无数据话题",
        "eventTitle": "无数据事件",
    }
    plan = ReportPlanner(default_registry()).build(ReportConfig.model_validate(raw))

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresVerdictRepository(connection).fetch(plan.scope)

    assert snapshot.has_data is False
    assert snapshot.peak_day is None
    assert snapshot.risk_level is None
    assert snapshot.momentum is None
