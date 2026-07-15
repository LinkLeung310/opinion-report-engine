from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresSeverityRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def scoped_config(topic_tag: str) -> ReportConfig:
    raw = sample_config()
    raw["topic"] = {
        "tag": topic_tag,
        "displayName": "严重程度测试",
        "eventTitle": "严重程度测试事件",
    }
    return ReportConfig.model_validate(raw)


def test_severity_sql_matches_seeded_facts_and_deterministic_evidence() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(
        scoped_config("bilibili-dislike")
    ).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresSeverityRepository(connection).fetch(scope)

    assert snapshot.negative_articles == 7
    assert (
        snapshot.low_articles,
        snapshot.medium_articles,
        snapshot.high_articles,
        snapshot.critical_articles,
    ) == (1, 2, 3, 1)
    assert (
        snapshot.score_1_articles,
        snapshot.score_2_articles,
        snapshot.score_3_articles,
        snapshot.score_4_articles,
        snapshot.score_5_articles,
    ) == (0, 2, 1, 3, 1)
    assert snapshot.negative_engagement == 20_620
    assert snapshot.high_critical_engagement == 16_115
    assert snapshot.to_evidence_set().record_ids == (
        "bili-007",
        "bili-005",
        "bili-003",
    )
    assert snapshot.to_fact_set().get("averageNegativeScore").formatted_value == "3.4"
    assert snapshot.to_fact_set().get("highCriticalRatio").formatted_value == "57.1%"
    assert snapshot.query_id == "severity.v1"


def test_severity_sql_returns_empty_snapshot_when_scope_has_no_negatives() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(scoped_config("missing-topic")).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresSeverityRepository(connection).fetch(scope)

    assert snapshot.has_data is False
    assert snapshot.negative_articles == 0
    assert snapshot.evidence_records == ()
    assert snapshot.average_negative_score is None
