"""Composition root for the synchronous report engine."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager, contextmanager
from datetime import datetime
from typing import Protocol
from zoneinfo import ZoneInfo

import psycopg
from psycopg import Connection

from report_engine.application.planner import ReportPlanner
from report_engine.application.service import ReportApplicationService
from report_engine.charts.engagement import EngagementChartBuilder
from report_engine.charts.benchmark import BenchmarkChartBuilder
from report_engine.charts.metrics import MetricsChartBuilder
from report_engine.charts.keywords import KeywordsChartBuilder
from report_engine.charts.media_social import MediaSocialChartBuilder
from report_engine.charts.negative_themes import NegativeThemesChartBuilder
from report_engine.charts.platforms import PlatformsChartBuilder
from report_engine.charts.risk import RiskChartBuilder
from report_engine.charts.response import ResponseChartBuilder
from report_engine.charts.sentiment_evolution import SentimentEvolutionChartBuilder
from report_engine.charts.severity import SeverityChartBuilder
from report_engine.charts.spread_path import SpreadPathChartBuilder
from report_engine.charts.trend import TrendChartBuilder
from report_engine.charts.timeline import TimelineChartBuilder
from report_engine.charts.top_content import TopContentChartBuilder
from report_engine.config import SectionId
from report_engine.data.postgres import (
    PostgresBenchmarkRepository,
    PostgresBizImpactRepository,
    PostgresEngagementRepository,
    PostgresKeywordsRepository,
    PostgresMediaSocialRepository,
    PostgresMetricsRepository,
    PostgresNegativeThemesRepository,
    PostgresPlatformsRepository,
    PostgresRecommendationsRepository,
    PostgresRiskRepository,
    PostgresResponseRepository,
    PostgresSentimentEvolutionRepository,
    PostgresSeverityRepository,
    PostgresSpreadPathRepository,
    PostgresTrendRepository,
    PostgresTimelineRepository,
    PostgresTopContentRepository,
    PostgresVerdictRepository,
    PostgresViewpointsRepository,
)
from report_engine.llm.openai_compatible import OpenAICompatibleNarrator
from report_engine.llm.protocol import Narrator
from report_engine.rendering import ReportAssembler, ReportLabPdfRenderer
from report_engine.sections.engagement_runner import EngagementSectionRunner
from report_engine.sections.benchmark_runner import BenchmarkSectionRunner
from report_engine.sections.biz_impact_runner import BizImpactSectionRunner
from report_engine.sections.metrics_runner import MetricsSectionRunner
from report_engine.sections.keywords_runner import KeywordsSectionRunner
from report_engine.sections.media_social_runner import MediaSocialSectionRunner
from report_engine.sections.negative_themes_runner import NegativeThemesSectionRunner
from report_engine.sections.platforms_runner import PlatformsSectionRunner
from report_engine.sections.recommendations_runner import RecommendationsSectionRunner
from report_engine.sections.registry import default_registry
from report_engine.sections.risk_runner import RiskSectionRunner
from report_engine.sections.response_runner import ResponseSectionRunner
from report_engine.sections.sentiment_evolution_runner import (
    SentimentEvolutionSectionRunner,
)
from report_engine.sections.severity_runner import SeveritySectionRunner
from report_engine.sections.spread_path_runner import SpreadPathSectionRunner
from report_engine.sections.trend_runner import TrendSectionRunner
from report_engine.sections.timeline_runner import TimelineSectionRunner
from report_engine.sections.top_content_runner import TopContentSectionRunner
from report_engine.sections.verdict_runner import VerdictSectionRunner
from report_engine.sections.viewpoints_runner import ViewpointsSectionRunner
from report_engine.settings import Settings, SettingsError
from report_engine.storage import BundlePublisher, CatalogPublisher


REPORT_TIMEZONE = ZoneInfo("Asia/Shanghai")


class PostgresConnector(Protocol):
    def __call__(
        self,
        dsn: str,
        *,
        connect_timeout: int,
    ) -> AbstractContextManager[Connection]: ...


def build_real_narrator(settings: Settings) -> Narrator:
    """Build one real narrator without hiding missing or unsafe settings."""

    if (
        settings.llm_base_url is None
        or settings.llm_api_key is None
        or settings.llm_model is None
    ):
        raise SettingsError("LLM settings are required for real narration")
    try:
        return OpenAICompatibleNarrator(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )
    except ValueError as exc:
        raise SettingsError(f"Invalid LLM settings: {exc}") from exc


def build_report_service_factory(
    settings: Settings,
    *,
    narrator_factory: Callable[[], Narrator],
    connect: PostgresConnector = psycopg.connect,
) -> Callable[[], AbstractContextManager[ReportApplicationService]]:
    """Create per-task database, narrator, and application-service contexts."""

    @contextmanager
    def open_service():
        narrator = narrator_factory()
        with connect(
            settings.pg_dsn,
            connect_timeout=5,
        ) as connection:
            yield build_report_service(connection, narrator)

    return open_service


def build_report_service(
    connection: Connection,
    narrator: Narrator,
) -> ReportApplicationService:
    engagement_runner = EngagementSectionRunner(
        repository=PostgresEngagementRepository(connection),
        chart_builder=EngagementChartBuilder(),
        narrator=narrator,
    )
    metrics_runner = MetricsSectionRunner(
        repository=PostgresMetricsRepository(connection),
        chart_builder=MetricsChartBuilder(),
        narrator=narrator,
    )
    keywords_runner = KeywordsSectionRunner(
        repository=PostgresKeywordsRepository(connection),
        chart_builder=KeywordsChartBuilder(),
        narrator=narrator,
    )
    media_social_runner = MediaSocialSectionRunner(
        repository=PostgresMediaSocialRepository(connection),
        chart_builder=MediaSocialChartBuilder(),
        narrator=narrator,
    )
    verdict_runner = VerdictSectionRunner(
        repository=PostgresVerdictRepository(connection),
        narrator=narrator,
    )
    trend_runner = TrendSectionRunner(
        repository=PostgresTrendRepository(connection),
        chart_builder=TrendChartBuilder(),
        narrator=narrator,
    )
    viewpoints_runner = ViewpointsSectionRunner(
        repository=PostgresViewpointsRepository(connection),
        narrator=narrator,
    )
    platforms_runner = PlatformsSectionRunner(
        repository=PostgresPlatformsRepository(connection),
        chart_builder=PlatformsChartBuilder(),
        narrator=narrator,
    )
    severity_runner = SeveritySectionRunner(
        repository=PostgresSeverityRepository(connection),
        chart_builder=SeverityChartBuilder(),
        narrator=narrator,
    )
    risk_runner = RiskSectionRunner(
        repository=PostgresRiskRepository(connection),
        chart_builder=RiskChartBuilder(),
        narrator=narrator,
    )
    sentiment_evolution_runner = SentimentEvolutionSectionRunner(
        repository=PostgresSentimentEvolutionRepository(connection),
        chart_builder=SentimentEvolutionChartBuilder(),
        narrator=narrator,
    )
    timeline_runner = TimelineSectionRunner(
        repository=PostgresTimelineRepository(connection),
        chart_builder=TimelineChartBuilder(),
        narrator=narrator,
    )
    top_content_runner = TopContentSectionRunner(
        repository=PostgresTopContentRepository(connection),
        chart_builder=TopContentChartBuilder(),
        narrator=narrator,
    )
    negative_themes_runner = NegativeThemesSectionRunner(
        repository=PostgresNegativeThemesRepository(connection),
        chart_builder=NegativeThemesChartBuilder(),
        narrator=narrator,
    )
    spread_path_runner = SpreadPathSectionRunner(
        repository=PostgresSpreadPathRepository(connection),
        chart_builder=SpreadPathChartBuilder(),
        narrator=narrator,
    )
    response_runner = ResponseSectionRunner(
        repository=PostgresResponseRepository(connection),
        chart_builder=ResponseChartBuilder(),
        narrator=narrator,
    )
    benchmark_runner = BenchmarkSectionRunner(
        PostgresBenchmarkRepository(connection), BenchmarkChartBuilder(), narrator
    )
    biz_impact_runner = BizImpactSectionRunner(
        repository=PostgresBizImpactRepository(connection),
        narrator=narrator,
    )
    recommendations_runner = RecommendationsSectionRunner(
        repository=PostgresRecommendationsRepository(connection),
        narrator=narrator,
    )
    return ReportApplicationService(
        planner=ReportPlanner(default_registry()),
        section_runners={
            SectionId.VERDICT: verdict_runner,
            SectionId.METRICS: metrics_runner,
            SectionId.ENGAGEMENT: engagement_runner,
            SectionId.KEYWORDS: keywords_runner,
            SectionId.MEDIA_SOCIAL: media_social_runner,
            SectionId.TREND: trend_runner,
            SectionId.VIEWPOINTS: viewpoints_runner,
            SectionId.PLATFORMS: platforms_runner,
            SectionId.SEVERITY: severity_runner,
            SectionId.RISK: risk_runner,
            SectionId.SENTIMENT_EVOLUTION: sentiment_evolution_runner,
            SectionId.TIMELINE: timeline_runner,
            SectionId.TOP_CONTENT: top_content_runner,
            SectionId.NEGATIVE_THEMES: negative_themes_runner,
            SectionId.SPREAD_PATH: spread_path_runner,
            SectionId.RESPONSE: response_runner,
            SectionId.BENCHMARK: benchmark_runner,
            SectionId.BIZ_IMPACT: biz_impact_runner,
            SectionId.RECOMMENDATIONS: recommendations_runner,
        },
        assembler=ReportAssembler(),
        pdf_renderer=ReportLabPdfRenderer(),
        publisher=BundlePublisher(),
        catalog_publisher=CatalogPublisher(),
        clock=lambda: datetime.now(REPORT_TIMEZONE),
    )
