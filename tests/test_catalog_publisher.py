from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from report_engine.storage.catalog import CatalogPublicationError, CatalogPublisher


def _published_bundle(
    output_root: Path,
    report_id: str,
    generated_at: str,
    **extra: object,
) -> tuple[Path, dict[str, object]]:
    bundle = output_root / report_id
    (bundle / "charts").mkdir(parents=True)
    (bundle / "report.md").write_text("# Report\n", encoding="utf-8")
    (bundle / "report.pdf").write_bytes(b"%PDF-1.4\n")
    meta: dict[str, object] = {
        "id": report_id,
        "title": f"Report {report_id}",
        "reportType": "csuite",
        "language": "zh",
        "topic": "测试主题",
        "dateRange": {"from": "2026-07-01", "to": "2026-07-10"},
        "sections": 7,
        "charts": 3,
        "stats": {
            "articles": 42,
            "negativeRatio": "25.0%",
            "peakDay": "2026-07-03",
        },
        "file": f"/reports/{report_id}/report.pdf",
        "generatedAt": generated_at,
        **extra,
    }
    (bundle / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8"
    )
    return bundle, meta


def _read_catalog(output_root: Path) -> list[dict[str, object]]:
    return json.loads((output_root / "index.json").read_text(encoding="utf-8"))


def test_publishes_exact_bundle_metadata_and_preserves_extensions(tmp_path) -> None:
    output_root = tmp_path / "out"
    bundle, meta = _published_bundle(
        output_root,
        "topic-2026-07-10-v1",
        "2026-07-10T18:30:00+08:00",
        generation={"status": "complete"},
    )

    catalog = CatalogPublisher().publish(bundle, output_root)

    assert catalog == output_root / "index.json"
    assert _read_catalog(output_root) == [meta]
    assert not list(output_root.glob(".index-*.tmp"))


def test_orders_newest_first_then_report_id_ascending(tmp_path) -> None:
    output_root = tmp_path / "out"
    older, _ = _published_bundle(
        output_root, "older-v1", "2026-07-09T10:00:00+08:00"
    )
    same_time_b, _ = _published_bundle(
        output_root, "same-b-v1", "2026-07-10T10:00:00+08:00"
    )
    same_time_a, _ = _published_bundle(
        output_root, "same-a-v1", "2026-07-10T10:00:00+08:00"
    )

    publisher = CatalogPublisher()
    for bundle in (older, same_time_b, same_time_a):
        publisher.publish(bundle, output_root)

    assert [entry["id"] for entry in _read_catalog(output_root)] == [
        "same-a-v1",
        "same-b-v1",
        "older-v1",
    ]


def test_identical_report_is_idempotent_without_replacing_catalog(tmp_path) -> None:
    output_root = tmp_path / "out"
    bundle, _ = _published_bundle(
        output_root, "topic-v1", "2026-07-10T10:00:00+08:00"
    )
    replace_calls: list[tuple[Path, Path]] = []

    def record_replace(source: Path, target: Path) -> None:
        replace_calls.append((source, target))
        source.replace(target)

    publisher = CatalogPublisher(replace=record_replace)
    publisher.publish(bundle, output_root)
    first_bytes = (output_root / "index.json").read_bytes()
    publisher.publish(bundle, output_root)

    assert (output_root / "index.json").read_bytes() == first_bytes
    assert len(replace_calls) == 1


def test_rejects_conflicting_metadata_for_an_existing_report_id(tmp_path) -> None:
    output_root = tmp_path / "out"
    bundle, _ = _published_bundle(
        output_root, "topic-v1", "2026-07-10T10:00:00+08:00"
    )
    publisher = CatalogPublisher()
    publisher.publish(bundle, output_root)
    old_bytes = (output_root / "index.json").read_bytes()
    meta_path = bundle / "meta.json"
    changed = json.loads(meta_path.read_text(encoding="utf-8"))
    changed["title"] = "Changed title"
    meta_path.write_text(json.dumps(changed), encoding="utf-8")

    with pytest.raises(CatalogPublicationError, match="conflicting report ID"):
        publisher.publish(bundle, output_root)

    assert (output_root / "index.json").read_bytes() == old_bytes


