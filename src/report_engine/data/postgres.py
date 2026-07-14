"""PostgreSQL repositories backed by fixed, parameterized SQL."""

from __future__ import annotations

from importlib.resources import files
from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row

from report_engine.domain.scope import AnalysisScope
from report_engine.sections.metrics import MetricsSnapshot


METRICS_QUERY_ID = "metrics.v1"
METRICS_SQL = (
    files("report_engine.data.queries").joinpath("metrics.sql").read_text(encoding="utf-8")
)


class PostgresMetricsRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._connection = connection

    def fetch(self, scope: AnalysisScope) -> MetricsSnapshot:
        parameters = {
            "topic_tag": scope.topic_tag,
            "from_inclusive": scope.from_inclusive,
            "to_exclusive": scope.to_exclusive,
            "timezone_name": scope.timezone_name,
        }
        with self._connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(METRICS_SQL, parameters)
            row = cursor.fetchone()

        if row is None:  # The aggregate query should always yield exactly one row.
            raise RuntimeError("metrics query returned no aggregate row")

        return MetricsSnapshot(
            article_count=row["article_count"],
            positive_articles=row["positive_articles"],
            neutral_articles=row["neutral_articles"],
            negative_articles=row["negative_articles"],
            platform_count=row["platform_count"],
            likes=row["likes"],
            comments=row["comments"],
            shares=row["shares"],
            favorites=row["favorites"],
            peak_day=row["peak_day"],
            peak_article_count=row["peak_article_count"],
            query_id=METRICS_QUERY_ID,
        )
