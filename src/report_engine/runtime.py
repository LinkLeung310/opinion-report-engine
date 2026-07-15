"""Composition root for the synchronous report engine."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from psycopg import Connection

from report_engine.application.planner import ReportPlanner
from report_engine.application.service import ReportApplicationService
from report_engine.charts.metrics import MetricsChartBuilder
from report_engine.charts.keywords import KeywordsChartBuilder
from report_engine.charts.platforms import PlatformsChartBuilder
from report_engine.charts.risk import RiskChartBuilder
from report_engine.charts.sentiment_evolution import SentimentEvolutionChartBuilder
from report_engine.charts.severity import SeverityChartBuilder
from report_engine.charts.trend import TrendChartBuilder
from report_engine.config import SectionId
from report_engine.data.postgres import (
    PostgresKeywordsRepository,
    PostgresMetricsRepository,
    PostgresPlatformsRepository,
    PostgresRiskRepository,
    PostgresSentimentEvolutionRepository,
    PostgresSeverityRepository,
    PostgresTrendRepository,
    PostgresVerdictRepository,
    PostgresViewpointsRepository,
)
from report_engine.llm.protocol import Narrator
from report_engine.rendering import ReportAssembler, ReportLabPdfRenderer
from report_engine.sections.metrics_runner import MetricsSectionRunner
from report_engine.sections.keywords_runner import KeywordsSectionRunner
from report_engine.sections.platforms_runner import PlatformsSectionRunner
from report_engine.sections.registry import default_registry
from report_engine.sections.risk_runner import RiskSectionRunner
from report_engine.sections.sentiment_evolution_runner import (
    SentimentEvolutionSectionRunner,
)
from report_engine.sections.severity_runner import SeveritySectionRunner
from report_engine.sections.trend_runner import TrendSectionRunner
from report_engine.sections.verdict_runner import VerdictSectionRunner
from report_engine.sections.viewpoints_runner import ViewpointsSectionRunner
from report_engine.storage.bundle import BundlePublisher


REPORT_TIMEZONE = ZoneInfo("Asia/Shanghai")


def build_report_service(
    connection: Connection,
    narrator: Narrator,
) -> ReportApplicationService:
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
    return ReportApplicationService(
        planner=ReportPlanner(default_registry()),
        section_runners={
            SectionId.VERDICT: verdict_runner,
            SectionId.METRICS: metrics_runner,
            SectionId.KEYWORDS: keywords_runner,
            SectionId.TREND: trend_runner,
            SectionId.VIEWPOINTS: viewpoints_runner,
            SectionId.PLATFORMS: platforms_runner,
            SectionId.SEVERITY: severity_runner,
            SectionId.RISK: risk_runner,
            SectionId.SENTIMENT_EVOLUTION: sentiment_evolution_runner,
        },
        assembler=ReportAssembler(),
        pdf_renderer=ReportLabPdfRenderer(),
        publisher=BundlePublisher(),
        clock=lambda: datetime.now(REPORT_TIMEZONE),
    )
