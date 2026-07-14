"""Write the fixed output contract without exposing partial bundles."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

from report_engine.domain.results import ReportResult


class BundlePublisher:
    def publish(
        self,
        report: ReportResult,
        pdf_bytes: bytes,
        chart_sources: dict[str, Path],
        output_root: Path,
    ) -> Path:
        self._validate_component(report.report_id, "report ID")
        for chart_name in chart_sources:
            self._validate_component(chart_name, "chart filename")

        expected_charts = {
            chart for section in report.sections for chart in section.charts
        }
        if set(chart_sources) != expected_charts:
            raise ValueError("chart sources must match the report result exactly")
        if not pdf_bytes.startswith(b"%PDF-"):
            raise ValueError("report PDF does not have a valid PDF header")

        output_root.mkdir(parents=True, exist_ok=True)
        target = output_root / report.report_id
        if target.exists():
            raise FileExistsError(f"report bundle already exists: {report.report_id}")

        temporary = output_root / f".tmp-{report.report_id}-{uuid4().hex}"
        charts_directory = temporary / "charts"
        try:
            charts_directory.mkdir(parents=True)
            (temporary / "report.md").write_text(report.markdown, encoding="utf-8")
            (temporary / "meta.json").write_text(
                json.dumps(report.meta, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (temporary / "report.pdf").write_bytes(pdf_bytes)
            for chart_name, source in chart_sources.items():
                if not source.is_file():
                    raise FileNotFoundError(f"chart source is missing: {chart_name}")
                shutil.copyfile(source, charts_directory / chart_name)

            os.replace(temporary, target)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise

        return target

    @staticmethod
    def _validate_component(value: str, label: str) -> None:
        if not value or Path(value).name != value or value in {".", ".."}:
            raise ValueError(f"invalid {label}")
