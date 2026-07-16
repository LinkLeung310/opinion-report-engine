"""Domain objects shared by report-engine adapters."""

from report_engine.domain.facts import Fact, FactSet
from report_engine.domain.results import SectionResult, SectionStatus
from report_engine.domain.scope import AnalysisScope
from report_engine.domain.user_context import UserContext, VerificationStatus

__all__ = [
    "AnalysisScope",
    "Fact",
    "FactSet",
    "SectionResult",
    "SectionStatus",
    "UserContext",
    "VerificationStatus",
]
