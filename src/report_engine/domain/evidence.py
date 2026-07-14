"""Source evidence approved for model-assisted viewpoint synthesis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Evidence:
    record_id: str
    title: str
    summary: str
    platform: str
    published_at: datetime
    sentiment: str

    def __post_init__(self) -> None:
        if not self.title.strip() or not self.summary.strip():
            raise ValueError("evidence requires a non-empty title and summary")


@dataclass(frozen=True)
class EvidenceSet:
    records: tuple[Evidence, ...] = ()

    @property
    def record_ids(self) -> tuple[str, ...]:
        return tuple(record.record_id for record in self.records)
