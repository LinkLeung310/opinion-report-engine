"""Publish the frontend report catalog without exposing partial updates."""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Any, Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from report_engine.config import Language, ReportType


NonEmptyString = Annotated[str, Field(strict=True, min_length=1)]
NonNegativeInteger = Annotated[int, Field(strict=True, ge=0)]


class CatalogPublicationError(RuntimeError):
    """A safe, user-facing failure to publish the report catalog."""


class _CatalogDateRange(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    from_date: date = Field(alias="from")
    to_date: date = Field(alias="to")

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        if self.from_date > self.to_date:
            raise ValueError("date range is reversed")
        return self


class _CatalogStats(BaseModel):
    model_config = ConfigDict(extra="allow")

    articles: NonNegativeInteger
    negative_ratio: NonEmptyString = Field(alias="negativeRatio")
    peak_day: NonEmptyString = Field(alias="peakDay")


class _CatalogEntry(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: NonEmptyString
    title: NonEmptyString
    report_type: ReportType = Field(alias="reportType")
    language: Language
    topic: NonEmptyString
    date_range: _CatalogDateRange = Field(alias="dateRange")
    sections: NonNegativeInteger
    charts: NonNegativeInteger
    stats: _CatalogStats
    file: NonEmptyString
    generated_at: datetime = Field(alias="generatedAt")

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if Path(value).name != value or value in {".", ".."}:
            raise ValueError("invalid report ID")
        return value

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("generatedAt must include a UTC offset")
        return value


class CatalogPublisher:
    """Add complete report metadata to ``out/index.json`` atomically."""

    _lock = threading.Lock()

    def __init__(
        self,
        replace: Callable[[Path, Path], None] = os.replace,
    ) -> None:
        self._replace = replace

    def publish(self, bundle_path: Path, output_root: Path) -> Path:
        output_root = Path(output_root)
        bundle_path = Path(bundle_path)
        metadata, entry = self._read_bundle_metadata(bundle_path, output_root)
        index_path = output_root / "index.json"

        with self._lock:
            existing = self._read_existing(index_path)
            by_id = {validated.id: raw for raw, validated in existing}
            current = by_id.get(entry.id)
            if current is not None:
                if current == metadata:
                    return index_path
                raise CatalogPublicationError(
                    "Existing report catalog has a conflicting report ID"
                )

            combined = [*existing, (metadata, entry)]
            combined.sort(
                key=lambda item: (-item[1].generated_at.timestamp(), item[1].id)
            )
            self._write_atomically(
                index_path,
                [raw for raw, _validated in combined],
            )

        return index_path

    @staticmethod
    def _read_bundle_metadata(
        bundle_path: Path,
        output_root: Path,
    ) -> tuple[dict[str, Any], _CatalogEntry]:
        try:
            resolved_root = output_root.resolve(strict=True)
            resolved_bundle = bundle_path.resolve(strict=True)
        except OSError:
            raise CatalogPublicationError("Invalid published report bundle") from None

        required_files = ("report.md", "report.pdf", "meta.json")
        if (
            not resolved_bundle.is_dir()
            or resolved_bundle.parent != resolved_root
            or not (resolved_bundle / "charts").is_dir()
            or any(not (resolved_bundle / name).is_file() for name in required_files)
        ):
            raise CatalogPublicationError("Invalid published report bundle")

        try:
            raw = json.loads(
                (resolved_bundle / "meta.json").read_text(encoding="utf-8")
            )
            if not isinstance(raw, dict):
                raise ValueError
            entry = _CatalogEntry.model_validate(raw)
            if entry.id != resolved_bundle.name:
                raise ValueError
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            raise CatalogPublicationError("Invalid bundle metadata") from None

        return raw, entry

    @staticmethod
    def _read_existing(
        index_path: Path,
    ) -> list[tuple[dict[str, Any], _CatalogEntry]]:
        if not index_path.exists():
            return []

        try:
            raw_catalog = json.loads(index_path.read_text(encoding="utf-8"))
            if not isinstance(raw_catalog, list):
                raise ValueError
            entries: list[tuple[dict[str, Any], _CatalogEntry]] = []
            seen: set[str] = set()
            for raw in raw_catalog:
                if not isinstance(raw, dict):
                    raise ValueError
                entry = _CatalogEntry.model_validate(raw)
                if entry.id in seen:
                    raise CatalogPublicationError(
                        "Existing report catalog contains a duplicate report ID"
                    )
                seen.add(entry.id)
                entries.append((raw, entry))
            return entries
        except CatalogPublicationError:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            raise CatalogPublicationError("Invalid existing report catalog") from None

    def _write_atomically(
        self,
        index_path: Path,
        entries: list[dict[str, Any]],
    ) -> None:
        temporary = index_path.parent / f".index-{uuid4().hex}.tmp"
        try:
            with temporary.open("x", encoding="utf-8") as handle:
                json.dump(entries, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            self._replace(temporary, index_path)
        except (OSError, TypeError, ValueError):
            raise CatalogPublicationError("Could not update report catalog") from None
        finally:
            temporary.unlink(missing_ok=True)
