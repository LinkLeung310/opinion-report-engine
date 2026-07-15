"""Deterministic narrator for automated tests and offline development."""

from __future__ import annotations

from collections.abc import Iterable

from report_engine.config import Language, SectionId
from report_engine.llm.protocol import NarrationRequest


class StubNarrator:
    def __init__(self, fail_sections: Iterable[SectionId] = ()) -> None:
        self._fail_sections = frozenset(fail_sections)
        self.requests: list[NarrationRequest] = []

    def narrate(self, request: NarrationRequest) -> str:
        self.requests.append(request)
        if request.section_id in self._fail_sections:
            raise TimeoutError("synthetic provider response containing secret details")

        values = request.facts.prompt_values()
        if request.section_id is SectionId.VERDICT:
            if request.language is Language.EN:
                risk = {"low": "low", "medium": "medium", "high": "high"}[
                    values["riskLevel"]
                ]
                momentum = {
                    "cooling": "cooling",
                    "easing": "easing",
                    "sustained": "remaining elevated",
                }[values["momentum"]]
                return (
                    "## Executive verdict\n\n"
                    f"The computed risk level is {risk}. Negative items account for "
                    f"{values['negativeRatio']}; high-risk items represent "
                    f"{values['highRiskNegativeRatio']} of negative coverage.\n\n"
                    f"- Discussion peaks on {values['peakDay']} with "
                    f"{values['peakArticles']} items.\n"
                    f"- The final day records {values['finalDayArticles']} items, or "
                    f"{values['latestVsPeakRatio']} of the peak; momentum is {momentum}."
                )

            risk = {"low": "低", "medium": "中", "high": "高"}[
                values["riskLevel"]
            ]
            momentum = {
                "cooling": "回落",
                "easing": "缓和",
                "sustained": "高位持续",
            }[values["momentum"]]
            return (
                "## 核心结论\n\n"
                f"代码判定当前风险等级为{risk}。负面内容占比为 "
                f"{values['negativeRatio']}，其中高风险内容占全部负面内容的 "
                f"{values['highRiskNegativeRatio']}。\n\n"
                f"- 讨论于 {values['peakDay']} 达峰，峰值日共有 "
                f"{values['peakArticles']} 篇内容。\n"
                f"- 截止日共有 {values['finalDayArticles']} 篇，为峰值的 "
                f"{values['latestVsPeakRatio']}，热度处于{momentum}状态。"
            )

        if request.section_id is SectionId.METRICS:
            if request.language is Language.EN:
                return (
                    "## Network overview\n\n"
                    f"The monitoring window contains {values['articles']} items across "
                    f"{values['platforms']} platforms. Negative coverage accounts for "
                    f"{values['negativeRatio']}, while total engagement reaches "
                    f"{values['engagement']}. Discussion peaks on {values['peakDay']} "
                    f"with {values['peakArticles']} items."
                )
            return (
                "## 全网数据概览\n\n"
                f"监测期内共收集 {values['articles']} 篇相关内容，覆盖 "
                f"{values['platforms']} 个平台。负面内容占比为 "
                f"{values['negativeRatio']}，互动总量达到 {values['engagement']}。"
                f"讨论于 {values['peakDay']} 达到峰值，当日共有 "
                f"{values['peakArticles']} 篇相关内容。"
            )

        approved_facts = "；".join(
            f"{key}：{value}" for key, value in values.items()
        )
        return f"## {request.section_id.value}\n\n{approved_facts}。"
