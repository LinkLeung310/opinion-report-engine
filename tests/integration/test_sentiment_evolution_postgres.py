from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresSentimentEvolutionRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def scoped_config(topic_tag: str) -> ReportConfig:
    raw = sample_config()
    raw["topic"] = {
        "tag": topic_tag,
        "displayName": "情感演变测试",
        "eventTitle": "情感演变测试事件",
    }
    return ReportConfig.model_validate(raw)


def test_sentiment_evolution_sql_matches_seeded_phase_composition() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(
        scoped_config("bilibili-dislike")
    ).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresSentimentEvolutionRepository(connection).fetch(scope)

    assert [phase.calendar_days for phase in snapshot.phases] == [3, 2, 2]
    assert [phase.article_count for phase in snapshot.phases] == [6, 4, 2]
    assert [
        (
            phase.positive_articles,
            phase.neutral_articles,
            phase.negative_articles,
        )
        for phase in snapshot.phases
    ] == [(1, 2, 3), (1, 1, 2), (0, 0, 2)]
    assert snapshot.to_fact_set().get("negativeShareDelta").formatted_value == "+50.0 个百分点"
    assert snapshot.query_id == "sentiment-evolution.v1"


def test_sentiment_evolution_sql_keeps_empty_calendar_days() -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    scope = ReportPlanner(default_registry()).build(scoped_config("missing-topic")).scope

    with psycopg.connect(dsn, connect_timeout=5) as connection:
        snapshot = PostgresSentimentEvolutionRepository(connection).fetch(scope)

    assert snapshot.has_data is False
    assert len(snapshot.points) == 7
    assert [phase.article_count for phase in snapshot.phases] == [0, 0, 0]
