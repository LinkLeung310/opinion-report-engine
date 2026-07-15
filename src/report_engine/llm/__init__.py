"""Injectable narrative adapters."""

from report_engine.llm.protocol import NarrationRequest, Narrator
from report_engine.llm.stub import StubNarrator

__all__ = ["NarrationRequest", "Narrator", "StubNarrator"]
