from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from report_engine.api.jobs import (
    JobRecord,
    JobStatus,
    JobStore,
    JobStoreError,
    JobTransitionError,
)
from report_engine.config import SectionId


TASK_ID = UUID("4f7f7f38-a88f-4f70-b558-4798d0acef91")
SUBMITTED_AT = datetime(2026, 7, 17, 4, 0, tzinfo=UTC)


def _queued(
    *,
    task_id: UUID = TASK_ID,
    submitted_at: datetime = SUBMITTED_AT,
    total_sections: int = 2,
) -> JobRecord:
    return JobRecord.queued(
        task_id=task_id,
        submitted_at=submitted_at,
        total_sections=total_sections,
    )


def test_job_record_allows_only_explicit_lifecycle_transitions() -> None:
    queued = _queued()

    running = queued.mark_running(SUBMITTED_AT + timedelta(seconds=1))
    first_section = running.update_progress(
        current_section=SectionId.METRICS,
        completed_sections=0,
    )
    second_section = first_section.update_progress(
        current_section=SectionId.TREND,
        completed_sections=1,
    )
    ready = second_section.update_progress(
        current_section=None,
        completed_sections=2,
    )
    completed = ready.mark_completed(
        SUBMITTED_AT + timedelta(seconds=10),
        report_id="topic-2026-07-17-v1",
    )

    assert completed.status is JobStatus.COMPLETED
    assert completed.progress.completed_sections == 2
    assert completed.report_id == "topic-2026-07-17-v1"
    assert completed.downloads is not None
    assert completed.downloads.pdf == f"/reports/{TASK_ID}/report.pdf"
    assert completed.downloads.bundle == f"/reports/{TASK_ID}/bundle.zip"

    with pytest.raises(JobTransitionError, match="terminal"):
        completed.mark_failed(
            SUBMITTED_AT + timedelta(seconds=11),
            code="generation_failed",
            message="Report generation failed",
        )


def test_job_record_rejects_skipped_or_regressing_transitions() -> None:
    queued = _queued()

    with pytest.raises(JobTransitionError, match="Invalid job lifecycle"):
        queued.mark_running(SUBMITTED_AT - timedelta(seconds=1))

    with pytest.raises(JobTransitionError, match="queued"):
        queued.mark_completed(SUBMITTED_AT, report_id="topic-v1")

    running = queued.mark_running(SUBMITTED_AT + timedelta(seconds=1))
    progressed = running.update_progress(
        current_section=SectionId.TREND,
        completed_sections=1,
    )

    with pytest.raises(JobTransitionError, match="regress"):
        progressed.update_progress(
            current_section=SectionId.METRICS,
            completed_sections=0,
        )

    with pytest.raises(JobTransitionError, match="all sections"):
        progressed.mark_completed(
            SUBMITTED_AT + timedelta(seconds=2),
            report_id="topic-v1",
        )

    with pytest.raises(JobTransitionError, match="Invalid job lifecycle"):
        progressed.update_progress(
            current_section=None,
            completed_sections=3,
        )


def test_interrupted_queued_job_can_be_persisted_as_safe_failure() -> None:
    failed = _queued().mark_failed(
        SUBMITTED_AT + timedelta(minutes=1),
        code="service_restarted",
        message="Report generation was interrupted by a service restart",
    )

    assert failed.status is JobStatus.FAILED
    assert failed.started_at is None
    assert failed.finished_at == SUBMITTED_AT + timedelta(minutes=1)
    assert failed.error is not None
    assert failed.error.code == "service_restarted"
    assert failed.report_id is None
    assert failed.downloads is None


def test_job_record_rejects_inconsistent_persisted_state() -> None:
    raw = _queued().model_dump(mode="json", by_alias=True)
    raw.update(
        {
            "status": "completed",
            "finishedAt": "2026-07-17T04:01:00Z",
            "reportId": "topic-v1",
            "downloads": {
                "pdf": f"/reports/{TASK_ID}/report.pdf",
                "bundle": f"/reports/{TASK_ID}/bundle.zip",
            },
        }
    )

    with pytest.raises(ValidationError, match="completed job"):
        JobRecord.model_validate(raw)


