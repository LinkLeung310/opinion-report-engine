from __future__ import annotations

import os

import psycopg
import pytest

from report_engine.application.planner import ReportPlanner
from report_engine.config import ReportConfig
from report_engine.data.postgres import PostgresKeywordsRepository
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


pytestmark = pytest.mark.integration


def scope_for(tag: str):
    raw = sample_config()
    raw["topic"]["tag"] = tag
    return ReportPlanner(default_registry()).build(ReportConfig.model_validate(raw)).scope


@pytest.fixture
def connection():
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")
    with psycopg.connect(dsn) as database_connection:
        yield database_connection


def test_repository_extracts_auditable_fixture_phrases(connection) -> None:
    snapshot = PostgresKeywordsRepository(connection).fetch(
        scope_for("bilibili-dislike")
    )

    assert snapshot.query_id == "keywords.v1"
    assert snapshot.article_count == 12
    assert [phrase.text for phrase in snapshot.display_phrases] == [
        "不喜欢",
        "入口调整",
        "反馈机制",
        "控制感",
        "透明度",
        "负反馈入口",
    ]
    assert [phrase.document_count for phrase in snapshot.display_phrases] == [2] * 6
    assert [phrase.negative_documents for phrase in snapshot.display_phrases] == [
        2,
        1,
        2,
        2,
        2,
        2,
    ]
    assert not snapshot.emerging_phrases
    assert snapshot.leading_phrases == snapshot.display_phrases
    facts = snapshot.to_fact_set()
    assert facts.get("keyword2Text").source_record_ids == ("bili-001", "bili-004")
    assert facts.get("keyword2Coverage").formatted_value == "16.7%"
    assert facts.get("leadingPhraseCount").raw_value == 6


def test_repository_returns_empty_snapshot_for_unknown_topic(connection) -> None:
    snapshot = PostgresKeywordsRepository(connection).fetch(scope_for("missing-topic"))

    assert snapshot.article_count == 0
    assert snapshot.has_articles is False
    assert snapshot.has_data is False
    assert snapshot.display_phrases == ()
