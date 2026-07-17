from __future__ import annotations

import json
import threading
import time
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID
from zipfile import ZipFile

import pytest

from report_engine.api.jobs import JobRecord, JobStatus, JobStore
from report_engine.api.manager import (
    JobArtifactUnavailableError,
    JobIdempotencyConflictError,
    JobManager,
    JobManagerError,
    JobNotReadyError,
    JobQueueFullError,
)
from report_engine.config import ReportConfig, SectionId
from report_engine.storage.archive import JobArchiveError, ZipArchivePublisher
from tests.test_config import sample_config


NOW = datetime(2026, 7, 17, 5, 0, tzinfo=UTC)
TASK_IDS = (
    UUID("4f7f7f38-a88f-4f70-b558-4798d0acef91"),
    UUID("82a4dcf7-181a-4c36-b871-ec7a14ab0d8a"),
    UUID("b933bfa7-679d-49aa-b5c2-c28a8fb9ca2a"),
    UUID("e6532e65-797a-4da1-8822-750413df805d"),
)


def _config(tag: str = "bilibili-dislike") -> ReportConfig:
    raw = sample_config()
    raw["topic"]["tag"] = tag
    raw["sections"] = [{"id": "metrics", "enabled": True}]
    return ReportConfig.model_validate(raw)


def _id_factory(*task_ids: UUID):
    values = iter(task_ids)
    return lambda: next(values)


def _write_bundle(output_root: Path, report_id: str) -> Path:
    bundle = output_root / report_id
    charts = bundle / "charts"
    charts.mkdir(parents=True)
    (bundle / "report.md").write_text("# Report\n", encoding="utf-8")
    (bundle / "report.pdf").write_bytes(b"%PDF-1.4\n")
    (bundle / "meta.json").write_text(
        json.dumps({"id": report_id}),
        encoding="utf-8",
    )
    (charts / "sentiment.png").write_bytes(b"PNG")
    return bundle


@dataclass
class _FakeService:
    resource_id: int
    gate: threading.Event | None
    started: threading.Condition
    started_resources: list[int]
    fail: bool

    def generate(
        self,
        config: ReportConfig,
        output_root: Path,
        progress_callback=None,
    ):
        enabled = [section.id for section in config.sections if section.enabled]
        if progress_callback is not None:
            progress_callback(enabled[0], 0)
        with self.started:
            self.started_resources.append(self.resource_id)
            self.started.notify_all()
        if self.gate is not None and not self.gate.wait(timeout=5):
            raise RuntimeError("test gate timed out")
        if self.fail:
            raise RuntimeError("secret provider and filesystem detail")
        report_id = f"{config.topic.tag}-v{self.resource_id}"
        _write_bundle(output_root, report_id)
        if progress_callback is not None:
            progress_callback(None, len(enabled))
        return SimpleNamespace(report_id=report_id)


class _FakeServiceFactory:
    def __init__(
        self,
        *,
        gate: threading.Event | None = None,
        fail: bool = False,
    ) -> None:
        self.gate = gate
        self.fail = fail
        self.condition = threading.Condition()
        self.started_resources: list[int] = []
        self.closed_resources: list[int] = []
        self._next_resource = 1

    def __call__(self) -> AbstractContextManager[_FakeService]:
        return self._open()

    @contextmanager
    def _open(self):
        with self.condition:
            resource_id = self._next_resource
            self._next_resource += 1
        try:
            yield _FakeService(
                resource_id=resource_id,
                gate=self.gate,
                started=self.condition,
                started_resources=self.started_resources,
                fail=self.fail,
            )
        finally:
            with self.condition:
                self.closed_resources.append(resource_id)
                self.condition.notify_all()

    def wait_until_started(self, count: int) -> None:
        deadline = time.monotonic() + 5
        with self.condition:
            while len(self.started_resources) < count:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise AssertionError("workers did not start")
                self.condition.wait(timeout=remaining)


