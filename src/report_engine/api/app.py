"""FastAPI adapter for the durable M3 report-job manager."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, Protocol
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, Path as ApiPath, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from report_engine.api.jobs import JobRecord, JobStatus
from report_engine.api.manager import (
    InvalidIdempotencyKeyError,
    JobArtifactUnavailableError,
    JobArtifacts,
    JobIdempotencyConflictError,
    JobManager,
    JobManagerError,
    JobNotReadyError,
    JobQueueFullError,
    JobSubmission,
)
from report_engine.config import ReportConfig, SectionId
from report_engine.runtime import (
    build_real_narrator,
    build_report_service_factory,
)
from report_engine.settings import Settings
from report_engine.storage.archive import ZipArchivePublisher


class JobManagerPort(Protocol):
    def start(self) -> None: ...

    def close(self) -> None: ...

    def submit(
        self,
        config: ReportConfig,
        *,
        idempotency_key: str | None = None,
    ) -> JobSubmission: ...

    def get(self, task_id: UUID | str) -> JobRecord | None: ...

    def artifacts(self, task_id: UUID | str) -> JobArtifacts: ...


class _ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SubmissionResponse(_ApiModel):
    task_id: UUID = Field(alias="taskId")
    status: JobStatus
    status_url: str = Field(alias="statusUrl")


class ProgressResponse(_ApiModel):
    current_section: SectionId | None = Field(alias="currentSection")
    completed_sections: int = Field(alias="completedSections")
    total_sections: int = Field(alias="totalSections")


class DownloadsResponse(_ApiModel):
    pdf: str
    bundle: str


class JobErrorResponse(_ApiModel):
    code: str
    message: str


class StatusResponse(_ApiModel):
    task_id: UUID = Field(alias="taskId")
    status: JobStatus
    submitted_at: datetime = Field(alias="submittedAt")
    started_at: datetime | None = Field(alias="startedAt")
    finished_at: datetime | None = Field(alias="finishedAt")
    progress: ProgressResponse
    report_id: str | None = Field(alias="reportId")
    downloads: DownloadsResponse | None
    error: JobErrorResponse | None


class ErrorDetail(_ApiModel):
    code: str
    message: str
    details: dict[str, Any]
    request_id: UUID = Field(alias="requestId")


class ErrorResponse(_ApiModel):
    error: ErrorDetail


class ApiProblem(RuntimeError):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        self.headers = headers or {}


ERROR_404 = {404: {"model": ErrorResponse}}
ERROR_409 = {409: {"model": ErrorResponse}}
ERROR_422 = {422: {"model": ErrorResponse}}
ERROR_500 = {500: {"model": ErrorResponse}}


def create_app(manager: JobManagerPort) -> FastAPI:
    """Create the HTTP adapter around an injected job manager."""

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        manager.start()
        try:
            yield
        finally:
            await run_in_threadpool(manager.close)

    app = FastAPI(
        title="Opinion Report Engine API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.job_manager = manager

    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):
        request.state.request_id = uuid4()
        response = await call_next(request)
        response.headers["X-Request-ID"] = str(request.state.request_id)
        return response

    @app.exception_handler(ApiProblem)
    async def api_problem_handler(
        request: Request,
        problem: ApiProblem,
    ) -> JSONResponse:
        return _error_response(
            request,
            problem.status_code,
            problem.code,
            problem.message,
            details=problem.details,
            headers=problem.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        issues = [
            {
                "location": list(issue["loc"]),
                "type": issue["type"],
            }
            for issue in error.errors()
        ]
        return _error_response(
            request,
            422,
            "invalid_report_config",
            "Report configuration is invalid",
            details={"issues": issues},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request,
        error: StarletteHTTPException,
    ) -> JSONResponse:
        code = "not_found" if error.status_code == 404 else "http_error"
        message = "Resource was not found" if error.status_code == 404 else (
            "HTTP request could not be handled"
        )
        return _error_response(request, error.status_code, code, message)

    @app.exception_handler(Exception)
    async def unexpected_error_handler(
        request: Request,
        _: Exception,
    ) -> JSONResponse:
        return _error_response(
            request,
            500,
            "internal_error",
            "The service could not complete the request",
        )

    @app.post(
        "/reports",
        response_model=SubmissionResponse,
        status_code=202,
        responses={
            200: {"model": SubmissionResponse},
            409: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    async def submit_report(
        config: ReportConfig,
        idempotency_key: Annotated[
            str | None,
            Header(alias="Idempotency-Key"),
        ] = None,
    ) -> Response:
        try:
            submission = manager.submit(
                config,
                idempotency_key=idempotency_key,
            )
        except InvalidIdempotencyKeyError:
            raise ApiProblem(
                422,
                "invalid_idempotency_key",
                "Idempotency-Key is invalid",
            ) from None
        except JobIdempotencyConflictError:
            raise ApiProblem(
                409,
                "idempotency_conflict",
                "Idempotency-Key was already used with another config",
            ) from None
        except JobQueueFullError:
            raise ApiProblem(
                503,
                "queue_full",
                "Report job queue is full",
                headers={"Retry-After": "5"},
            ) from None
        except JobManagerError:
            raise ApiProblem(
                503,
                "service_unavailable",
                "Report task could not be accepted",
            ) from None

        record = submission.record
        status_url = f"/reports/{record.task_id}/status"
        response = SubmissionResponse(
            taskId=record.task_id,
            status=record.status,
            statusUrl=status_url,
        )
        status_code = (
            200
            if submission.replayed
            and record.status in {JobStatus.COMPLETED, JobStatus.FAILED}
            else 202
        )
        return JSONResponse(
            status_code=status_code,
            content=response.model_dump(mode="json", by_alias=True),
            headers={"Location": status_url},
        )

    @app.get(
        "/reports/{taskId}/status",
        response_model=StatusResponse,
        responses={**ERROR_404, **ERROR_422},
    )
    async def get_status(
        task_id: Annotated[str, ApiPath(alias="taskId")],
    ) -> StatusResponse:
        _, record = _require_task(manager, task_id)
        return _status_response(record)

    @app.get(
        "/reports/{taskId}/report.pdf",
        response_class=FileResponse,
        responses={
            200: {"content": {"application/pdf": {}}},
            **ERROR_404,
            **ERROR_409,
            **ERROR_422,
            **ERROR_500,
        },
    )
    async def download_pdf(
        task_id: Annotated[str, ApiPath(alias="taskId")],
    ) -> FileResponse:
        normalized, record = _require_task(manager, task_id)
        artifacts = _require_artifacts(manager, normalized, record)
        assert record.report_id is not None
        return FileResponse(
            artifacts.pdf,
            media_type="application/pdf",
            filename=f"{record.report_id}.pdf",
        )

    @app.get(
        "/reports/{taskId}/bundle.zip",
        response_class=FileResponse,
        responses={
            200: {"content": {"application/zip": {}}},
            **ERROR_404,
            **ERROR_409,
            **ERROR_422,
            **ERROR_500,
        },
    )
    async def download_bundle(
        task_id: Annotated[str, ApiPath(alias="taskId")],
    ) -> FileResponse:
        normalized, record = _require_task(manager, task_id)
        artifacts = _require_artifacts(manager, normalized, record)
        assert record.report_id is not None
        return FileResponse(
            artifacts.archive,
            media_type="application/zip",
            filename=f"{record.report_id}.zip",
        )

    return app


def create_runtime_app(output_root: Path = Path("out")) -> FastAPI:
    """Uvicorn application factory using only the fixed environment settings."""

    settings = Settings.from_environment(require_llm=True)
    service_factory = build_report_service_factory(
        settings,
        narrator_factory=lambda: build_real_narrator(settings),
    )
    manager = JobManager(
        output_root=output_root,
        service_factory=service_factory,
        archive_publisher=ZipArchivePublisher(),
        clock=lambda: datetime.now(UTC),
    )
    return create_app(manager)


def _require_task(
    manager: JobManagerPort,
    task_id: str,
) -> tuple[UUID, JobRecord]:
    try:
        normalized = UUID(task_id)
    except (TypeError, ValueError, AttributeError):
        raise ApiProblem(
            422,
            "invalid_task_id",
            "Report task ID must be a UUID",
        ) from None
    record = manager.get(normalized)
    if record is None:
        raise ApiProblem(404, "task_not_found", "Report task was not found")
    return normalized, record


def _require_artifacts(
    manager: JobManagerPort,
    task_id: UUID,
    record: JobRecord,
) -> JobArtifacts:
    if record.status is not JobStatus.COMPLETED:
        raise ApiProblem(409, "report_not_ready", "Report is not ready")
    try:
        return manager.artifacts(task_id)
    except JobNotReadyError:
        raise ApiProblem(409, "report_not_ready", "Report is not ready") from None
    except (JobArtifactUnavailableError, JobManagerError):
        raise ApiProblem(
            500,
            "artifact_unavailable",
            "Report artifact is unavailable",
        ) from None


def _status_response(record: JobRecord) -> StatusResponse:
    downloads = (
        DownloadsResponse(
            pdf=record.downloads.pdf,
            bundle=record.downloads.bundle,
        )
        if record.downloads is not None
        else None
    )
    error = (
        JobErrorResponse(code=record.error.code, message=record.error.message)
        if record.error is not None
        else None
    )
    return StatusResponse(
        taskId=record.task_id,
        status=record.status,
        submittedAt=record.submitted_at,
        startedAt=record.started_at,
        finishedAt=record.finished_at,
        progress=ProgressResponse(
            currentSection=record.progress.current_section,
            completedSections=record.progress.completed_sections,
            totalSections=record.progress.total_sections,
        ),
        reportId=record.report_id,
        downloads=downloads,
        error=error,
    )


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", uuid4())
    body = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            details=details or {},
            requestId=request_id,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json", by_alias=True),
        headers=headers,
    )
