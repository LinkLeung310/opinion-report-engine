"""Language-model boundary and injectable provider adapters."""

from report_engine.llm.openai_compatible import OpenAICompatibleNarrator
from report_engine.llm.protocol import NarrationRequest, Narrator
from report_engine.llm.stub import StubNarrator

__all__ = [
    "NarrationRequest",
    "Narrator",
    "OpenAICompatibleNarrator",
    "StubNarrator",
]