def _wait_for_terminal(manager: JobManager, task_id: UUID) -> JobRecord:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        record = manager.get(task_id)
        assert record is not None
        if record.status in {JobStatus.COMPLETED, JobStatus.FAILED}:
            return record
        time.sleep(0.01)
    raise AssertionError("job did not reach a terminal state")


def _manager(
    output_root: Path,
    factory: _FakeServiceFactory,
    *task_ids: UUID,
    max_workers: int = 2,
    max_active_jobs: int = 16,
) -> JobManager:
    return JobManager(
        output_root=output_root,
        service_factory=factory,
        archive_publisher=ZipArchivePublisher(),
        clock=lambda: NOW,
        task_id_factory=_id_factory(*task_ids),
        max_workers=max_workers,
        max_active_jobs=max_active_jobs,
    )


def test_manager_runs_two_tasks_with_separate_resource_contexts(tmp_path: Path) -> None:
    gate = threading.Event()
    factory = _FakeServiceFactory(gate=gate)
    manager = _manager(tmp_path / "out", factory, *TASK_IDS[:2])
    manager.start()

    first = manager.submit(_config("first-topic"))
    second = manager.submit(_config("second-topic"))
    factory.wait_until_started(2)

    assert set(factory.started_resources) == {1, 2}
    assert manager.get(first.record.task_id).status is JobStatus.RUNNING
    assert manager.get(second.record.task_id).status is JobStatus.RUNNING
    with pytest.raises(JobNotReadyError):
        manager.artifacts(first.record.task_id)

    gate.set()
    first_done = _wait_for_terminal(manager, first.record.task_id)
    second_done = _wait_for_terminal(manager, second.record.task_id)
    manager.close()

    assert first_done.status is JobStatus.COMPLETED
    assert second_done.status is JobStatus.COMPLETED
    assert first_done.report_id != second_done.report_id
    assert set(factory.closed_resources) == {1, 2}
    assert manager.artifacts(first.record.task_id).pdf.is_file()
    assert manager.artifacts(second.record.task_id).archive.is_file()


def test_bounded_capacity_counts_running_and_queued_jobs(tmp_path: Path) -> None:
    gate = threading.Event()
    factory = _FakeServiceFactory(gate=gate)
    manager = _manager(
        tmp_path / "out",
        factory,
        *TASK_IDS,
        max_workers=1,
        max_active_jobs=2,
    )
    manager.start()

    first = manager.submit(_config("first"))
    factory.wait_until_started(1)
    second = manager.submit(_config("second"))
    with pytest.raises(JobQueueFullError, match="capacity"):
        manager.submit(_config("third"))

    assert manager.get(first.record.task_id).status is JobStatus.RUNNING
    assert manager.get(second.record.task_id).status is JobStatus.QUEUED
    gate.set()
    assert (
        _wait_for_terminal(manager, first.record.task_id).status
        is JobStatus.COMPLETED
    )
    assert (
        _wait_for_terminal(manager, second.record.task_id).status
        is JobStatus.COMPLETED
    )

    third = manager.submit(_config("third"))
    assert (
        _wait_for_terminal(manager, third.record.task_id).status
        is JobStatus.COMPLETED
    )
    manager.close()


def test_idempotency_replays_same_config_and_rejects_key_reuse(tmp_path: Path) -> None:
    gate = threading.Event()
    factory = _FakeServiceFactory(gate=gate)
    output_root = tmp_path / "out"
    manager = _manager(output_root, factory, *TASK_IDS[:2], max_workers=1)
    manager.start()

    first = manager.submit(_config(), idempotency_key="  retry-123  ")
    replay = manager.submit(_config(), idempotency_key="retry-123")

    assert replay.replayed is True
    assert replay.record.task_id == first.record.task_id
    with pytest.raises(JobIdempotencyConflictError, match="different config"):
        manager.submit(_config("other-topic"), idempotency_key="retry-123")

    task_json = (
        output_root
        / ".report-jobs"
        / "tasks"
        / f"{first.record.task_id}.json"
    ).read_text(encoding="utf-8")
    assert "retry-123" not in task_json
    assert "bilibili-dislike" not in task_json

    gate.set()
    _wait_for_terminal(manager, first.record.task_id)
    terminal_replay = manager.submit(_config(), idempotency_key="retry-123")
    manager.close()

    assert terminal_replay.replayed is True
    assert terminal_replay.record.status is JobStatus.COMPLETED
    assert factory.started_resources == [1]


