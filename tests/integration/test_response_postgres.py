from __future__ import annotations

import os
from datetime import date
from decimal import Decimal

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresResponseRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def scoped_config(topic_tag: str) -> ReportConfig:
    raw = sample_config()
    raw["topic"] = {
        "tag": topic_tag,
        "displayName": "回应前后测试",
        "eventTitle": "回应前后测试事件",
    }
    return ReportConfig.model_validate(raw)


def fetch_snapshot(topic_tag: str):
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(scoped_config(topic_tag)).scope
    with psycopg.connect(dsn, connect_timeout=5) as connection:
        return PostgresResponseRepository(connection).fetch(
            scope,
            date(2026, 3, 19),
        )


def test_response_sql_matches_seeded_balanced_comparison() -> None:
    snapshot = fetch_snapshot("bilibili-dislike")
    facts = snapshot.to_fact_set()

    assert snapshot.query_id == "response.v1"
    assert snapshot.article_count == 12
    assert snapshot.window.window_days == 2
    assert (
        snapshot.pre.positive_articles,
        snapshot.pre.neutral_articles,
        snapshot.pre.negative_articles,
    ) == (0, 2, 2)
    assert (
        snapshot.post.positive_articles,
        snapshot.post.neutral_articles,
        snapshot.post.negative_articles,
    ) == (1, 1, 2)
    assert snapshot.pre.daily_average == snapshot.post.daily_average == Decimal(2)
    assert snapshot.response_day_articles == 2
    assert snapshot.response_day_official_tagged_articles == 1
    assert snapshot.outside_matched_windows_articles == 2
    assert facts.get("negativeShareDelta").formatted_value == "+0.0 个百分点"


def test_response_sql_returns_auditable_empty_snapshot() -> None:
    snapshot = fetch_snapshot("missing-topic")
    facts = snapshot.to_fact_set()

    assert snapshot.has_scoped_data is False
    assert snapshot.has_comparison_data is False
    assert snapshot.article_count == 0
    assert snapshot.window.window_days == 2
    assert facts.get("preNegativeShare").formatted_value == "不可用"
    assert facts.get("postNegativeShare").formatted_value == "不可用"
