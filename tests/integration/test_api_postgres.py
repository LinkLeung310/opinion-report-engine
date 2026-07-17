from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
import json
import os
from pathlib import Path
import threading
import time
from zipfile import ZipFile

from fastapi.testclient import TestClient
from PIL import Image
import psycopg
import pytest
from pypdf import PdfReader

from report_engine.api.app import create_app
from report_engine.api.jobs import JobStatus
from report_engine.api.manager import JobManager
from report_engine.llm.stub import StubNarrator
from report_engine.runtime import build_report_service_factory
from report_engine.settings import Settings
from report_engine.storage.archive import ZipArchivePublisher


pytestmark = pytest.mark.integration

REPOSITORY_ROOT = Path(__file__).parents[2]
CONFIG = REPOSITORY_ROOT / "examples" / "report-config.metrics.json"


class _BarrierNarrator:
    def __init__(self, barrier: threading.Barrier) -> None:
        self._barrier = barrier
        self._stub = StubNarrator()

    @property
    def requests(self):
        return self._stub.requests

    def narrate(self, request):
        try:
            self._barrier.wait(timeout=15)
        except threading.BrokenBarrierError:
            raise RuntimeError(
                "API jobs did not reach narration concurrently"
            ) from None
        return self._stub.narrate(request)


def _wait_for_completed(client: TestClient, task_id: str) -> dict:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        response = client.get(f"/reports/{task_id}/status")
        assert response.status_code == 200
        status = response.json()
        if status["status"] == JobStatus.COMPLETED:
            return status
        if status["status"] == JobStatus.FAILED:
            pytest.fail(f"API task failed: {status['error']}")
        time.sleep(0.02)
    pytest.fail("API task did not complete within 30 seconds")


def _assert_a4_pdf(pdf_bytes: bytes) -> None:
    reader = PdfReader(BytesIO(pdf_bytes))
    assert reader.pages
    for page in reader.pages:
        assert float(page.mediabox.width) == pytest.approx(595.28, abs=0.5)
        assert float(page.mediabox.height) == pytest.approx(841.89, abs=0.5)
    assert sum(len(page.images) for page in reader.pages) == 1


def test_two_real_database_api_jobs_survive_service_restart(tmp_path: Path) -> None:
    dsn = os.getenv("PG_DSN")
    if not dsn:
        pytest.skip("PG_DSN is required for fixture integration tests")

    output_root = tmp_path / "out"
    raw_config = json.loads(CONFIG.read_text(encoding="utf-8"))
    barrier = threading.Barrier(2)
    narrators: list[_BarrierNarrator] = []
    connection_ids: list[int] = []
    backend_pids: list[int] = []
    resource_lock = threading.Lock()

    def narrator_factory() -> _BarrierNarrator:
        narrator = _BarrierNarrator(barrier)
        with resource_lock:
            narrators.append(narrator)
        return narrator

    def tracked_connect(dsn_value: str, *, connect_timeout: int):
        connection = psycopg.connect(
            dsn_value,
            connect_timeout=connect_timeout,
        )
        with resource_lock:
            connection_ids.append(id(connection))
            backend_pids.append(connection.info.backend_pid)
        return connection

    settings = Settings(
        pg_dsn=dsn,
        llm_base_url=None,
        llm_api_key=None,
        llm_model=None,
    )
    service_factory = build_report_service_factory(
        settings,
        narrator_factory=narrator_factory,
        connect=tracked_connect,
    )
    first_manager = JobManager(
        output_root=output_root,
        service_factory=service_factory,
        archive_publisher=ZipArchivePublisher(),
        clock=lambda: datetime.now(UTC),
    )
    downloads: dict[str, tuple[bytes, bytes]] = {}

    with TestClient(create_app(first_manager)) as client:
        first = client.post("/reports", json=raw_config)
        second = client.post("/reports", json=raw_config)
        assert first.status_code == 202
        assert second.status_code == 202
        task_ids = (first.json()["taskId"], second.json()["taskId"])
        assert task_ids[0] != task_ids[1]

        statuses = tuple(
            _wait_for_completed(client, task_id) for task_id in task_ids
        )
        report_ids = {status["reportId"] for status in statuses}
        assert report_ids == {
            "bilibili-dislike-2026-03-23-v1",
            "bilibili-dislike-2026-03-23-v2",
        }

        for status in statuses:
            pdf = client.get(status["downloads"]["pdf"])
            archive = client.get(status["downloads"]["bundle"])
            assert pdf.status_code == 200
            assert archive.status_code == 200
            _assert_a4_pdf(pdf.content)
            with ZipFile(BytesIO(archive.content)) as handle:
                root = status["reportId"]
                assert set(handle.namelist()) == {
                    f"{root}/",
                    f"{root}/report.md",
                    f"{root}/report.pdf",
                    f"{root}/meta.json",
                    f"{root}/charts/",
                    f"{root}/charts/sentiment-overview.png",
                }
            downloads[status["taskId"]] = (pdf.content, archive.content)

            bundle = output_root / status["reportId"]
            meta = json.loads(
                (bundle / "meta.json").read_text(encoding="utf-8")
            )
            assert meta["stats"] == {
                "articles": 12,
                "negativeRatio": "58.3%",
                "peakDay": "3/20",
            }
            assert meta["generation"] == {
                "requested": 1,
                "complete": 1,
                "noData": 0,
                "failed": 0,
            }
            chart_path = bundle / "charts" / "sentiment-overview.png"
            with Image.open(chart_path) as chart:
                assert chart.info["dpi"] == pytest.approx((150, 150), abs=0.1)

    assert len(narrators) == 2
    assert all(len(narrator.requests) == 1 for narrator in narrators)
    assert len(set(connection_ids)) == 2
    assert len(set(backend_pids)) == 2
    catalog = json.loads((output_root / "index.json").read_text(encoding="utf-8"))
    assert {entry["id"] for entry in catalog} == report_ids

    restarted_narrators: list[StubNarrator] = []

    def restarted_narrator_factory() -> StubNarrator:
        narrator = StubNarrator()
        restarted_narrators.append(narrator)
        return narrator

    restarted_manager = JobManager(
        output_root=output_root,
        service_factory=build_report_service_factory(
            settings,
            narrator_factory=restarted_narrator_factory,
        ),
        archive_publisher=ZipArchivePublisher(),
        clock=lambda: datetime.now(UTC),
    )
    with TestClient(create_app(restarted_manager)) as client:
        for task_id, expected in downloads.items():
            status = client.get(f"/reports/{task_id}/status")
            pdf = client.get(f"/reports/{task_id}/report.pdf")
            archive = client.get(f"/reports/{task_id}/bundle.zip")
            assert status.status_code == 200
            assert status.json()["status"] == "completed"
            assert (pdf.content, archive.content) == expected

    assert restarted_narrators == []
