"""Composition root for the synchronous report engine."""

from __future__ import annotations

from datetime import UTC, datetime

from psycopg import Connection

from report_engine.application.planner import ReportPlanner
from report_engine.application.service import ReportApplicationService
from report_engine.charts.metrics import MetricsChartBuilder
from report_engine.config import SectionId
from report_engine.data.postgres import (
    PostgresMetricsRepository,
    PostgresVerdictRepository,
)
from report_engine.llm.protocol import Narrator
from report_engine.rendering import ReportAssembler, ReportLabPdfRenderer
from report_engine.sections.metrics_runner import MetricsSectionRunner
from report_engine.sections.registry import default_registry
from report_engine.sections.verdict_runner import VerdictSectionRunner
from report_engine.storage.bundle import BundlePublisher


def build_report_service(
    connection: Connection,
    narrator: Narrator,
) -> ReportApplicationService:
    metrics_runner = MetricsSectionRunner(
        repository=PostgresMetricsRepository(connection),
        chart_builder=MetricsChartBuilder(),
        narrator=narrator,
    )
    verdict_runner = VerdictSectionRunner(
        repository=PostgresVerdictRepository(connection),
        narrator=narrator,
    )
    return ReportApplicationService(
        planner=ReportPlanner(default_registry()),
        section_runners={
            SectionId.VERDICT: verdict_runner,
            SectionId.METRICS: metrics_runner,
        },
        assembler=ReportAssembler(),
        pdf_renderer=ReportLabPdfRenderer(),
        publisher=BundlePublisher(),
        clock=lambda: datetime.now(UTC),
    )
