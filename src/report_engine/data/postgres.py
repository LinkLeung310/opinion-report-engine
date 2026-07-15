"""PostgreSQL repositories backed by fixed, parameterized SQL."""

from __future__ import annotations

from importlib.resources import files
from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row

from report_engine.domain.scope import AnalysisScope
from report_engine.sections.metrics import MetricsSnapshot
from report_engine.sections.platforms import PlatformRow, PlatformsSnapshot
from report_engine.sections.severity import SeverityEvidenceRecord, SeveritySnapshot
from report_engine.sections.trend import DailyTrendPoint, TrendSnapshot
from report_engine.sections.verdict import VerdictSnapshot


METRICS_QUERY_ID = "metrics.v1"
METRICS_SQL = (
    files("report_engine.data.queries").joinpath("metrics.sql").read_text(encoding="utf-8")
)
VERDICT_QUERY_ID = "verdict.v1"
VERDICT_SQL = (
    files("report_engine.data.queries").joinpath("verdict.sql").read_text(encoding="utf-8")
)
TREND_QUERY_ID = "trend.v1"
TREND_SQL = (
    files("report_engine.data.queries").joinpath("trend.sql").read_text(encoding="utf-8")
)
PLATFORMS_QUERY_ID = "platforms.v1"
PLATFORMS_SQL = (
    files("report_engine.data.queries")
    .joinpath("platforms.sql")
    .read_text(encoding="utf-8")
)
SEVERITY_QUERY_ID = "severity.v1"
SEVERITY_SQL = (
    files("report_engine.data.queries")
    .joinpath("severity.sql")
    .read_text(encoding="utf-8")
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


class PostgresVerdictRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._connection = connection

    def fetch(self, scope: AnalysisScope) -> VerdictSnapshot:
        parameters = {
            "topic_tag": scope.topic_tag,
            "from_inclusive": scope.from_inclusive,
            "to_exclusive": scope.to_exclusive,
            "to_date": scope.to_date,
            "timezone_name": scope.timezone_name,
        }
        with self._connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(VERDICT_SQL, parameters)
            row = cursor.fetchone()

        if row is None:  # The aggregate query should always yield exactly one row.
            raise RuntimeError("verdict query returned no aggregate row")

        return VerdictSnapshot(
            article_count=row["article_count"],
            negative_articles=row["negative_articles"],
            high_risk_negative_articles=row["high_risk_negative_articles"],
            critical_negative_articles=row["critical_negative_articles"],
            peak_day=row["peak_day"],
            peak_article_count=row["peak_article_count"],
            final_day_article_count=row["final_day_article_count"],
            query_id=VERDICT_QUERY_ID,
        )


class PostgresTrendRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._connection = connection

    def fetch(self, scope: AnalysisScope) -> TrendSnapshot:
        parameters = {
            "topic_tag": scope.topic_tag,
            "from_date": scope.from_date,
            "to_date": scope.to_date,
            "from_inclusive": scope.from_inclusive,
            "to_exclusive": scope.to_exclusive,
            "timezone_name": scope.timezone_name,
        }
        with self._connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(TREND_SQL, parameters)
            rows = cursor.fetchall()

        return TrendSnapshot(
            points=tuple(
                DailyTrendPoint(
                    day=row["article_day"],
                    article_count=row["article_count"],
                    positive_articles=row["positive_articles"],
                    neutral_articles=row["neutral_articles"],
                    negative_articles=row["negative_articles"],
                )
                for row in rows
            ),
            query_id=TREND_QUERY_ID,
        )


class PostgresPlatformsRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._connection = connection

    def fetch(self, scope: AnalysisScope) -> PlatformsSnapshot:
        parameters = {
            "topic_tag": scope.topic_tag,
            "from_inclusive": scope.from_inclusive,
            "to_exclusive": scope.to_exclusive,
        }
        with self._connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(PLATFORMS_SQL, parameters)
            rows = cursor.fetchall()

        return PlatformsSnapshot(
            rows=tuple(
                PlatformRow(
                    platform=row["platform"],
                    article_count=row["article_count"],
                    positive_articles=row["positive_articles"],
                    neutral_articles=row["neutral_articles"],
                    negative_articles=row["negative_articles"],
                    likes=row["likes"],
                    comments=row["comments"],
                    shares=row["shares"],
                    favorites=row["favorites"],
                )
                for row in rows
            ),
            query_id=PLATFORMS_QUERY_ID,
        )


class PostgresSeverityRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._connection = connection

    def fetch(self, scope: AnalysisScope) -> SeveritySnapshot:
        parameters = {
            "topic_tag": scope.topic_tag,
            "from_inclusive": scope.from_inclusive,
            "to_exclusive": scope.to_exclusive,
        }
        with self._connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(SEVERITY_SQL, parameters)
            rows = cursor.fetchall()

        if not rows:
            return SeveritySnapshot(
                negative_articles=0,
                low_articles=0,
                medium_articles=0,
                high_articles=0,
                critical_articles=0,
                missing_severity_articles=0,
                score_1_articles=0,
                score_2_articles=0,
                score_3_articles=0,
                score_4_articles=0,
                score_5_articles=0,
                scored_negative_articles=0,
                missing_score_articles=0,
                average_negative_score=None,
                negative_engagement=0,
                high_critical_engagement=0,
                evidence_records=(),
                query_id=SEVERITY_QUERY_ID,
            )

        aggregate = rows[0]
        return SeveritySnapshot(
            negative_articles=aggregate["negative_articles"],
            low_articles=aggregate["low_articles"],
            medium_articles=aggregate["medium_articles"],
            high_articles=aggregate["high_articles"],
            critical_articles=aggregate["critical_articles"],
            missing_severity_articles=aggregate["missing_severity_articles"],
            score_1_articles=aggregate["score_1_articles"],
            score_2_articles=aggregate["score_2_articles"],
            score_3_articles=aggregate["score_3_articles"],
            score_4_articles=aggregate["score_4_articles"],
            score_5_articles=aggregate["score_5_articles"],
            scored_negative_articles=aggregate["scored_negative_articles"],
            missing_score_articles=aggregate["missing_score_articles"],
            average_negative_score=aggregate["average_negative_score"],
            negative_engagement=aggregate["negative_engagement"],
            high_critical_engagement=aggregate["high_critical_engagement"],
            evidence_records=tuple(
                SeverityEvidenceRecord(
                    external_id=row["external_id"],
                    title=row["title"],
                    summary=row["summary"],
                    platform=row["platform"],
                    published_at=row["published_at"],
                    sentiment=row["sentiment"],
                    negative_score=row["negative_score"],
                    severity=row["severity"],
                    total_engagement=row["total_engagement"],
                )
                for row in rows
            ),
            query_id=SEVERITY_QUERY_ID,
        )
