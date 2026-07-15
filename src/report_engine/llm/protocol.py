"""The only model-facing interface used by report sections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from report_engine.config import Language, SectionId
from report_engine.domain.evidence import EvidenceSet
from report_engine.domain.facts import FactSet


@dataclass(frozen=True)
class NarrationRequest:
    section_id: SectionId
    language: Language
    facts: FactSet
    evidence: EvidenceSet = EvidenceSet()


class Narrator(Protocol):
    def narrate(self, request: NarrationRequest) -> str: ...
