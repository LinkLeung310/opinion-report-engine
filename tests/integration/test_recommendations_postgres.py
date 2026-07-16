from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresRecommendationsRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def scoped_config(topic_tag: str) -> ReportConfig:
    raw = sample_config()
    raw["topic"] = {
        "tag": topic_tag,
        "displayName": "行动建议测试",
        "eventTitle": "行动建议测试事件",
    }
    return ReportConfig.model_validate(raw)


def test_recommendations_sql_matches_fixture_playbook() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(
        scoped_config("bilibili-dislike")
    ).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresRecommendationsRepository(connection).fetch(scope)

    assert snapshot.article_count == 12
    assert snapshot.negative_article_count == 7
    assert [action.action_id for action in snapshot.selected_actions] == [
        "triage_high_risk",
        "restore_user_control",
        "explain_change",
        "close_feedback_loop",
    ]
    assert snapshot.action_citation_ids == (
        "bili-007",
        "bili-005",
        "bili-003",
        "bili-007",
    )
    assert snapshot.to_evidence_set().record_ids == (
        "bili-007",
        "bili-005",
        "bili-003",
    )
    assert snapshot.to_fact_set().get("classifiedNegativeShare").formatted_value == "100.0%"
    assert snapshot.query_id == "recommendations.v1"


def test_recommendations_sql_returns_valid_empty_snapshot() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(scoped_config("missing-topic")).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresRecommendationsRepository(connection).fetch(scope)

    assert snapshot.article_count == 0
    assert snapshot.negative_article_count == 0
    assert snapshot.records == ()
    assert snapshot.selected_actions == ()