def test_completed_idempotent_task_replays_after_manager_restart(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "out"
    first_factory = _FakeServiceFactory()
    first_manager = _manager(output_root, first_factory, TASK_IDS[0])
    first_manager.start()
    submitted = first_manager.submit(_config(), idempotency_key="restart-safe")
    completed = _wait_for_terminal(first_manager, submitted.record.task_id)
    first_manager.close()

    second_factory = _FakeServiceFactory()
    second_manager = _manager(output_root, second_factory, TASK_IDS[1])
    second_manager.start()
    replay = second_manager.submit(_config(), idempotency_key="restart-safe")
    second_manager.close()

    assert completed.status is JobStatus.COMPLETED
    assert replay.replayed is True
    assert replay.record == completed
    assert second_factory.started_resources == []


@pytest.mark.parametrize(
    "key",
    ["", "contains space", "非ascii", "control\nkey", "x" * 129],
)
def test_rejects_invalid_idempotency_keys(tmp_path: Path, key: str) -> None:
    manager = _manager(tmp_path / "out", _FakeServiceFactory(), TASK_IDS[0])
    manager.start()

    with pytest.raises(JobManagerError, match="idempotency key"):
        manager.submit(_config(), idempotency_key=key)

    manager.close()


def test_generation_failure_is_safe_and_releases_capacity(tmp_path: Path) -> None:
    factory = _FakeServiceFactory(fail=True)
    manager = _manager(
        tmp_path / "out",
        factory,
        *TASK_IDS[:2],
        max_workers=1,
        max_active_jobs=1,
    )
    manager.start()

    submission = manager.submit(_config())
    failed = _wait_for_terminal(manager, submission.record.task_id)

    assert failed.status is JobStatus.FAILED
    assert failed.error is not None
    assert failed.error.code == "generation_failed"
    assert failed.error.message == "Report generation failed"
    assert "secret" not in failed.error.message

    second = manager.submit(_config("second"))
    assert _wait_for_terminal(manager, second.record.task_id).status is JobStatus.FAILED
    manager.close()


def test_start_recovers_completed_and_fails_interrupted_jobs(tmp_path: Path) -> None:
    output_root = tmp_path / "out"
    store = JobStore(output_root)
    submitted = NOW - timedelta(minutes=5)

    queued = JobRecord.queued(
        task_id=TASK_IDS[0],
        submitted_at=submitted,
        total_sections=1,
    )
    store.create(queued)
    running = JobRecord.queued(
        task_id=TASK_IDS[1],
        submitted_at=submitted,
        total_sections=1,
    )
    store.create(running)
    store.update(running.mark_running(submitted + timedelta(seconds=1)))

    completed = JobRecord.queued(
        task_id=TASK_IDS[2],
        submitted_at=submitted,
        total_sections=1,
    )
    store.create(completed)
    completed = completed.mark_running(submitted + timedelta(seconds=1))
    store.update(completed)
    completed = completed.update_progress(
        current_section=None,
        completed_sections=1,
    )
    store.update(completed)
    _write_bundle(output_root, "completed-v1")
    ZipArchivePublisher().publish(TASK_IDS[2], "completed-v1", output_root)
    completed = completed.mark_completed(
        submitted + timedelta(minutes=1),
        report_id="completed-v1",
    )
    store.update(completed)

    manager = _manager(output_root, _FakeServiceFactory(), TASK_IDS[3])
    manager.start()

    for task_id in TASK_IDS[:2]:
        recovered = manager.get(task_id)
        assert recovered is not None
        assert recovered.status is JobStatus.FAILED
        assert recovered.error is not None
        assert recovered.error.code == "service_restarted"
    assert manager.get(TASK_IDS[2]) == completed
    assert manager.artifacts(TASK_IDS[2]).archive.is_file()
    manager.close()


def test_corrupt_persisted_state_prevents_manager_start(tmp_path: Path) -> None:
    tasks = tmp_path / "out" / ".report-jobs" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / f"{TASK_IDS[0]}.json").write_text("not json", encoding="utf-8")
    manager = _manager(tmp_path / "out", _FakeServiceFactory(), TASK_IDS[1])

    with pytest.raises(JobManagerError, match="start"):
        manager.start()


