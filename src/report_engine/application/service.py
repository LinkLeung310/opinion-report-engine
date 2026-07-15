"""Application service that owns one complete report-generation transaction."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.facts import FactSet
from report_engine.domain.results import (
    FailureStage,
    ReportResult,
    SectionFailure,
    SectionResult,
    SectionStatus,
)
from report_engine.domain.scope import AnalysisScope
from report_engine.rendering.assembler import ReportAssembler
from report_engine.storage.bundle import BundlePublisher


class SectionRunner(Protocol):
    def run(
        self,
        scope: AnalysisScope,
        language: Language,
        chart_directory: Path,
    ) -> SectionResult: ...


class PdfRenderer(Protocol):
    def render(self, markdown: str, chart_directory: Path) -> bytes: ...


class ReportIdAllocator:
    def allocate(self, config: ReportConfig, output_root: Path) -> str:
        safe_tag = re.sub(r"[^a-z0-9]+", "-", config.topic.tag.lower()).strip("-")
        base = f"{safe_tag or 'report'}-{config.date_range.to_date.isoformat()}"
        version = 1
        while (output_root / f"{base}-v{version}").exists():
            version += 1
        return f"{base}-v{version}"


class ReportApplicationService:
    def __init__(
        self,
        planner: ReportPlanner,
        section_runners: Mapping[SectionId, SectionRunner],
        assembler: ReportAssembler,
        pdf_renderer: PdfRenderer,
        publisher: BundlePublisher,
        clock: Callable[[], datetime],
        id_allocator: ReportIdAllocator | None = None,
    ) -> None:
        self._planner = planner
        self._section_runners = dict(section_runners)
        self._assembler = assembler
        self._pdf_renderer = pdf_renderer
        self._publisher = publisher
        self._clock = clock
        self._id_allocator = id_allocator or ReportIdAllocator()

    def generate(self, config: ReportConfig, output_root: Path) -> ReportResult:
        plan = self._planner.build(config)
        report_id = self._id_allocator.allocate(config, output_root)

        with TemporaryDirectory(prefix=f"{report_id}-") as temporary:
            chart_directory = Path(temporary) / "charts"
            results = tuple(
                self._run_section(
                    section.id,
                    section.can_execute,
                    section.input_errors,
                    plan.scope,
                    config.language,
                    chart_directory,
                )
                for section in plan.sections
            )
            report = self._assembler.assemble(
                config=config,
                report_id=report_id,
                sections=results,
                generated_at=self._clock(),
            )
            pdf_bytes = self._pdf_renderer.render(report.markdown, chart_directory)
            chart_sources = {
                chart_name: chart_directory / chart_name
                for result in results
                for chart_name in result.charts
            }
            self._publisher.publish(
                report=report,
                pdf_bytes=pdf_bytes,
                chart_sources=chart_sources,
                output_root=output_root,
            )
        return report

    def _run_section(
        self,
        section_id: SectionId,
        can_execute: bool,
        input_errors: tuple[str, ...],
        scope: AnalysisScope,
        language: Language,
        chart_directory: Path,
    ) -> SectionResult:
        if not can_execute:
            return self._failed_section(
                section_id,
                FailureStage.INPUT,
                "; ".join(input_errors),
            )

        runner = self._section_runners.get(section_id)
        if runner is None:
            return self._failed_section(
                section_id,
                FailureStage.INPUT,
                "Section is not implemented",
            )

        try:
            return runner.run(scope, language, chart_directory)
        except Exception:
            return self._failed_section(
                section_id,
                FailureStage.CALCULATION,
                "Unexpected section execution failure",
            )

    @staticmethod
    def _failed_section(
        section_id: SectionId,
        stage: FailureStage,
        message: str,
        facts: FactSet | None = None,
    ) -> SectionResult:
        return SectionResult(
            section_id=section_id,
            status=SectionStatus.FAILED,
            markdown=f"## {section_id.value}\n\n本章节生成失败，请稍后重试。",
            facts=facts,
            failure=SectionFailure(stage=stage, message=message),
        )
