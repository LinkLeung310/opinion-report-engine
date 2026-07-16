"""Validated report-job state and atomic local persistence for M3."""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Any, Literal, Self
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from report_engine.config import SectionId


NonEmptyString = Annotated[str, Field(strict=True, min_length=1)]
NonNegativeInteger = Annotated[int, Field(strict=True, ge=0)]
PositiveInteger = Annotated[int, Field(strict=True, ge=1)]
Sha256Hex = Annotated[
    str,
    Field(strict=True, pattern=r"^[0-9a-f]{64}$"),
]


class JobStoreError(RuntimeError):
    """A safe failure while reading or writing persisted task state."""


class JobTransitionError(ValueError):
    """An attempted report-job lifecycle transition is not valid."""


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class _PersistentModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class JobProgress(_PersistentModel):
    current_section: SectionId | None = Field(alias="currentSection")
    completed_sections: NonNegativeInteger = Field(alias="completedSections")
    total_sections: PositiveInteger = Field(alias="totalSections")

    @model_validator(mode="after")
    def validate_counts(self) -> Self:
        if self.completed_sections > self.total_sections:
            raise ValueError("completedSections cannot exceed totalSections")
        return self


class JobDownloads(_PersistentModel):
    pdf: NonEmptyString
    bundle: NonEmptyString


class JobError(_PersistentModel):
    code: Annotated[
        str,
        Field(strict=True, pattern=r"^[a-z][a-z0-9_]{0,63}$"),
    ]
    message: NonEmptyString


