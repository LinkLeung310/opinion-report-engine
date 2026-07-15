from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresMetricsRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def test_metrics_sql_matches_the_seeded_fixture_scope() -> None:
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
        snapshot = PostgresMetricsRepository(connection).fetch(plan.scope)

    assert snapshot.article_count == 12
    assert snapshot.positive_articles == 2
    assert snapshot.neutral_articles == 3
    assert snapshot.negative_articles == 7
    assert snapshot.platform_count == 4
    assert snapshot.total_engagement == 26_170
    assert snapshot.peak_day.isoformat() == "2026-03-20"
    assert snapshot.peak_article_count == 3
    assert snapshot.query_id == "metrics.v1"
