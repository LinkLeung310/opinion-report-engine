from __future__ import annotations

import json
import threading
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID
from zipfile import ZipFile

from fastapi.testclient import TestClient

from report_engine.api.app import create_app
from report_engine.api.manager import JobManager
from report_engine.storage.archive import ZipArchivePublisher
from tests.test_config import sample_config


NOW = datetime(2026, 7, 17, 8, 0, tzinfo=UTC)
TASK_IDS = (
    UUID("4f7f7f38-a88f-4f70-b558-4798d0acef91"),
    UUID("82a4dcf7-181a-4c36-b871-ec7a14ab0d8a"),
    UUID("b933bfa7-679d-49aa-b5c2-c28a8fb9ca2a"),
)


def _raw_config(tag: str = "bilibili-dislike") -> dict:
    raw = sample_config()
    raw["topic"]["tag"] = tag
    raw["sections"] = [{"id": "metrics", "enabled": True}]
    return raw


class _Service:
    def __init__(self, resource_id: int, gate: threading.Event | None) -> None:
        self._resource_id = resource_id
        self._gate = gate

    def generate(self, config, output_root, *, progress_callback=None):
        if progress_callback is not None:
            progress_callback(config.sections[0].id, 0)
        if self._gate is not None and not self._gate.wait(timeout=5):
            raise RuntimeError("test gate timed out")
        report_id = f"{config.topic.tag}-v{self._resource_id}"
        bundle = output_root / report_id
        charts = bundle / "charts"
        charts.mkdir(parents=True)
        (bundle / "report.md").write_text("# Report\n", encoding="utf-8")
        (bundle / "report.pdf").write_bytes(b"%PDF-1.4\nAPI test\n")
        (bundle / "meta.json").write_text(
            json.dumps({"id": report_id}),
            encoding="utf-8",
        )
        (charts / "sentiment.png").write_bytes(b"PNG")
        if progress_callback is not None:
            progress_callback(None, 1)
        return SimpleNamespace(report_id=report_id)


class _ServiceFactory:
    def __init__(self, gate: threading.Event | None = None) -> None:
        self._gate = gate
        self._lock = threading.Lock()
        self.created: list[int] = []
        self.closed: list[int] = []

    @contextmanager
    def __call__(self):
        with self._lock:
            resource_id = len(self.created) + 1
            self.created.append(resource_id)
        try:
            yield _Service(resource_id, self._gate)
        finally:
            with self._lock:
                self.closed.append(resource_id)


def _manager(
    output_root: Path,
    factory: _ServiceFactory,
    *,
    max_workers: int = 2,
    max_active_jobs: int = 16,
) -> JobManager:
    task_ids = iter(TASK_IDS)
    return JobManager(
        output_root=output_root,
        service_factory=factory,
        archive_publisher=ZipArchivePublisher(),
        clock=lambda: NOW,
        task_id_factory=lambda: next(task_ids),
        max_workers=max_workers,
        max_active_jobs=max_active_jobs,
    )


def _wait_for_terminal(client: TestClient, task_id: str) -> dict:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        response = client.get(f"/reports/{task_id}/status")
        assert response.status_code == 200
        body = response.json()
        if body["status"] in {"completed", "failed"}:
            return body
        time.sleep(0.01)
    raise AssertionError("API task did not reach a terminal state")


def _assert_request_id(response) -> str:
    request_id = response.headers["X-Request-ID"]
    UUID(request_id)
    return request_id


def test_submit_status_and_download_complete_bundle(tmp_path: Path) -> None:
    factory = _ServiceFactory()
    manager = _manager(tmp_path / "out", factory)

    with TestClient(create_app(manager)) as client:
        submitted = client.post("/reports", json=_raw_config())

        assert submitted.status_code == 202
        assert submitted.headers["Location"] == (
            f"/reports/{TASK_IDS[0]}/status"
        )
        _assert_request_id(submitted)
        assert submitted.json() == {
            "taskId": str(TASK_IDS[0]),
            "status": "queued",
            "statusUrl": f"/reports/{TASK_IDS[0]}/status",
        }

        status = _wait_for_terminal(client, str(TASK_IDS[0]))
        assert set(status) == {
            "taskId",
            "status",
            "submittedAt",
            "startedAt",
            "finishedAt",
            "progress",
            "reportId",
            "downloads",
            "error",
        }
        assert status["status"] == "completed"
        assert status["progress"] == {
            "currentSection": None,
            "completedSections": 1,
            "totalSections": 1,
        }
        assert status["downloads"] == {
            "pdf": f"/reports/{TASK_IDS[0]}/report.pdf",
            "bundle": f"/reports/{TASK_IDS[0]}/bundle.zip",
        }

        pdf = client.get(status["downloads"]["pdf"])
        archive = client.get(status["downloads"]["bundle"])
        assert pdf.status_code == 200
        assert pdf.headers["content-type"] == "application/pdf"
        assert status["reportId"] in pdf.headers["content-disposition"]
        assert pdf.content.startswith(b"%PDF")
        assert archive.status_code == 200
        assert archive.headers["content-type"] == "application/zip"
        assert status["reportId"] in archive.headers["content-disposition"]

        archive_path = tmp_path / "download.zip"
        archive_path.write_bytes(archive.content)
        with ZipFile(archive_path) as handle:
            assert set(handle.namelist()) == {
                f"{status['reportId']}/",
                f"{status['reportId']}/report.md",
                f"{status['reportId']}/report.pdf",
                f"{status['reportId']}/meta.json",
                f"{status['reportId']}/charts/",
                f"{status['reportId']}/charts/sentiment.png",
            }

    assert factory.created == [1]
    assert factory.closed == [1]


