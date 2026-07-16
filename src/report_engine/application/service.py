"""Application service that owns one complete report-generation transaction."""

from __future__ import annotations

import re
import threading
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Protocol

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
from report_engine.presentation import failed_section_markdown
from report_engine.rendering.assembler import ReportAssembler


class SectionRunner(Protocol):
    def run(
        self,
        scope: AnalysisScope,
        language: Language,
        chart_directory: Path,
        section_input: Mapping[str, Any] | None = None,
    ) -> SectionResult: ...


class PdfRenderer(Protocol):
    def render(self, markdown: str, chart_directory: Path) -> bytes: ...


class BundlePublisherPort(Protocol):
    def publish(
        self,
        report: ReportResult,
        pdf_bytes: bytes,
        chart_sources: dict[str, Path],
        output_root: Path,
    ) -> Path: ...


class CatalogPublisherPort(Protocol):
    def publish(self, bundle_path: Path, output_root: Path) -> Path: ...


class ReportIdAllocator:
    _lock = threading.Lock()
    _reservations: set[tuple[Path, str]] = set()

    def allocate(self, config: ReportConfig, output_root: Path) -> str:
        safe_tag = re.sub(r"[^a-z0-9]+", "-", config.topic.tag.lower()).strip("-")
        base = f"{safe_tag or 'report'}-{config.date_range.to_date.isoformat()}"
        root = Path(output_root).resolve()
        with self._lock:
            version = 1
            while (
                (output_root / f"{base}-v{version}").exists()
                or (root, f"{base}-v{version}") in self._reservations
            ):
                version += 1
            report_id = f"{base}-v{version}"
            self._reservations.add((root, report_id))
            return report_id

    def release(self, report_id: str, output_root: Path) -> None:
        root = Path(output_root).resolve()
        with self._lock:
            self._reservations.discard((root, report_id))


class ReportApplicationService:
    def __init__(
        self,
        planner: ReportPlanner,
        section_runners: Mapping[SectionId, SectionRunner],
        assembler: ReportAssembler,
        pdf_renderer: PdfRenderer,
        publisher: BundlePublisherPort,
        catalog_publisher: CatalogPublisherPort,
        clock: Callable[[], datetime],
        id_allocator: ReportIdAllocator | None = None,
    ) -> None:
        self._planner = planner
        self._section_runners = dict(section_runners)
        self._assembler = assembler
        self._pdf_renderer = pdf_renderer
        self._publisher = publisher
        self._catalog_publisher = catalog_publisher
        self._clock = clock
        self._id_allocator = id_allocator or ReportIdAllocator()

    def generate(
        self,
        config: ReportConfig,
        output_root: Path,
        *,
        progress_callback: Callable[[SectionId | None, int], None] | None = None,
    ) -> ReportResult:
        plan = self._planner.build(config)
        report_id = self._id_allocator.allocate(config, output_root)

        try:
            with TemporaryDirectory(prefix=f"{report_id}-") as temporary:
                chart_directory = Path(temporary) / "charts"
                results: list[SectionResult] = []
                for completed, section in enumerate(plan.sections):
                    if progress_callback is not None:
                        progress_callback(section.id, completed)
                    results.append(
                        self._run_section(
                            section.id,
                            section.can_execute,
                            section.input_errors,
                            plan.scope,
                            config.language,
                            chart_directory,
                            section.input,
                        )
                    )
                if progress_callback is not None:
                    progress_callback(None, len(results))
                section_results = tuple(results)
                report = self._assembler.assemble(
                    config=config,
                    report_id=report_id,
                    sections=section_results,
                    generated_at=self._clock(),
                )
                pdf_bytes = self._pdf_renderer.render(
                    report.markdown,
                    chart_directory,
                )
                chart_sources = {
                    chart_name: chart_directory / chart_name
                    for result in section_results
                    for chart_name in result.charts
                }
                bundle_path = self._publisher.publish(
                    report=report,
                    pdf_bytes=pdf_bytes,
                    chart_sources=chart_sources,
                    output_root=output_root,
                )
                self._catalog_publisher.publish(bundle_path, output_root)
            return report
        finally:
            self._id_allocator.release(report_id, output_root)

    def _run_section(
        self,
        section_id: SectionId,
        can_execute: bool,
        input_errors: tuple[str, ...],
        scope: AnalysisScope,
        language: Language,
        chart_directory: Path,
        section_input: Mapping[str, Any],
    ) -> SectionResult:
        if not can_execute:
            return self._failed_section(
                section_id,
                FailureStage.INPUT,
                "; ".join(input_errors),
                language,
            )

        runner = self._section_runners.get(section_id)
        if runner is None:
            return self._failed_section(
                section_id,
                FailureStage.INPUT,
                "Section is not implemented",
                language,
            )

        try:
            return runner.run(scope, language, chart_directory, section_input)
        except Exception:
            return self._failed_section(
                section_id,
                FailureStage.CALCULATION,
                "Unexpected section execution failure",
                language,
            )

    @staticmethod
    def _failed_section(
        section_id: SectionId,
        stage: FailureStage,
        message: str,
        language: Language,
        facts: FactSet | None = None,
    ) -> SectionResult:
        return SectionResult(
            section_id=section_id,
            status=SectionStatus.FAILED,
            markdown=failed_section_markdown(section_id, language),
            facts=facts,
            failure=SectionFailure(stage=stage, message=message),
        )
