from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresTimelineRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def scoped_config(topic_tag: str) -> ReportConfig:
    raw = sample_config()
    raw["topic"] = {
        "tag": topic_tag,
        "displayName": "时间线测试",
        "eventTitle": "时间线测试事件",
    }
    return ReportConfig.model_validate(raw)


def test_timeline_sql_matches_fixture_roles_and_auditable_facts() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(
        scoped_config("bilibili-dislike")
    ).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresTimelineRepository(connection).fetch(scope)

    assert snapshot.article_count == 12
    assert snapshot.peak_day.isoformat() == "2026-03-20"
    assert snapshot.peak_articles == 3
    assert snapshot.response_tagged_articles == 1
    assert [record.role for record in snapshot.role_records] == [
        "first_observed",
        "tagged_response",
        "peak_day_representative",
        "last_observed",
    ]
    assert [record.external_id for record in snapshot.role_records] == [
        "bili-001",
        "bili-006",
        "bili-007",
        "bili-012",
    ]
    assert snapshot.to_evidence_set().record_ids == (
        "bili-001",
        "bili-006",
        "bili-007",
        "bili-012",
    )
    assert snapshot.milestones[2].total_engagement == 10_020
    facts = snapshot.to_fact_set()
    assert facts.get("observedCalendarDays").raw_value == 7
    assert facts.get("milestone3PeakEngagement").formatted_value == "10,020"
    assert snapshot.query_id == "timeline.v1"


def test_timeline_sql_returns_valid_empty_snapshot() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(scoped_config("missing-topic")).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresTimelineRepository(connection).fetch(scope)

    assert snapshot.has_data is False
    assert snapshot.article_count == 0
    assert snapshot.peak_day is None
    assert snapshot.role_records == ()
    assert snapshot.to_evidence_set().records == ()
