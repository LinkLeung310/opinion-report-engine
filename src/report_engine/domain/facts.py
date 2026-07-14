"""Auditable facts shared by narratives, charts, and deterministic rendering."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


FactValue = str | int | float | Decimal | date | datetime | None


@dataclass(frozen=True)
class Fact:
    key: str
    raw_value: FactValue
    formatted_value: str
    source_id: str
    source_record_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class FactSet:
    facts: tuple[Fact, ...]

    def __post_init__(self) -> None:
        keys = [fact.key for fact in self.facts]
        if len(keys) != len(set(keys)):
            raise ValueError("FactSet keys must be unique")

    def get(self, key: str) -> Fact:
        for fact in self.facts:
            if fact.key == key:
                return fact
        raise KeyError(key)

    def prompt_values(self) -> dict[str, str]:
        """Expose approved display values without asking the model to calculate."""

        return {fact.key: fact.formatted_value for fact in self.facts}
