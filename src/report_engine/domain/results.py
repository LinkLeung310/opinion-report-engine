"""Stable section outcomes used by renderers, metadata, and API status."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from report_engine.config import SectionId
from report_engine.domain.evidence import EvidenceSet
from report_engine.domain.facts import FactSet


class SectionStatus(StrEnum):
    COMPLETE = "complete"
    NO_DATA = "no_data"
    FAILED = "failed"


class FailureStage(StrEnum):
    INPUT = "input"
    QUERY = "query"
    CALCULATION = "calculation"
    CHART = "chart"
    LLM = "llm"


@dataclass(frozen=True)
class SectionFailure:
    stage: FailureStage
    message: str


@dataclass(frozen=True)
class SectionResult:
    section_id: SectionId
    status: SectionStatus
    markdown: str
    facts: FactSet | None = None
    evidence: EvidenceSet = EvidenceSet()
    charts: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    failure: SectionFailure | None = None
