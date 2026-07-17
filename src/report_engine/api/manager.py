"""Bounded in-process execution and recovery for report jobs."""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4

from report_engine.api.jobs import (
    JobRecord,
    JobStatus,
    JobStore,
    JobStoreError,
    JobTransitionError,
)
from report_engine.config import ReportConfig, SectionId
from report_engine.domain.results import ReportResult


class JobManagerError(RuntimeError):
    """A safe report-job manager failure."""


class JobQueueFullError(JobManagerError):
    """The bounded queued-plus-running capacity is exhausted."""


class JobIdempotencyConflictError(JobManagerError):
    """An idempotency key was reused for a different request."""


class InvalidIdempotencyKeyError(JobManagerError):
    """An idempotency key does not satisfy the public HTTP contract."""


class JobNotReadyError(JobManagerError):
    """A known task has not completed yet."""


class JobArtifactUnavailableError(JobManagerError):
    """A completed task's persisted artifact is unavailable."""


@dataclass(frozen=True)
class JobSubmission:
    record: JobRecord
    replayed: bool


@dataclass(frozen=True)
class JobArtifacts:
    pdf: Path
    archive: Path


class ReportGenerator(Protocol):
    def generate(
        self,
        config: ReportConfig,
        output_root: Path,
        *,
        progress_callback: Callable[[SectionId | None, int], None] | None = None,
    ) -> ReportResult: ...


class ArchivePublisher(Protocol):
    def publish(
        self,
        task_id: UUID,
        report_id: str,
        output_root: Path,
    ) -> Path: ...


