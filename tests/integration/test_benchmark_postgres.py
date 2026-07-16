from __future__ import annotations

import os
from decimal import Decimal

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresBenchmarkRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def fetch_snapshot(comparison_tag: str):
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    raw = sample_config()
    raw["topic"] = {
        "tag": "bilibili-dislike",
        "displayName": "B站猜你不喜欢算法调整",
        "eventTitle": "B站猜你不喜欢算法调整事件",
    }
    scope = ReportPlanner(default_registry()).build(
        ReportConfig.model_validate(raw)
    ).scope
    with psycopg.connect(dsn, connect_timeout=5) as connection:
        return PostgresBenchmarkRepository(connection).fetch(scope, comparison_tag)


def test_benchmark_sql_matches_independent_synthetic_history() -> None:
    snapshot = fetch_snapshot("legacy-feed-controls")
    facts = snapshot.to_fact_set()

    assert snapshot.query_id == "benchmark.v1"
    assert snapshot.current.article_count == 12
    assert snapshot.comparison.article_count == 8
    assert (snapshot.current.positive_articles, snapshot.current.neutral_articles,
            snapshot.current.negative_articles) == (2, 3, 7)
    assert (snapshot.comparison.positive_articles,
            snapshot.comparison.neutral_articles,
            snapshot.comparison.negative_articles) == (1, 2, 5)
    assert snapshot.current.platform_count == snapshot.comparison.platform_count == 4
    assert snapshot.current.high_critical_articles == 4
    assert snapshot.comparison.high_critical_articles == 3
    assert snapshot.current.total_engagement == 26170
    assert snapshot.comparison.total_engagement == 9500
    assert snapshot.comparison.daily_average == Decimal(8) / Decimal(7)
    assert snapshot.comparison.excluded_later_articles == 0
    assert facts.get("negativeShareDelta").formatted_value == "-4.2 个百分点"


def test_benchmark_sql_rejects_overlapping_tag_population() -> None:
    snapshot = fetch_snapshot("algorithm")

    assert snapshot.current.article_count == 12
    assert snapshot.comparison.article_count == 0
    assert snapshot.comparison.start_day is None
    assert snapshot.has_data is False