class JobRecord(_PersistentModel):
    """One durable task record with a validated, one-way lifecycle."""

    schema_version: Literal[1] = Field(default=1, alias="schemaVersion")
    task_id: UUID = Field(alias="taskId")
    status: JobStatus
    submitted_at: datetime = Field(alias="submittedAt")
    started_at: datetime | None = Field(default=None, alias="startedAt")
    finished_at: datetime | None = Field(default=None, alias="finishedAt")
    progress: JobProgress
    report_id: NonEmptyString | None = Field(default=None, alias="reportId")
    downloads: JobDownloads | None = None
    error: JobError | None = None
    idempotency_key_hash: Sha256Hex | None = Field(
        default=None,
        alias="idempotencyKeyHash",
    )
    request_fingerprint: Sha256Hex | None = Field(
        default=None,
        alias="requestFingerprint",
    )

    @field_validator("submitted_at", "started_at", "finished_at")
    @classmethod
    def validate_aware_time(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("job timestamps must include a UTC offset")
        return value.astimezone(UTC)

    @field_validator("report_id")
    @classmethod
    def validate_report_id(cls, value: str | None) -> str | None:
        if value is not None and (
            Path(value).name != value or value in {".", ".."}
        ):
            raise ValueError("invalid report ID")
        return value

    @model_validator(mode="after")
    def validate_lifecycle(self) -> Self:
        self._validate_time_order()

        if (self.idempotency_key_hash is None) != (
            self.request_fingerprint is None
        ):
            raise ValueError(
                "idempotencyKeyHash and requestFingerprint must appear together"
            )

        if self.status is JobStatus.QUEUED:
            if (
                self.started_at is not None
                or self.finished_at is not None
                or self.progress.current_section is not None
                or self.progress.completed_sections != 0
                or self.report_id is not None
                or self.downloads is not None
                or self.error is not None
            ):
                raise ValueError("queued job contains fields from a later state")
        elif self.status is JobStatus.RUNNING:
            if (
                self.started_at is None
                or self.finished_at is not None
                or self.report_id is not None
                or self.downloads is not None
                or self.error is not None
            ):
                raise ValueError("running job has inconsistent lifecycle fields")
        elif self.status is JobStatus.COMPLETED:
            if (
                self.started_at is None
                or self.finished_at is None
                or self.progress.current_section is not None
                or self.progress.completed_sections
                != self.progress.total_sections
                or self.report_id is None
                or self.downloads is None
                or self.error is not None
            ):
                raise ValueError("completed job has inconsistent lifecycle fields")
            self._validate_downloads()
        elif self.status is JobStatus.FAILED:
            if (
                self.finished_at is None
                or self.progress.current_section is not None
                or self.report_id is not None
                or self.downloads is not None
                or self.error is None
            ):
                raise ValueError("failed job has inconsistent lifecycle fields")
        return self

    def _validate_time_order(self) -> None:
        if self.started_at is not None and self.started_at < self.submitted_at:
            raise ValueError("startedAt cannot precede submittedAt")
        lower_bound = self.started_at or self.submitted_at
        if self.finished_at is not None and self.finished_at < lower_bound:
            raise ValueError("finishedAt cannot precede the job start")

    def _validate_downloads(self) -> None:
        expected_pdf = f"/reports/{self.task_id}/report.pdf"
        expected_bundle = f"/reports/{self.task_id}/bundle.zip"
        if self.downloads is None or (
            self.downloads.pdf != expected_pdf
            or self.downloads.bundle != expected_bundle
        ):
            raise ValueError("completed job contains invalid download URLs")

    @classmethod
    def queued(
        cls,
        *,
        task_id: UUID,
        submitted_at: datetime,
        total_sections: int,
        idempotency_key_hash: str | None = None,
        request_fingerprint: str | None = None,
    ) -> Self:
        return cls(
            taskId=task_id,
            status=JobStatus.QUEUED,
            submittedAt=submitted_at,
            progress=JobProgress(
                currentSection=None,
                completedSections=0,
                totalSections=total_sections,
            ),
            idempotencyKeyHash=idempotency_key_hash,
            requestFingerprint=request_fingerprint,
        )

    def mark_running(self, at: datetime) -> Self:
        self._require_status(JobStatus.QUEUED)
        return self._rebuild(status=JobStatus.RUNNING, startedAt=at)

    def update_progress(
        self,
        *,
        current_section: SectionId | None,
        completed_sections: int,
    ) -> Self:
        self._require_status(JobStatus.RUNNING)
        if completed_sections < self.progress.completed_sections:
            raise JobTransitionError("Job progress cannot regress")
        progress = {
            "currentSection": current_section,
            "completedSections": completed_sections,
            "totalSections": self.progress.total_sections,
        }
        return self._rebuild(progress=progress)

    def mark_completed(self, at: datetime, *, report_id: str) -> Self:
        self._require_status(JobStatus.RUNNING)
        if self.progress.completed_sections != self.progress.total_sections:
            raise JobTransitionError(
                "Job cannot complete before all sections are processed"
            )
        downloads = {
            "pdf": f"/reports/{self.task_id}/report.pdf",
            "bundle": f"/reports/{self.task_id}/bundle.zip",
        }
        return self._rebuild(
            status=JobStatus.COMPLETED,
            finishedAt=at,
            reportId=report_id,
            downloads=downloads,
        )

    def mark_failed(self, at: datetime, *, code: str, message: str) -> Self:
        if self.status in {JobStatus.COMPLETED, JobStatus.FAILED}:
            raise JobTransitionError("A terminal job cannot change state")
        return self._rebuild(
            status=JobStatus.FAILED,
            finishedAt=at,
            progress={
                "currentSection": None,
                "completedSections": self.progress.completed_sections,
                "totalSections": self.progress.total_sections,
            },
            reportId=None,
            downloads=None,
            error={"code": code, "message": message},
        )

    def validate_successor_of(self, previous: Self) -> None:
        immutable_fields = (
            self.task_id == previous.task_id
            and self.submitted_at == previous.submitted_at
            and self.progress.total_sections == previous.progress.total_sections
            and self.idempotency_key_hash == previous.idempotency_key_hash
            and self.request_fingerprint == previous.request_fingerprint
        )
        if not immutable_fields:
            raise JobTransitionError("Persisted job identity cannot change")
        if previous.status in {JobStatus.COMPLETED, JobStatus.FAILED}:
            raise JobTransitionError("A terminal job cannot change state")

        allowed = {
            JobStatus.QUEUED: {JobStatus.RUNNING, JobStatus.FAILED},
            JobStatus.RUNNING: {
                JobStatus.RUNNING,
                JobStatus.COMPLETED,
                JobStatus.FAILED,
            },
        }
        if self.status not in allowed[previous.status]:
            raise JobTransitionError(
                f"Invalid job transition from {previous.status.value} "
                f"to {self.status.value}"
            )
        if (
            previous.status is JobStatus.RUNNING
            and self.started_at != previous.started_at
        ):
            raise JobTransitionError("Persisted job start time cannot change")
        if self.progress.completed_sections < previous.progress.completed_sections:
            raise JobTransitionError("Persisted job progress cannot regress")

    def _require_status(self, expected: JobStatus) -> None:
        if self.status in {JobStatus.COMPLETED, JobStatus.FAILED}:
            raise JobTransitionError("A terminal job cannot change state")
        if self.status is not expected:
            raise JobTransitionError(
                f"Job must be {expected.value}, not {self.status.value}"
            )

    def _rebuild(self, **updates: Any) -> Self:
        raw = self.model_dump(mode="python", by_alias=True)
        raw.update(updates)
        try:
            return type(self).model_validate(raw)
        except ValidationError:
            raise JobTransitionError("Invalid job lifecycle transition") from None


class JobStore:
    """Persist task records below ``out/.report-jobs/tasks`` atomically."""

    _lock = threading.Lock()

    def __init__(
        self,
        output_root: Path,
        *,
        replace: Callable[[Path, Path], None] = os.replace,
    ) -> None:
        self._tasks_root = Path(output_root) / ".report-jobs" / "tasks"
        self._replace = replace

    def create(self, record: JobRecord) -> Path:
        with self._lock:
            self._ensure_tasks_root()
            if record.status is not JobStatus.QUEUED:
                raise JobTransitionError("A new persisted job must be queued")
            task_path = self._task_path(record.task_id)
            if task_path.exists() or task_path.is_symlink():
                raise JobStoreError("Report task already exists")
            self._write_atomically(task_path, record)
            return task_path

    def update(self, record: JobRecord) -> Path:
        with self._lock:
            self._validate_tasks_root(required=True)
            task_path = self._task_path(record.task_id)
            if not task_path.is_file() or task_path.is_symlink():
                raise JobStoreError("Report task does not exist")
            previous = self._read(task_path)
            record.validate_successor_of(previous)
            self._write_atomically(task_path, record)
            return task_path

    def get(self, task_id: UUID | str) -> JobRecord | None:
        normalized = self._normalize_task_id(task_id)
        with self._lock:
            if not self._validate_tasks_root(required=False):
                return None
            task_path = self._task_path(normalized)
            try:
                if not task_path.exists() and not task_path.is_symlink():
                    return None
            except OSError:
                raise JobStoreError("Could not read persisted report task") from None
            return self._read(task_path)

    def load_all(self) -> tuple[JobRecord, ...]:
        with self._lock:
            if not self._validate_tasks_root(required=False):
                return ()
            try:
                paths = sorted(self._tasks_root.glob("*.json"))
            except OSError:
                raise JobStoreError("Could not read persisted report tasks") from None

            records = [self._read(path) for path in paths]
            records.sort(key=lambda record: (record.submitted_at, str(record.task_id)))
            return tuple(records)

    @staticmethod
    def _normalize_task_id(task_id: UUID | str) -> UUID:
        try:
            return task_id if isinstance(task_id, UUID) else UUID(task_id)
        except (TypeError, ValueError, AttributeError):
            raise JobStoreError("Invalid report task ID") from None

    def _task_path(self, task_id: UUID) -> Path:
        return self._tasks_root / f"{task_id}.json"

    def _ensure_tasks_root(self) -> None:
        if self._tasks_root.is_symlink():
            raise JobStoreError("Invalid report task storage")
        try:
            self._tasks_root.mkdir(parents=True, exist_ok=True)
        except OSError:
            raise JobStoreError("Could not create report task storage") from None
        self._validate_tasks_root(required=True)

    def _validate_tasks_root(self, *, required: bool) -> bool:
        try:
            exists = self._tasks_root.exists()
            is_symlink = self._tasks_root.is_symlink()
            if not exists and not is_symlink:
                if required:
                    raise JobStoreError("Invalid report task storage")
                return False
            if is_symlink or not self._tasks_root.is_dir():
                raise JobStoreError("Invalid report task storage")
            return True
        except JobStoreError:
            raise
        except OSError:
            raise JobStoreError("Invalid report task storage") from None

    @staticmethod
    def _read(task_path: Path) -> JobRecord:
        try:
            if not task_path.is_file() or task_path.is_symlink():
                raise ValueError
            raw = json.loads(task_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError
            record = JobRecord.model_validate(raw)
            if task_path.name != f"{record.task_id}.json":
                raise ValueError
            return record
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            raise JobStoreError("Invalid persisted report task") from None

    def _write_atomically(self, task_path: Path, record: JobRecord) -> None:
        temporary = self._tasks_root / f".job-{uuid4().hex}.tmp"
        try:
            payload = record.model_dump(mode="json", by_alias=True)
            with temporary.open("x", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            self._replace(temporary, task_path)
        except (OSError, TypeError, ValueError):
            raise JobStoreError("Could not persist report task") from None
        finally:
            temporary.unlink(missing_ok=True)
