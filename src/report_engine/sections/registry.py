"""Registry for the project's 19 report-section product definitions."""

from __future__ import annotations

from collections.abc import Iterable

from report_engine.config import SectionId
from report_engine.sections.base import SectionDefinition


class SectionRegistry:
    def __init__(self, definitions: Iterable[SectionDefinition]) -> None:
        self._definitions = {definition.id: definition for definition in definitions}
        if len(self._definitions) != len(SectionId):
            raise ValueError("registry must define every section ID exactly once")

    def get(self, section_id: SectionId) -> SectionDefinition:
        return self._definitions[section_id]


def default_registry() -> SectionRegistry:
    required_inputs = {
        SectionId.RESPONSE: ("responseDate",),
        SectionId.BENCHMARK: ("comparisonTag",),
        SectionId.BIZ_IMPACT: ("notes",),
    }
    return SectionRegistry(
        SectionDefinition(
            id=section_id,
            required_inputs=required_inputs.get(section_id, ()),
        )
        for section_id in SectionId
    )