def test_http_errors_are_coded_safe_and_retryable(tmp_path: Path) -> None:
    gate = threading.Event()
    manager = _manager(
        tmp_path / "out",
        _ServiceFactory(gate),
        max_workers=1,
        max_active_jobs=1,
    )

    with TestClient(create_app(manager)) as client:
        invalid_config = _raw_config()
        invalid_config["privateSecret"] = "must-not-be-reflected"
        invalid = client.post("/reports", json=invalid_config)
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "invalid_report_config"
        assert "must-not-be-reflected" not in invalid.text
        assert invalid.json()["error"]["requestId"] == _assert_request_id(
            invalid
        )

        invalid_key = client.post(
            "/reports",
            json=_raw_config(),
            headers={"Idempotency-Key": "contains space"},
        )
        assert invalid_key.status_code == 422
        assert invalid_key.json()["error"]["code"] == (
            "invalid_idempotency_key"
        )

        first = client.post(
            "/reports",
            json=_raw_config(),
            headers={"Idempotency-Key": "retry-123"},
        )
        replay = client.post(
            "/reports",
            json=_raw_config(),
            headers={"Idempotency-Key": "retry-123"},
        )
        conflict = client.post(
            "/reports",
            json=_raw_config("another-topic"),
            headers={"Idempotency-Key": "retry-123"},
        )
        full = client.post("/reports", json=_raw_config("third-topic"))

        assert first.status_code == 202
        assert replay.status_code == 202
        assert replay.json()["taskId"] == first.json()["taskId"]
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "idempotency_conflict"
        assert full.status_code == 503
        assert full.headers["Retry-After"] == "5"
        assert full.json()["error"]["code"] == "queue_full"

        not_ready = client.get(
            f"/reports/{first.json()['taskId']}/report.pdf"
        )
        assert not_ready.status_code == 409
        assert not_ready.json()["error"]["code"] == "report_not_ready"

        invalid_id = client.get("/reports/not-a-uuid/status")
        unknown = client.get(f"/reports/{TASK_IDS[2]}/status")
        assert invalid_id.status_code == 422
        assert invalid_id.json()["error"]["code"] == "invalid_task_id"
        assert unknown.status_code == 404
        assert unknown.json()["error"]["code"] == "task_not_found"

        gate.set()
        completed = _wait_for_terminal(client, first.json()["taskId"])
        assert completed["status"] == "completed"
        terminal_replay = client.post(
            "/reports",
            json=_raw_config(),
            headers={"Idempotency-Key": "retry-123"},
        )
        assert terminal_replay.status_code == 200
        assert terminal_replay.json()["status"] == "completed"


def test_missing_completed_artifact_returns_safe_500(tmp_path: Path) -> None:
    output_root = tmp_path / "out"
    manager = _manager(output_root, _ServiceFactory())

    with TestClient(create_app(manager)) as client:
        submitted = client.post("/reports", json=_raw_config())
        status = _wait_for_terminal(client, submitted.json()["taskId"])
        (output_root / status["reportId"] / "report.pdf").unlink()

        response = client.get(status["downloads"]["pdf"])
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "artifact_unavailable"
        assert str(output_root) not in response.text


def test_openapi_matches_the_unversioned_m3_contract(tmp_path: Path) -> None:
    manager = _manager(tmp_path / "out", _ServiceFactory())
    schema = create_app(manager).openapi()

    assert "/reports" in schema["paths"]
    assert "get" not in schema["paths"]["/reports"]
    assert set(schema["paths"]) == {
        "/reports",
        "/reports/{taskId}/status",
        "/reports/{taskId}/report.pdf",
        "/reports/{taskId}/bundle.zip",
    }
    post = schema["paths"]["/reports"]["post"]
    assert post["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ReportConfig"
    }
    assert set(post["responses"]) == {"200", "202", "409", "422", "503"}
    assert "security" not in schema
    assert "security" not in post
    assert set(schema["paths"]["/reports/{taskId}/status"]["get"]["responses"]) == {
        "200",
        "404",
        "422",
    }
    assert set(
        schema["paths"]["/reports/{taskId}/report.pdf"]["get"][
            "responses"
        ]
    ) == {"200", "404", "409", "422", "500"}
