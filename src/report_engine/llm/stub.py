"""Deterministic narrator for automated tests and offline development."""

from __future__ import annotations

from collections.abc import Iterable

from report_engine.config import SectionId
from report_engine.llm.protocol import NarrationRequest


class StubNarrator:
    def __init__(self, fail_sections: Iterable[SectionId] = ()) -> None:
        self._fail_sections = frozenset(fail_sections)
        self.requests: list[NarrationRequest] = []

    def narrate(self, request: NarrationRequest) -> str:
        self.requests.append(request)
        if request.section_id in self._fail_sections:
            raise TimeoutError("synthetic provider response containing secret details")

        approved_facts = "；".join(
            f"{key}：{value}" for key, value in request.facts.prompt_values().items()
        )
        return f"## {request.section_id.value}\n\n{approved_facts}。"