@pytest.mark.parametrize(
    "mutation",
    [
        {"submittedAt": "2026-07-17T04:00:00"},
        {"idempotencyKeyHash": "a" * 64},
        {"requestFingerprint": "b" * 64},
    ],
)
def test_job_record_rejects_unsafe_timestamp_or_partial_idempotency_metadata(
    mutation: dict[str, str],
) -> None:
    raw = _queued().model_dump(mode="json", by_alias=True)
    raw.update(mutation)

    with pytest.raises(ValidationError):
        JobRecord.model_validate(raw)


def test_store_round_trip_uses_atomic_task_path_without_sensitive_config(
    tmp_path: Path,
) -> None:
    store = JobStore(tmp_path / "out")
    record = JobRecord.queued(
        task_id=TASK_ID,
        submitted_at=SUBMITTED_AT,
        total_sections=2,
        idempotency_key_hash="a" * 64,
        request_fingerprint="b" * 64,
    )

    task_path = store.create(record)

    assert task_path == (
        tmp_path / "out" / ".report-jobs" / "tasks" / f"{TASK_ID}.json"
    )
    assert store.get(TASK_ID) == record
    raw = json.loads(task_path.read_text(encoding="utf-8"))
    assert raw["schemaVersion"] == 1
    assert raw["taskId"] == str(TASK_ID)
    assert raw["status"] == "queued"
    assert raw["progress"] == {
        "currentSection": None,
        "completedSections": 0,
        "totalSections": 2,
    }
    assert "config" not in raw
    assert "notes" not in raw
    assert not list(task_path.parent.glob(".job-*.tmp"))


def test_store_preserves_unknown_fields_across_a_state_update(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "out")
    task_path = store.create(_queued())
    raw = json.loads(task_path.read_text(encoding="utf-8"))
    raw["futureField"] = {"retained": True}
    task_path.write_text(json.dumps(raw), encoding="utf-8")

    loaded = store.get(TASK_ID)
    assert loaded is not None
    store.update(loaded.mark_running(SUBMITTED_AT + timedelta(seconds=1)))

    updated = json.loads(task_path.read_text(encoding="utf-8"))
    assert updated["futureField"] == {"retained": True}
    assert updated["status"] == "running"


def test_store_rejects_duplicate_create_and_missing_update(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "out")
    store.create(_queued())

    with pytest.raises(JobStoreError, match="already exists"):
        store.create(_queued())

    missing = _queued(
        task_id=UUID("82a4dcf7-181a-4c36-b871-ec7a14ab0d8a")
    )
    with pytest.raises(JobStoreError, match="does not exist"):
        store.update(missing)


def test_store_rejects_a_stale_progress_update(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "out")
    queued = _queued()
    store.create(queued)
    running = queued.mark_running(SUBMITTED_AT + timedelta(seconds=1))
    store.update(running)
    progressed = running.update_progress(
        current_section=SectionId.TREND,
        completed_sections=1,
    )
    store.update(progressed)

    stale = running.update_progress(
        current_section=SectionId.METRICS,
        completed_sections=0,
    )
    with pytest.raises(JobTransitionError, match="regress"):
        store.update(stale)

    assert store.get(TASK_ID) == progressed


@pytest.mark.parametrize(
    "contents",
    [
        "not json",
        "[]",
        json.dumps(
            {
                **_queued().model_dump(mode="json", by_alias=True),
                "status": "unknown",
            }
        ),
    ],
)
def test_store_rejects_corrupt_state_instead_of_silently_skipping_it(
    tmp_path: Path,
    contents: str,
) -> None:
    tasks = tmp_path / "out" / ".report-jobs" / "tasks"
    tasks.mkdir(parents=True)
    task_path = tasks / f"{TASK_ID}.json"
    task_path.write_text(contents, encoding="utf-8")

    with pytest.raises(JobStoreError, match="Invalid persisted report task"):
        JobStore(tmp_path / "out").load_all()

    assert task_path.read_text(encoding="utf-8") == contents


