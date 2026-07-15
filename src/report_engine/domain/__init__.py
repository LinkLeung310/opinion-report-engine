"""Domain objects shared by report-engine adapters."""

from report_engine.domain.facts import Fact, FactSet
from report_engine.domain.results import SectionResult, SectionStatus
from report_engine.domain.scope import AnalysisScope

__all__ = ["AnalysisScope", "Fact", "FactSet", "SectionResult", "SectionStatus"]