@pytest.mark.parametrize("catalog", ["not json", "{}"])
def test_rejects_a_malformed_existing_catalog_without_changing_it(
    tmp_path, catalog: str
) -> None:
    output_root = tmp_path / "out"
    bundle, _ = _published_bundle(
        output_root, "topic-v1", "2026-07-10T10:00:00+08:00"
    )
    index_path = output_root / "index.json"
    index_path.write_text(catalog, encoding="utf-8")

    with pytest.raises(CatalogPublicationError, match="existing report catalog"):
        CatalogPublisher().publish(bundle, output_root)

    assert index_path.read_text(encoding="utf-8") == catalog


def test_rejects_duplicate_existing_ids(tmp_path) -> None:
    output_root = tmp_path / "out"
    existing, meta = _published_bundle(
        output_root, "existing-v1", "2026-07-09T10:00:00+08:00"
    )
    bundle, _ = _published_bundle(
        output_root, "new-v1", "2026-07-10T10:00:00+08:00"
    )
    (output_root / "index.json").write_text(
        json.dumps([meta, meta]), encoding="utf-8"
    )

    with pytest.raises(CatalogPublicationError, match="duplicate report ID"):
        CatalogPublisher().publish(bundle, output_root)

    assert existing.is_dir()


def test_atomic_replace_failure_preserves_the_previous_catalog(tmp_path) -> None:
    output_root = tmp_path / "out"
    first, _ = _published_bundle(
        output_root, "first-v1", "2026-07-09T10:00:00+08:00"
    )
    second, _ = _published_bundle(
        output_root, "second-v1", "2026-07-10T10:00:00+08:00"
    )
    CatalogPublisher().publish(first, output_root)
    old_bytes = (output_root / "index.json").read_bytes()

    def fail_replace(source: Path, target: Path) -> None:
        raise OSError("filesystem detail must not escape")

    with pytest.raises(CatalogPublicationError, match="Could not update") as error:
        CatalogPublisher(replace=fail_replace).publish(second, output_root)

    assert "filesystem detail" not in str(error.value)
    assert (output_root / "index.json").read_bytes() == old_bytes
    assert not list(output_root.glob(".index-*.tmp"))


def test_concurrent_publishers_do_not_lose_catalog_entries(tmp_path) -> None:
    output_root = tmp_path / "out"
    bundles = [
        _published_bundle(
            output_root,
            f"topic-v{version}",
            f"2026-07-{version:02d}T10:00:00+08:00",
        )[0]
        for version in range(1, 13)
    ]

    with ThreadPoolExecutor(max_workers=6) as executor:
        list(
            executor.map(
                lambda bundle: CatalogPublisher().publish(bundle, output_root),
                bundles,
            )
        )

    entries = _read_catalog(output_root)
    assert len(entries) == 12
    assert {entry["id"] for entry in entries} == {
        f"topic-v{version}" for version in range(1, 13)
    }


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"generatedAt": "2026-07-10T10:00:00"}, "bundle metadata"),
        ({"sections": -1}, "bundle metadata"),
        ({"id": "different-v1"}, "bundle metadata"),
    ],
)
def test_rejects_invalid_bundle_metadata(tmp_path, mutation, message) -> None:
    output_root = tmp_path / "out"
    bundle, meta = _published_bundle(
        output_root, "topic-v1", "2026-07-10T10:00:00+08:00"
    )
    meta.update(mutation)
    (bundle / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

    with pytest.raises(CatalogPublicationError, match=message):
        CatalogPublisher().publish(bundle, output_root)

    assert not (output_root / "index.json").exists()
