"""PostgreSQL repositories backed by fixed, parameterized SQL."""

from __future__ import annotations

from importlib.resources import files
from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row

from report_engine.domain.scope import AnalysisScope
from report_engine.sections.engagement import EngagementRecord, EngagementSnapshot
from report_engine.sections.metrics import MetricsSnapshot
from report_engine.sections.keywords import KeywordSourceRecord, KeywordsSnapshot
from report_engine.sections.media_social import MediaSocialRow, MediaSocialSnapshot
from report_engine.sections.platforms import PlatformRow, PlatformsSnapshot
from report_engine.sections.risk import RiskSnapshot
from report_engine.sections.severity import SeverityEvidenceRecord, SeveritySnapshot
from report_engine.sections.sentiment_evolution import (
    DailySentimentPoint,
    SentimentEvolutionSnapshot,
)
from report_engine.sections.trend import DailyTrendPoint, TrendSnapshot
from report_engine.sections.timeline import TimelineRoleRecord, TimelineSnapshot
from report_engine.sections.verdict import VerdictSnapshot
from report_engine.sections.viewpoints import (
    ViewpointEvidenceRecord,
    ViewpointsSnapshot,
)


METRICS_QUERY_ID = "metrics.v1"
METRICS_SQL = (
    files("report_engine.data.queries").joinpath("metrics.sql").read_text(encoding="utf-8")
)
ENGAGEMENT_QUERY_ID = "engagement.v1"
ENGAGEMENT_SQL = (
    files("report_engine.data.queries")
    .joinpath("engagement.sql")
    .read_text(encoding="utf-8")
)
KEYWORDS_QUERY_ID = "keywords.v1"
KEYWORDS_SQL = (
    files("report_engine.data.queries").joinpath("keywords.sql").read_text(encoding="utf-8")
)
MEDIA_SOCIAL_QUERY_ID = "media-social.v1"
MEDIA_SOCIAL_SQL = (
    files("report_engine.data.queries")
    .joinpath("media_social.sql")
    .read_text(encoding="utf-8")
)
VERDICT_QUERY_ID = "verdict.v1"
VERDICT_SQL = (
    files("report_engine.data.queries").joinpath("verdict.sql").read_text(encoding="utf-8")
)
TREND_QUERY_ID = "trend.v1"
TREND_SQL = (
    files("report_engine.data.queries").joinpath("trend.sql").read_text(encoding="utf-8")
)
SENTIMENT_EVOLUTION_QUERY_ID = "sentiment-evolution.v1"
SENTIMENT_EVOLUTION_SQL = (
    files("report_engine.data.queries")
    .joinpath("sentiment_evolution.sql")
    .read_text(encoding="utf-8")
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
RISK_QUERY_ID = "risk.v1"
RISK_SQL = (
    files("report_engine.data.queries").joinpath("risk.sql").read_text(encoding="utf-8")
)
VIEWPOINTS_QUERY_ID = "viewpoints.v1"
VIEWPOINTS_SQL = (
    files("report_engine.data.queries")
    .joinpath("viewpoints.sql")
    .read_text(encoding="utf-8")
)
TIMELINE_QUERY_ID = "timeline.v1"
TIMELINE_SQL = (
    files("report_engine.data.queries").joinpath("timeline.sql").read_text(encoding="utf-8")
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


class PostgresEngagementRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._connection = connection

    def fetch(self, scope: AnalysisScope) -> EngagementSnapshot:
        parameters = {
            "topic_tag": scope.topic_tag,
            "from_inclusive": scope.from_inclusive,
            "to_exclusive": scope.to_exclusive,
        }
        with self._connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(ENGAGEMENT_SQL, parameters)
            rows = cursor.fetchall()

        if not rows:
            raise RuntimeError("engagement query returned no aggregate row")

        aggregate = rows[0]
        return EngagementSnapshot(
            article_count=aggregate["article_count"],
            positive_total_engagement_articles=aggregate[
                "positive_total_engagement_articles"
            ],
            zero_engagement_articles=aggregate["zero_engagement_articles"],
            likes=aggregate["likes"],
            comments=aggregate["comments"],
            shares=aggregate["shares"],
            favorites=aggregate["favorites"],
            leading_record_count=aggregate["leading_record_count"],
            records=tuple(
                EngagementRecord(
                    external_id=row["external_id"],
                    title=row["title"],
                    summary=row["summary"],
                    platform=row["platform"],
                    published_at=row["published_at"],
                    sentiment=row["sentiment"],
                    likes=row["record_likes"],
                    comments=row["record_comments"],
                    shares=row["record_shares"],
                    favorites=row["record_favorites"],
                    engagement_rank=row["engagement_rank"],
                )
                for row in rows
                if row["external_id"] is not None
            ),
            query_id=ENGAGEMENT_QUERY_ID,
        )


class PostgresKeywordsRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._connection = connection

    def fetch(self, scope: AnalysisScope) -> KeywordsSnapshot:
        parameters = {
            "topic_tag": scope.topic_tag,
            "from_inclusive": scope.from_inclusive,
            "to_exclusive": scope.to_exclusive,
            "timezone_name": scope.timezone_name,
        }
        with self._connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(KEYWORDS_SQL, parameters)
            rows = cursor.fetchall()

        return KeywordsSnapshot(
            records=tuple(
                KeywordSourceRecord(
                    external_id=row["external_id"],
                    title=row["title"],
                    summary=row["summary"],
                    published_at=row["published_at"],
                    published_day=row["published_day"],
                    sentiment=row["sentiment"],
                )
                for row in rows
            ),
            from_date=scope.from_date,
            to_date=scope.to_date,
            query_id=KEYWORDS_QUERY_ID,
        )


class PostgresMediaSocialRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._connection = connection

    def fetch(self, scope: AnalysisScope) -> MediaSocialSnapshot:
        parameters = {
            "topic_tag": scope.topic_tag,
            "from_inclusive": scope.from_inclusive,
            "to_exclusive": scope.to_exclusive,
        }
        with self._connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(MEDIA_SOCIAL_SQL, parameters)
            rows = cursor.fetchall()

        if len(rows) != 2:
            raise RuntimeError("media-social query must return exactly two source rows")
        total_article_counts = {row["total_article_count"] for row in rows}
        total_negative_counts = {row["total_negative_articles"] for row in rows}
        if len(total_article_counts) != 1 or len(total_negative_counts) != 1:
            raise RuntimeError("media-social query returned inconsistent totals")

        snapshot = MediaSocialSnapshot(
            rows=tuple(
                MediaSocialRow(
                    source_type=row["source_type"],
                    article_count=row["article_count"],
                    positive_articles=row["positive_articles"],
                    neutral_articles=row["neutral_articles"],
                    negative_articles=row["negative_articles"],
                    platform_count=row["platform_count"],
                )
                for row in rows
            ),
            query_id=MEDIA_SOCIAL_QUERY_ID,
        )
        if snapshot.article_count != next(iter(total_article_counts)):
            raise RuntimeError("media-social article total does not match source rows")
        if snapshot.negative_articles != next(iter(total_negative_counts)):
            raise RuntimeError("media-social negative total does not match source rows")
        return snapshot


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


class PostgresSentimentEvolutionRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._connection = connection

    def fetch(self, scope: AnalysisScope) -> SentimentEvolutionSnapshot:
        parameters = {
            "topic_tag": scope.topic_tag,
            "from_date": scope.from_date,
            "to_date": scope.to_date,
            "from_inclusive": scope.from_inclusive,
            "to_exclusive": scope.to_exclusive,
            "timezone_name": scope.timezone_name,
        }
        with self._connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(SENTIMENT_EVOLUTION_SQL, parameters)
            rows = cursor.fetchall()

        return SentimentEvolutionSnapshot(
            points=tuple(
                DailySentimentPoint(
                    day=row["article_day"],
                    article_count=row["article_count"],
                    positive_articles=row["positive_articles"],
                    neutral_articles=row["neutral_articles"],
                    negative_articles=row["negative_articles"],
                )
                for row in rows
            ),
            query_id=SENTIMENT_EVOLUTION_QUERY_ID,
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


class PostgresRiskRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._connection = connection

    def fetch(self, scope: AnalysisScope) -> RiskSnapshot:
        parameters = {
            "topic_tag": scope.topic_tag,
            "from_inclusive": scope.from_inclusive,
            "to_exclusive": scope.to_exclusive,
            "timezone_name": scope.timezone_name,
        }
        with self._connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(RISK_SQL, parameters)
            row = cursor.fetchone()

        if row is None:  # The aggregate query should always yield exactly one row.
            raise RuntimeError("risk query returned no aggregate row")

        return RiskSnapshot(
            article_count=row["article_count"],
            negative_articles=row["negative_articles"],
            high_critical_negative_articles=row[
                "high_critical_negative_articles"
            ],
            platform_count=row["platform_count"],
            negative_platform_count=row["negative_platform_count"],
            calendar_days=(scope.to_date - scope.from_date).days + 1,
            negative_active_days=row["negative_active_days"],
            total_engagement=row["total_engagement"],
            negative_engagement=row["negative_engagement"],
            query_id=RISK_QUERY_ID,
        )


class PostgresViewpointsRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._connection = connection

    def fetch(self, scope: AnalysisScope) -> ViewpointsSnapshot:
        parameters = {
            "topic_tag": scope.topic_tag,
            "from_inclusive": scope.from_inclusive,
            "to_exclusive": scope.to_exclusive,
        }
        with self._connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(VIEWPOINTS_SQL, parameters)
            rows = cursor.fetchall()

        if not rows:
            return ViewpointsSnapshot(
                article_count=0,
                positive_articles=0,
                neutral_articles=0,
                negative_articles=0,
                evidence_records=(),
                query_id=VIEWPOINTS_QUERY_ID,
            )

        aggregate = rows[0]
        return ViewpointsSnapshot(
            article_count=aggregate["article_count"],
            positive_articles=aggregate["positive_articles"],
            neutral_articles=aggregate["neutral_articles"],
            negative_articles=aggregate["negative_articles"],
            evidence_records=tuple(
                ViewpointEvidenceRecord(
                    external_id=row["external_id"],
                    title=row["title"],
                    summary=row["summary"],
                    platform=row["platform"],
                    published_at=row["published_at"],
                    sentiment=row["sentiment"],
                    total_engagement=row["total_engagement"],
                    evidence_rank=row["evidence_rank"],
                )
                for row in rows
            ),
            query_id=VIEWPOINTS_QUERY_ID,
        )


class PostgresTimelineRepository:
    def __init__(self, connection: Connection[Any]) -> None:
        self._connection = connection

    def fetch(self, scope: AnalysisScope) -> TimelineSnapshot:
        parameters = {
            "topic_tag": scope.topic_tag,
            "from_inclusive": scope.from_inclusive,
            "to_exclusive": scope.to_exclusive,
            "timezone_name": scope.timezone_name,
        }
        with self._connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(TIMELINE_SQL, parameters)
            rows = cursor.fetchall()

        if not rows:
            return TimelineSnapshot(
                article_count=0,
                peak_day=None,
                peak_articles=0,
                response_tagged_articles=0,
                role_records=(),
                timezone_name=scope.timezone_name,
                query_id=TIMELINE_QUERY_ID,
            )

        aggregate_fields = (
            "article_count",
            "peak_day",
            "peak_articles",
            "response_tagged_articles",
        )
        for field in aggregate_fields:
            if len({row[field] for row in rows}) != 1:
                raise RuntimeError(f"timeline query returned inconsistent {field}")

        aggregate = rows[0]
        return TimelineSnapshot(
            article_count=aggregate["article_count"],
            peak_day=aggregate["peak_day"],
            peak_articles=aggregate["peak_articles"],
            response_tagged_articles=aggregate["response_tagged_articles"],
            role_records=tuple(
                TimelineRoleRecord(
                    role=row["role"],
                    external_id=row["external_id"],
                    title=row["title"],
                    summary=row["summary"],
                    platform=row["platform"],
                    published_at=row["published_at"],
                    published_day=row["published_day"],
                    sentiment=row["sentiment"],
                    total_engagement=row["total_engagement"],
                    response_tagged=row["response_tagged"],
                )
                for row in rows
            ),
            timezone_name=scope.timezone_name,
            query_id=TIMELINE_QUERY_ID,
        )
