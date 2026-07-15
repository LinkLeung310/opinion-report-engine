from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from report_engine.rendering.assembler import ReportAssembler
from report_engine.storage.bundle import BundlePublisher
from tests.test_report_assembler import config_with_sections, section_results


def assembled_report():
    return ReportAssembler().assemble(
        config_with_sections(),
        "layoff-2026-03-23-v1",
        section_results(),
        datetime(2026, 7, 15, 2, 0, tzinfo=UTC),
    )


def test_publishes_the_complete_fixed_bundle_atomically(tmp_path) -> None:
    chart_source = tmp_path / "source.png"
    chart_source.write_bytes(b"png fixture")
    output_root = tmp_path / "out"

    target = BundlePublisher().publish(
        assembled_report(),
        b"%PDF-1.4\nfixture",
        {"sentiment-overview.png": chart_source},
        output_root,
    )

    assert target == output_root / "layoff-2026-03-23-v1"
    assert (target / "report.md").is_file()
    assert (target / "report.pdf").read_bytes().startswith(b"%PDF-")
    assert (target / "charts" / "sentiment-overview.png").is_file()
    meta = json.loads((target / "meta.json").read_text(encoding="utf-8"))
    assert meta["id"] == "layoff-2026-03-23-v1"
    assert not list(output_root.glob(".tmp-*"))


def test_missing_chart_never_publishes_a_partial_bundle(tmp_path) -> None:
    output_root = tmp_path / "out"

    with pytest.raises(FileNotFoundError, match="chart source is missing"):
        BundlePublisher().publish(
            assembled_report(),
            b"%PDF-1.4\nfixture",
            {"sentiment-overview.png": tmp_path / "missing.png"},
            output_root,
        )

    assert not (output_root / "layoff-2026-03-23-v1").exists()
    assert not list(output_root.glob(".tmp-*"))


def test_refuses_to_overwrite_an_existing_report_version(tmp_path) -> None:
    chart_source = tmp_path / "source.png"
    chart_source.write_bytes(b"png fixture")
    output_root = tmp_path / "out"
    publisher = BundlePublisher()
    report = assembled_report()
    publisher.publish(
        report,
        b"%PDF-1.4\nfixture",
        {"sentiment-overview.png": chart_source},
        output_root,
    )

    with pytest.raises(FileExistsError, match="already exists"):
        publisher.publish(
            report,
            b"%PDF-1.4\nfixture",
            {"sentiment-overview.png": chart_source},
            output_root,
        )


def test_rejects_path_traversal_in_report_ids(tmp_path) -> None:
    report = replace(assembled_report(), report_id="../outside")

    with pytest.raises(ValueError, match="invalid report ID"):
        BundlePublisher().publish(report, b"%PDF-1.4\n", {}, tmp_path / "out")