def test_close_stops_accepting_and_waits_for_accepted_work(tmp_path: Path) -> None:
    gate = threading.Event()
    factory = _FakeServiceFactory(gate=gate)
    manager = _manager(tmp_path / "out", factory, *TASK_IDS[:2], max_workers=1)
    manager.start()
    submission = manager.submit(_config())
    factory.wait_until_started(1)
    closed = threading.Event()

    def close_manager() -> None:
        manager.close()
        closed.set()

    closer = threading.Thread(target=close_manager)
    closer.start()
    time.sleep(0.05)

    assert not closed.is_set()
    with pytest.raises(JobManagerError, match="not accepting"):
        manager.submit(_config("late"))

    gate.set()
    closer.join(timeout=5)
    assert closed.is_set()
    assert manager.get(submission.record.task_id).status is JobStatus.COMPLETED


def test_zip_publisher_contains_only_the_fixed_bundle(tmp_path: Path) -> None:
    output_root = tmp_path / "out"
    _write_bundle(output_root, "topic-v1")
    (output_root / "index.json").write_text("[]", encoding="utf-8")
    archive = ZipArchivePublisher().publish(TASK_IDS[0], "topic-v1", output_root)

    with ZipFile(archive) as handle:
        assert set(handle.namelist()) == {
            "topic-v1/",
            "topic-v1/report.md",
            "topic-v1/report.pdf",
            "topic-v1/meta.json",
            "topic-v1/charts/",
            "topic-v1/charts/sentiment.png",
        }
    assert not list(archive.parent.glob(".archive-*.tmp"))


def test_zip_replace_failure_leaves_no_partial_download(tmp_path: Path) -> None:
    output_root = tmp_path / "out"
    _write_bundle(output_root, "topic-v1")

    def fail_replace(source: Path, target: Path) -> None:
        raise OSError("filesystem detail must not escape")

    with pytest.raises(JobArchiveError, match="Could not publish") as error:
        ZipArchivePublisher(replace=fail_replace).publish(
            TASK_IDS[0],
            "topic-v1",
            output_root,
        )

    assert "filesystem detail" not in str(error.value)
    downloads = output_root / ".report-jobs" / "downloads"
    assert not (downloads / f"{TASK_IDS[0]}.zip").exists()
    assert not list(downloads.glob(".archive-*.tmp"))


def test_zip_publisher_rejects_a_symlinked_internal_job_root(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "out"
    _write_bundle(output_root, "topic-v1")
    external = tmp_path / "external"
    external.mkdir()
    (output_root / ".report-jobs").symlink_to(
        external,
        target_is_directory=True,
    )

    with pytest.raises(JobArchiveError, match="archive storage"):
        ZipArchivePublisher().publish(TASK_IDS[0], "topic-v1", output_root)

    assert not (external / "downloads").exists()


def test_artifact_lookup_rejects_missing_files(tmp_path: Path) -> None:
    manager = _manager(tmp_path / "out", _FakeServiceFactory(), TASK_IDS[0])
    manager.start()
    submission = manager.submit(_config())
    completed = _wait_for_terminal(manager, submission.record.task_id)
    assert completed.report_id is not None
    (tmp_path / "out" / completed.report_id / "report.pdf").unlink()

    with pytest.raises(JobArtifactUnavailableError, match="unavailable"):
        manager.artifacts(submission.record.task_id)

    manager.close()
