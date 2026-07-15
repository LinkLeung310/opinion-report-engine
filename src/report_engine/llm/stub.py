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
        if request.section_id is SectionId.SEVERITY:
            evidence_lines = "\n".join(
                (
                    f"- [Evidence: {record.record_id}] {record.title}: "
                    f"{record.summary} ({record.platform})"
                    if request.language is Language.EN
                    else f"- [Evidence: {record.record_id}] {record.title}："
                    f"{record.summary}（{record.platform}）"
                )
                for record in request.evidence.records
            )
            if request.language is Language.EN:
                return (
                    "## Negative severity\n\n"
                    f"The scope contains {values['negativeArticles']} negative items. "
                    f"High or critical items total {values['highCriticalArticles']} "
                    f"({values['highCriticalRatio']}); the average negative score is "
                    f"{values['averageNegativeScore']}. High or critical items account "
                    f"for {values['highCriticalEngagementShare']} of negative engagement. "
                    f"Missing severity labels: {values['missingSeverityArticles']}; "
                    f"missing scores: {values['missingScoreArticles']}.\n\n"
                    f"{evidence_lines}"
                )
            return (
                "## 负面严重程度\n\n"
                f"监测期内共有 {values['negativeArticles']} 篇负面内容，其中高/危内容 "
                f"{values['highCriticalArticles']} 篇，占 {values['highCriticalRatio']}；"
                f"平均负面程度为 {values['averageNegativeScore']}。高/危内容贡献全部负面"
                f"互动的 {values['highCriticalEngagementShare']}。严重性标签缺失 "
                f"{values['missingSeverityArticles']} 篇，负面分数缺失 "
                f"{values['missingScoreArticles']} 篇。\n\n"
                f"{evidence_lines}"
            )

        if request.section_id is SectionId.PLATFORMS:
            tied = int(values["volumeLeaderCount"].replace(",", "")) > 1
            if request.language is Language.EN:
                volume = (
                    f"{values['volumeLeaders']} tie at {values['leadingArticleCount']} items each"
                    if tied
                    else f"{values['volumeLeaders']} leads with {values['leadingArticleCount']} items"
                )
                negative = (
                    f"- {values['negativeLeader']} contributes "
                    f"{values['negativeLeaderArticles']} negative items, or "
                    f"{values['negativeLeaderShare']} of all negative coverage; its "
                    f"within-platform negative ratio is {values['negativeLeaderRatio']}.\n"
                    if "negativeLeader" in values
                    else "- No negative items appear in the selected scope.\n"
                )
                return (
                    "## Platform performance\n\n"
                    f"The scope contains {values['articles']} items across "
                    f"{values['platformCount']} platforms.\n\n"
                    f"- {volume}, representing {values['leadingArticleShare']} per leader.\n"
                    f"{negative}"
                    f"- {values['engagementLeader']} leads engagement with "
                    f"{values['engagementLeaderTotal']}, or "
                    f"{values['engagementLeaderShare']} of the total and "
                    f"{values['engagementLeaderPerArticle']} per item."
                )

            volume = (
                f"{values['volumeLeaders']}均为 {values['leadingArticleCount']} 篇，并列第一"
                if tied
                else f"{values['volumeLeaders']}以 {values['leadingArticleCount']} 篇居首"
            )
            negative = (
                f"- {values['negativeLeader']}有 {values['negativeLeaderArticles']} 篇负面内容，"
                f"占全部负面内容的 {values['negativeLeaderShare']}，平台内负面占比为 "
                f"{values['negativeLeaderRatio']}。\n"
                if "negativeLeader" in values
                else "- 监测范围内未发现负面内容。\n"
            )
            return (
                "## 平台表现\n\n"
                f"监测期内 {values['articles']} 篇内容分布于 "
                f"{values['platformCount']} 个平台。\n\n"
                f"- {volume}，每个平台占总量的 {values['leadingArticleShare']}。\n"
                f"{negative}"
                f"- {values['engagementLeader']}互动量最高，达到 "
                f"{values['engagementLeaderTotal']}，占总互动的 "
                f"{values['engagementLeaderShare']}，篇均互动 "
                f"{values['engagementLeaderPerArticle']}。"
            )

        if request.section_id is SectionId.TREND:
            if request.language is Language.EN:
                return (
                    "## Heat trend\n\n"
                    f"Discussion peaks on {values['peakDay']} with {values['peakArticles']} "
                    f"items, representing {values['peakShare']} of all coverage. "
                    f"Activity appears on {values['activeDays']} of {values['calendarDays']} "
                    f"calendar days. The final day records {values['finalDayArticles']} "
                    f"items, or {values['finalVsPeakRatio']} of the peak."
                )
            return (
                "## 热度趋势\n\n"
                f"讨论于 {values['peakDay']} 达峰，峰值日共有 "
                f"{values['peakArticles']} 篇内容，占监测期总量的 "
                f"{values['peakShare']}。{values['calendarDays']} 个日历日中有 "
                f"{values['activeDays']} 日出现相关内容；截止日共有 "
                f"{values['finalDayArticles']} 篇，为峰值的 "
                f"{values['finalVsPeakRatio']}。"
            )

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