def test_store_rejects_a_record_whose_filename_does_not_match_task_id(
    tmp_path: Path,
) -> None:
    tasks = tmp_path / "out" / ".report-jobs" / "tasks"
    tasks.mkdir(parents=True)
    wrong_id = UUID("82a4dcf7-181a-4c36-b871-ec7a14ab0d8a")
    (tasks / f"{wrong_id}.json").write_text(
        _queued().model_dump_json(by_alias=True),
        encoding="utf-8",
    )

    with pytest.raises(JobStoreError, match="Invalid persisted report task"):
        JobStore(tmp_path / "out").load_all()


def test_store_rejects_a_corrupt_tasks_directory(tmp_path: Path) -> None:
    tasks = tmp_path / "out" / ".report-jobs" / "tasks"
    tasks.parent.mkdir(parents=True)
    tasks.write_text("not a directory", encoding="utf-8")

    store = JobStore(tmp_path / "out")
    with pytest.raises(JobStoreError, match="Invalid report task storage"):
        store.load_all()
    with pytest.raises(JobStoreError, match="Invalid report task storage"):
        store.get(TASK_ID)


def test_store_rejects_a_symlinked_internal_job_root(tmp_path: Path) -> None:
    output_root = tmp_path / "out"
    output_root.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    (output_root / ".report-jobs").symlink_to(
        external,
        target_is_directory=True,
    )

    with pytest.raises(JobStoreError, match="Invalid report task storage"):
        JobStore(output_root).create(_queued())

    assert not (external / "tasks").exists()


def test_atomic_replace_failure_preserves_previous_job_state(tmp_path: Path) -> None:
    output_root = tmp_path / "out"
    normal_store = JobStore(output_root)
    task_path = normal_store.create(_queued())
    old_bytes = task_path.read_bytes()

    def fail_replace(source: Path, target: Path) -> None:
        raise OSError("filesystem detail must not escape")

    failing_store = JobStore(output_root, replace=fail_replace)
    running = _queued().mark_running(SUBMITTED_AT + timedelta(seconds=1))

    with pytest.raises(JobStoreError, match="Could not persist") as error:
        failing_store.update(running)

    assert "filesystem detail" not in str(error.value)
    assert task_path.read_bytes() == old_bytes
    assert not list(task_path.parent.glob(".job-*.tmp"))


def test_store_loads_records_deterministically_and_ignores_temp_files(
    tmp_path: Path,
) -> None:
    store = JobStore(tmp_path / "out")
    records = [
        _queued(task_id=TASK_ID),
        _queued(
            task_id=UUID("82a4dcf7-181a-4c36-b871-ec7a14ab0d8a"),
            submitted_at=SUBMITTED_AT + timedelta(seconds=1),
        ),
    ]
    for record in reversed(records):
        store.create(record)
    tasks = tmp_path / "out" / ".report-jobs" / "tasks"
    (tasks / ".job-interrupted.tmp").write_text("partial", encoding="utf-8")

    assert store.load_all() == tuple(records)


def test_concurrent_store_instances_do_not_lose_jobs(tmp_path: Path) -> None:
    output_root = tmp_path / "out"
    records = [
        _queued(task_id=UUID(int=index + 1))
        for index in range(12)
    ]

    with ThreadPoolExecutor(max_workers=6) as executor:
        list(executor.map(lambda item: JobStore(output_root).create(item), records))

    assert {record.task_id for record in JobStore(output_root).load_all()} == {
        record.task_id for record in records
    }


def test_store_rejects_non_uuid_lookup_without_path_traversal(tmp_path: Path) -> None:
    output_root = tmp_path / "out"
    store = JobStore(output_root)

    with pytest.raises(JobStoreError, match="Invalid report task ID"):
        store.get("../../outside")

    assert not (tmp_path / "outside").exists()
