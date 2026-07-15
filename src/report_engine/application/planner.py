"""Convert a valid public config into an ordered, executable report plan."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from report_engine.config import ReportConfig, SectionId
from report_engine.domain.scope import AnalysisScope
from report_engine.sections.base import SectionDefinition
from report_engine.sections.registry import SectionRegistry


@dataclass(frozen=True)
class PlannedSection:
    definition: SectionDefinition
    input: dict[str, Any]
    input_errors: tuple[str, ...] = ()

    @property
    def id(self) -> SectionId:
        return self.definition.id

    @property
    def can_execute(self) -> bool:
        return not self.input_errors


@dataclass(frozen=True)
class ExecutionPlan:
    scope: AnalysisScope
    sections: tuple[PlannedSection, ...]
    warnings: tuple[str, ...] = ()


class ReportPlanner:
    def __init__(self, registry: SectionRegistry) -> None:
        self._registry = registry

    def build(self, config: ReportConfig) -> ExecutionPlan:
        sections: list[PlannedSection] = []
        for configured_section in config.sections:
            if not configured_section.enabled:
                continue

            definition = self._registry.get(configured_section.id)
            section_input = dict(configured_section.input or {})
            missing = tuple(
                field
                for field in definition.required_inputs
                if self._is_missing(section_input.get(field))
            )
            sections.append(
                PlannedSection(
                    definition=definition,
                    input=section_input,
                    input_errors=tuple(
                        f"Missing required section input: {field}" for field in missing
                    ),
                )
            )

        return ExecutionPlan(
            scope=AnalysisScope.from_config(config),
            sections=tuple(sections),
            warnings=config.normalization_warnings,
        )

    @staticmethod
    def _is_missing(value: object) -> bool:
        return value is None or (isinstance(value, str) and not value.strip())
