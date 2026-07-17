"""Publish one completed report bundle as an atomic task ZIP download."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from uuid import UUID, uuid4
from zipfile import ZIP_DEFLATED, ZipFile


class JobArchiveError(RuntimeError):
    """A safe failure while publishing a task's ZIP download."""


class ZipArchivePublisher:
    """Publish the fixed report bundle as one atomically visible ZIP."""

    def __init__(
        self,
        *,
        replace: Callable[[Path, Path], None] = os.replace,
    ) -> None:
        self._replace = replace

    def publish(
        self,
        task_id: UUID,
        report_id: str,
        output_root: Path,
    ) -> Path:
        files = self._bundle_files(report_id, Path(output_root))
        downloads = Path(output_root) / ".report-jobs" / "downloads"
        self._ensure_downloads(downloads, Path(output_root))
        target = downloads / f"{task_id}.zip"
        if target.exists() or target.is_symlink():
            raise JobArchiveError("Report task archive already exists")

        temporary = downloads / f".archive-{uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as raw_archive:
                with ZipFile(
                    raw_archive,
                    mode="w",
                    compression=ZIP_DEFLATED,
                ) as archive:
                    archive.writestr(f"{report_id}/", b"")
                    for source, relative in files:
                        archive.write(source, f"{report_id}/{relative.as_posix()}")
                    archive.writestr(f"{report_id}/charts/", b"")
                raw_archive.flush()
                os.fsync(raw_archive.fileno())
            self._replace(temporary, target)
        except (OSError, TypeError, ValueError):
            raise JobArchiveError("Could not publish report task archive") from None
        finally:
            temporary.unlink(missing_ok=True)
        return target

    @staticmethod
    def _bundle_files(
        report_id: str,
        output_root: Path,
    ) -> list[tuple[Path, Path]]:
        if not report_id or Path(report_id).name != report_id:
            raise JobArchiveError("Invalid published report bundle")
        bundle_candidate = output_root / report_id
        try:
            root = output_root.resolve(strict=True)
            bundle = bundle_candidate.resolve(strict=True)
        except OSError:
            raise JobArchiveError("Invalid published report bundle") from None
        if (
            bundle_candidate.is_symlink()
            or not bundle.is_dir()
            or bundle.parent != root
        ):
            raise JobArchiveError("Invalid published report bundle")

        files: list[tuple[Path, Path]] = []
        for name in ("report.md", "report.pdf", "meta.json"):
            source = bundle_candidate / name
            if not source.is_file() or source.is_symlink():
                raise JobArchiveError("Invalid published report bundle")
            files.append((source, Path(name)))

        charts = bundle_candidate / "charts"
        if not charts.is_dir() or charts.is_symlink():
            raise JobArchiveError("Invalid published report bundle")
        try:
            chart_files = sorted(charts.iterdir())
        except OSError:
            raise JobArchiveError("Invalid published report bundle") from None
        for chart in chart_files:
            if not chart.is_file() or chart.is_symlink() or chart.suffix != ".png":
                raise JobArchiveError("Invalid published report bundle")
            files.append((chart, Path("charts") / chart.name))
        return files

    @staticmethod
    def _ensure_downloads(downloads: Path, output_root: Path) -> None:
        jobs_root = output_root / ".report-jobs"
        if jobs_root.is_symlink() or downloads.is_symlink():
            raise JobArchiveError("Invalid report task archive storage")
        try:
            downloads.mkdir(parents=True, exist_ok=True)
        except OSError:
            raise JobArchiveError(
                "Could not create report task archive storage"
            ) from None
        try:
            root = output_root.resolve(strict=True)
            resolved_jobs = jobs_root.resolve(strict=True)
            resolved_downloads = downloads.resolve(strict=True)
        except OSError:
            raise JobArchiveError("Invalid report task archive storage") from None
        if (
            not downloads.is_dir()
            or jobs_root.is_symlink()
            or downloads.is_symlink()
            or resolved_jobs.parent != root
            or resolved_downloads.parent != resolved_jobs
        ):
            raise JobArchiveError("Invalid report task archive storage")