class JobManager:
    """Run report services with bounded capacity and durable task status."""

    def __init__(
        self,
        *,
        output_root: Path,
        service_factory: Callable[
            [], AbstractContextManager[ReportGenerator]
        ],
        archive_publisher: ArchivePublisher,
        clock: Callable[[], datetime],
        task_id_factory: Callable[[], UUID] = uuid4,
        max_workers: int = 2,
        max_active_jobs: int = 16,
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be positive")
        if max_active_jobs < max_workers:
            raise ValueError("max_active_jobs must be at least max_workers")
        self._output_root = Path(output_root)
        self._service_factory = service_factory
        self._clock = clock
        self._task_id_factory = task_id_factory
        self._archive_publisher = archive_publisher
        self._max_workers = max_workers
        self._max_active_jobs = max_active_jobs
        self._store = JobStore(self._output_root)
        self._lock = threading.RLock()
        self._records: dict[UUID, JobRecord] = {}
        self._idempotency: dict[str, UUID] = {}
        self._active_jobs = 0
        self._executor: ThreadPoolExecutor | None = None
        self._accepting = False
        self._closed = False

    def start(self) -> None:
        with self._lock:
            if self._closed:
                raise JobManagerError("Report job manager cannot be restarted")
            if self._accepting:
                return
            try:
                records = self._store.load_all()
                recovered = self._recover_interrupted(records)
                idempotency = self._build_idempotency_index(recovered)
            except (JobStoreError, JobTransitionError, ValueError):
                raise JobManagerError("Could not start report job manager") from None

            self._records = {record.task_id: record for record in recovered}
            self._idempotency = idempotency
            self._executor = ThreadPoolExecutor(
                max_workers=self._max_workers,
                thread_name_prefix="report-job",
            )
            self._accepting = True

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._accepting = False
            executor = self._executor
        if executor is not None:
            executor.shutdown(wait=True, cancel_futures=False)
        with self._lock:
            self._closed = True
            self._executor = None

    def submit(
        self,
        config: ReportConfig,
        *,
        idempotency_key: str | None = None,
    ) -> JobSubmission:
        key_hash, fingerprint = self._idempotency_metadata(
            config,
            idempotency_key,
        )
        with self._lock:
            if not self._accepting or self._executor is None:
                raise JobManagerError("Report job manager is not accepting tasks")
            replay = self._find_replay(key_hash, fingerprint)
            if replay is not None:
                return JobSubmission(record=replay, replayed=True)
            if self._active_jobs >= self._max_active_jobs:
                raise JobQueueFullError("Report job queue is at capacity")

            task_id = self._task_id_factory()
            if task_id in self._records:
                raise JobManagerError("Could not allocate a unique report task ID")
            total_sections = sum(section.enabled for section in config.sections)
            record = JobRecord.queued(
                task_id=task_id,
                submitted_at=self._clock(),
                total_sections=total_sections,
                idempotency_key_hash=key_hash,
                request_fingerprint=fingerprint,
            )
            try:
                self._store.create(record)
                self._records[task_id] = record
                if key_hash is not None:
                    self._idempotency[key_hash] = task_id
                self._active_jobs += 1
                self._executor.submit(self._run_job, task_id, config)
            except (JobStoreError, RuntimeError):
                self._active_jobs = max(0, self._active_jobs - 1)
                raise JobManagerError("Could not accept report task") from None
            return JobSubmission(record=record, replayed=False)

    def get(self, task_id: UUID | str) -> JobRecord | None:
        normalized = self._normalize_task_id(task_id)
        with self._lock:
            return self._records.get(normalized)

    def artifacts(self, task_id: UUID | str) -> JobArtifacts:
        normalized = self._normalize_task_id(task_id)
        with self._lock:
            record = self._records.get(normalized)
        if record is None:
            raise JobManagerError("Report task was not found")
        if record.status is not JobStatus.COMPLETED:
            raise JobNotReadyError("Report task is not complete")
        if record.report_id is None:
            raise JobArtifactUnavailableError("Report artifact is unavailable")
        return self._resolve_artifacts(record)

    def _recover_interrupted(
        self,
        records: tuple[JobRecord, ...],
    ) -> tuple[JobRecord, ...]:
        recovered: list[JobRecord] = []
        for record in records:
            if record.status in {JobStatus.QUEUED, JobStatus.RUNNING}:
                record = record.mark_failed(
                    self._clock(),
                    code="service_restarted",
                    message=(
                        "Report generation was interrupted by a service restart"
                    ),
                )
                self._store.update(record)
            recovered.append(record)
        return tuple(recovered)

    @staticmethod
    def _build_idempotency_index(
        records: tuple[JobRecord, ...],
    ) -> dict[str, UUID]:
        index: dict[str, UUID] = {}
        for record in records:
            key_hash = record.idempotency_key_hash
            if key_hash is None:
                continue
            if key_hash in index:
                raise ValueError("duplicate idempotency hash")
            index[key_hash] = record.task_id
        return index

    def _find_replay(
        self,
        key_hash: str | None,
        fingerprint: str | None,
    ) -> JobRecord | None:
        if key_hash is None:
            return None
        existing_id = self._idempotency.get(key_hash)
        if existing_id is None:
            return None
        existing = self._records[existing_id]
        if existing.request_fingerprint != fingerprint:
            raise JobIdempotencyConflictError(
                "Idempotency key was already used with a different config"
            )
        return existing

    @staticmethod
    def _idempotency_metadata(
        config: ReportConfig,
        key: str | None,
    ) -> tuple[str | None, str | None]:
        if key is None:
            return None, None
        normalized = key.strip()
        if (
            not 1 <= len(normalized) <= 128
            or any(
                ord(character) < 0x21 or ord(character) > 0x7E
                for character in normalized
            )
        ):
            raise InvalidIdempotencyKeyError("Invalid idempotency key")
        key_hash = hashlib.sha256(normalized.encode("ascii")).hexdigest()
        canonical = json.dumps(
            config.model_dump(mode="json", by_alias=True),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        fingerprint = hashlib.sha256(canonical).hexdigest()
        return key_hash, fingerprint

    def _run_job(self, task_id: UUID, config: ReportConfig) -> None:
        try:
            self._replace_record(
                task_id,
                lambda record: record.mark_running(self._clock()),
            )
            with self._service_factory() as service:
                report = service.generate(
                    config,
                    self._output_root,
                    progress_callback=lambda section_id, completed: (
                        self._update_progress(task_id, section_id, completed)
                    ),
                )
            self._finish_progress(task_id)
            self._archive_publisher.publish(
                task_id,
                report.report_id,
                self._output_root,
            )
            self._replace_record(
                task_id,
                lambda record: record.mark_completed(
                    self._clock(),
                    report_id=report.report_id,
                ),
            )
        except Exception:
            self._fail_job(task_id)
        finally:
            with self._lock:
                self._active_jobs = max(0, self._active_jobs - 1)

    def _update_progress(
        self,
        task_id: UUID,
        section_id: SectionId | None,
        completed: int,
    ) -> None:
        self._replace_record(
            task_id,
            lambda record: record.update_progress(
                current_section=section_id,
                completed_sections=completed,
            ),
        )

    def _finish_progress(self, task_id: UUID) -> None:
        with self._lock:
            record = self._records[task_id]
        if (
            record.progress.current_section is not None
            or record.progress.completed_sections != record.progress.total_sections
        ):
            self._update_progress(
                task_id,
                None,
                record.progress.total_sections,
            )

    def _replace_record(
        self,
        task_id: UUID,
        update: Callable[[JobRecord], JobRecord],
    ) -> JobRecord:
        with self._lock:
            current = self._records[task_id]
            replacement = update(current)
            self._store.update(replacement)
            self._records[task_id] = replacement
            return replacement

    def _fail_job(self, task_id: UUID) -> None:
        try:
            self._replace_record(
                task_id,
                lambda record: record.mark_failed(
                    self._clock(),
                    code="generation_failed",
                    message="Report generation failed",
                ),
            )
        except (JobStoreError, JobTransitionError, KeyError):
            return

    @staticmethod
    def _normalize_task_id(task_id: UUID | str) -> UUID:
        try:
            return task_id if isinstance(task_id, UUID) else UUID(task_id)
        except (TypeError, ValueError, AttributeError):
            raise JobManagerError("Invalid report task ID") from None

    def _resolve_artifacts(self, record: JobRecord) -> JobArtifacts:
        assert record.report_id is not None
        bundle_candidate = self._output_root / record.report_id
        jobs_root = self._output_root / ".report-jobs"
        downloads = jobs_root / "downloads"
        archive_candidate = downloads / f"{record.task_id}.zip"
        try:
            root = self._output_root.resolve(strict=True)
            bundle = bundle_candidate.resolve(strict=True)
            resolved_jobs = jobs_root.resolve(strict=True)
            resolved_downloads = downloads.resolve(strict=True)
            archive = archive_candidate.resolve(strict=True)
        except OSError:
            raise JobArtifactUnavailableError(
                "Report artifact is unavailable"
            ) from None
        required = (
            bundle_candidate / "report.md",
            bundle_candidate / "report.pdf",
            bundle_candidate / "meta.json",
        )
        if (
            bundle_candidate.is_symlink()
            or bundle.parent != root
            or not bundle.is_dir()
            or not (bundle_candidate / "charts").is_dir()
            or (bundle_candidate / "charts").is_symlink()
            or any(not path.is_file() or path.is_symlink() for path in required)
            or jobs_root.is_symlink()
            or downloads.is_symlink()
            or archive_candidate.is_symlink()
            or resolved_jobs.parent != root
            or resolved_downloads.parent != resolved_jobs
            or archive.parent != resolved_downloads
            or not archive.is_file()
        ):
            raise JobArtifactUnavailableError("Report artifact is unavailable")
        return JobArtifacts(pdf=required[1].resolve(), archive=archive)
