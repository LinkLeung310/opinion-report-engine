"""Static definition of one user-selectable report section."""

from __future__ import annotations

from dataclasses import dataclass

from report_engine.config import SectionId


@dataclass(frozen=True)
class SectionDefinition:
    id: SectionId
    required_inputs: tuple[str, ...] = ()
