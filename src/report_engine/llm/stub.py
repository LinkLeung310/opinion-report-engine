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
        if request.section_id is SectionId.SPREAD_PATH:
            sentiments_en = {
                "positive": "positive",
                "neutral": "neutral",
                "negative": "negative",
            }
            platform_lines = []
            for index, evidence in enumerate(request.evidence.records, start=1):
                prefix = f"platform{index}"
                if request.language is Language.EN:
                    sentiment = sentiments_en[
                        request.facts.get(f"{prefix}FirstSentiment").raw_value
                    ]
                    platform_lines.append(
                        f"- wave {values[f'{prefix}EntryWave']} | "
                        f"{values[f'{prefix}Name']} | first "
                        f"{values[f'{prefix}FirstObservedAt']} | last "
                        f"{values[f'{prefix}LastObservedAt']} | "
                        f"{values[f'{prefix}Articles']} records "
                        f"({values[f'{prefix}NegativeArticles']} negative) | "
                        f"{values[f'{prefix}ActiveDays']} active days | stored "
                        f"interactions {values[f'{prefix}TotalEngagement']}. First "
                        f"captured record [Evidence: {evidence.record_id}] "
                        f"{sentiment} | {evidence.title}: {evidence.summary}"
                    )
                else:
                    platform_lines.append(
                        f"- 波次 {values[f'{prefix}EntryWave']}｜"
                        f"{values[f'{prefix}Name']}｜首次 "
                        f"{values[f'{prefix}FirstObservedAt']}｜末次 "
                        f"{values[f'{prefix}LastObservedAt']}｜"
                        f"{values[f'{prefix}Articles']} 篇（负面 "
                        f"{values[f'{prefix}NegativeArticles']} 篇）｜活跃 "
                        f"{values[f'{prefix}ActiveDays']} 日｜存储互动 "
                        f"{values[f'{prefix}TotalEngagement']}。首收录记录 "
                        f"[Evidence: {evidence.record_id}] "
                        f"{values[f'{prefix}FirstSentiment']}｜"
                        f"{evidence.title}：{evidence.summary}"
                    )
            lines = "\n".join(platform_lines)
            if request.language is Language.EN:
                return (
                    "## Propagation path (observable order)\n\n"
                    f"Across {values['articles']} scoped records, "
                    f"{values['platformCount']} platforms are observed; "
                    f"{values['displayPlatformCount']} are displayed and "
                    f"{values['omittedPlatformCount']} omitted. Across "
                    f"{values['calendarDays']} calendar days, "
                    f"{values['multiPlatformDays']} contain multiple platforms. The "
                    f"same-day maximum is {values['maxDailyPlatforms']} platforms on "
                    f"{values['maxDailyPlatformDays']}. Displayed platforms form "
                    f"{values['entryWaveCount']} first-capture waves; the earliest "
                    f"platform set is {values['earliestPlatforms']} and the latest new "
                    f"platform set is {values['latestNewPlatforms']}, separated by "
                    f"{values['firstObservationIntervalHours']} hours.\n\n{lines}\n\n"
                    "The database has no repost, quote, parent, referral, or source-edge "
                    "fields. This is captured first-observation order and platform "
                    "participation only, not event origin, a transmission chain, "
                    "audience movement, or causal platform influence."
                )
            return (
                "## 传播路径（可观测顺序）\n\n"
                f"监测期内 {values['articles']} 篇内容覆盖 "
                f"{values['platformCount']} 个平台，显示 "
                f"{values['displayPlatformCount']} 个、省略 "
                f"{values['omittedPlatformCount']} 个；"
                f"{values['calendarDays']} 个日历日中有 "
                f"{values['multiPlatformDays']} 个多平台日，单日最多 "
                f"{values['maxDailyPlatforms']} 个平台，出现在 "
                f"{values['maxDailyPlatformDays']}。显示平台形成 "
                f"{values['entryWaveCount']} 个首次收录波次；最早平台为 "
                f"{values['earliestPlatforms']}，最后新出现平台为 "
                f"{values['latestNewPlatforms']}，首收录间隔 "
                f"{values['firstObservationIntervalHours']} 小时。\n\n{lines}\n\n"
                "数据库没有转载、引用、父子、引流或来源边字段；以上只表示本监测范围"
                "内的首次收录顺序和平台参与轨迹，不代表事件起源、传播链、受众迁移或"
                "平台间因果影响。"
            )

        if request.section_id is SectionId.NEGATIVE_THEMES:
            labels_en = {
                "user_agency": "User agency and control",
                "transparency": "Transparency and explanation",
                "feedback_effectiveness": "Feedback effectiveness",
            }
            evidence_by_id = {
                evidence.record_id: evidence for evidence in request.evidence.records
            }
            theme_lines = []
            theme_count = int(values["displayThemeCount"].replace(",", ""))
            for index in range(1, theme_count + 1):
                prefix = f"theme{index}"
                representative_id = values[f"{prefix}RepresentativeId"]
                evidence = evidence_by_id[representative_id]
                if request.language is Language.EN:
                    label = labels_en[request.facts.get(f"{prefix}Id").raw_value]
                    theme_lines.append(
                        f"- {label}: {values[f'{prefix}Articles']} of "
                        f"{values['negativeArticles']} negative records "
                        f"({values[f'{prefix}Share']}); concern "
                        f"{values[f'{prefix}ConcernArticles']}, demand "
                        f"{values[f'{prefix}DemandArticles']}, and high/critical "
                        f"{values[f'{prefix}HighCriticalArticles']} "
                        f"({values[f'{prefix}HighCriticalShare']}). Exact indicators: "
                        f"{values[f'{prefix}Indicators']}. Representative "
                        f"[Evidence: {evidence.record_id}] {evidence.platform} | "
                        f"{evidence.title}: {evidence.summary}"
                    )
                else:
                    theme_lines.append(
                        f"- {values[f'{prefix}Label']}：覆盖负面内容 "
                        f"{values[f'{prefix}Articles']}/{values['negativeArticles']} 篇（"
                        f"{values[f'{prefix}Share']}）；关切 "
                        f"{values[f'{prefix}ConcernArticles']} 篇、诉求 "
                        f"{values[f'{prefix}DemandArticles']} 篇，高/危 "
                        f"{values[f'{prefix}HighCriticalArticles']} 篇（"
                        f"{values[f'{prefix}HighCriticalShare']}）；匹配指标："
                        f"{values[f'{prefix}Indicators']}。代表记录 "
                        f"[Evidence: {evidence.record_id}] {evidence.platform}｜"
                        f"{evidence.title}：{evidence.summary}"
                    )
            lines = "\n".join(theme_lines)
            if request.language is Language.EN:
                return (
                    "## Negative issue themes\n\n"
                    f"Among {values['articles']} scoped records, "
                    f"{values['negativeArticles']} are negative. The versioned exact-"
                    f"indicator codebook classifies {values['classifiedNegativeArticles']} "
                    f"({values['classifiedNegativeShare']}) and leaves "
                    f"{values['unclassifiedNegativeArticles']} "
                    f"({values['unclassifiedNegativeShare']}) unclassified. "
                    f"{values['displayThemeCount']} fixed dimensions are displayed across "
                    f"{values['totalThemeMemberships']} overlapping memberships.\n\n"
                    f"{lines}\n\nThemes and concern/demand roles may overlap. This is "
                    "a versioned exact-indicator baseline over captured summaries; it "
                    "does not establish root causes, audience segments, verified harm, "
                    "or prevalence outside the monitored records."
                )
            return (
                "## 负面议题拆解\n\n"
                f"监测范围内 {values['articles']} 篇内容中有 "
                f"{values['negativeArticles']} 篇负面内容；版本化精确指标码表分类 "
                f"{values['classifiedNegativeArticles']} 篇（"
                f"{values['classifiedNegativeShare']}），未分类 "
                f"{values['unclassifiedNegativeArticles']} 篇（"
                f"{values['unclassifiedNegativeShare']}）。本章展示 "
                f"{values['displayThemeCount']} 个固定议题维度，共记录 "
                f"{values['totalThemeMemberships']} 次可重叠主题归属。\n\n{lines}\n\n"
                "议题以及关切/诉求角色均可重叠。本结果是对收录摘要应用版本化精确"
                "指标码表的基线，不代表根因、受众分群、已验证伤害或监测范围外的普遍程度。"
            )

        if request.section_id is SectionId.TOP_CONTENT:
            categories_en = {
                "dual_signal": "dual-signal representative",
                "engagement_only": "engagement-only representative",
                "risk_only": "risk-only representative",
            }
            sentiments_en = {
                "positive": "positive",
                "neutral": "neutral",
                "negative": "negative",
            }
            severities_en = {
                None: "unclassified",
                "low": "low",
                "medium": "medium",
                "high": "high",
                "critical": "critical",
            }
            evidence_lines = []
            for index, evidence in enumerate(request.evidence.records, start=1):
                prefix = f"record{index}"
                engagement_rank_raw = request.facts.get(
                    f"{prefix}EngagementRank"
                ).raw_value
                risk_rank_raw = request.facts.get(f"{prefix}RiskRank").raw_value
                severity_raw = request.facts.get(f"{prefix}Severity").raw_value
                score_raw = request.facts.get(f"{prefix}NegativeScore").raw_value
                if request.language is Language.EN:
                    severity = (
                        "not applicable"
                        if evidence.sentiment != "negative"
                        else severities_en[severity_raw]
                    )
                    evidence_lines.append(
                        f"- [Evidence: {evidence.record_id}] "
                        f"{categories_en[request.facts.get(f'{prefix}Category').raw_value]} | "
                        f"engagement rank "
                        f"{engagement_rank_raw if engagement_rank_raw is not None else 'unranked'} | "
                        f"risk rank {risk_rank_raw if risk_rank_raw is not None else 'unranked'} | "
                        f"{values[f'{prefix}Platform']} | "
                        f"{sentiments_en[evidence.sentiment]} | "
                        f"{evidence.title}: {evidence.summary} | stored interactions "
                        f"{values[f'{prefix}TotalEngagement']} | severity {severity} | "
                        f"negative score {score_raw if score_raw is not None else 'unavailable'}"
                    )
                else:
                    evidence_lines.append(
                        f"- [Evidence: {evidence.record_id}] "
                        f"{values[f'{prefix}Category']}｜互动排名 "
                        f"{values[f'{prefix}EngagementRank']}｜风险排名 "
                        f"{values[f'{prefix}RiskRank']}｜"
                        f"{values[f'{prefix}Platform']}｜"
                        f"{values[f'{prefix}Sentiment']}｜"
                        f"{evidence.title}：{evidence.summary}｜存储互动 "
                        f"{values[f'{prefix}TotalEngagement']}｜严重性 "
                        f"{values[f'{prefix}Severity']}｜负面分 "
                        f"{values[f'{prefix}NegativeScore']}"
                    )
            lines = "\n".join(evidence_lines)
            if request.language is Language.EN:
                return (
                    "## Representative content\n\n"
                    f"Across {values['articles']} captured records, "
                    f"{values['positiveEngagementArticles']} have positive stored "
                    f"interaction counters and {values['highRiskSignalArticles']} "
                    "meet the explicit high-risk-signal rule. The deduplicated "
                    f"shortlist contains {values['selectedCount']} records: "
                    f"{values['dualSignalCount']} dual-signal representatives, "
                    f"{values['engagementOnlyCount']} engagement-only, and "
                    f"{values['riskOnlyCount']} risk-only. Their stored interactions "
                    f"total {values['selectedEngagement']} "
                    f"({values['selectedEngagementShare']} of all stored interactions).\n\n"
                    f"{lines}\n\nInteraction-counter definitions may differ by "
                    "platform. The risk role is triggered only by supplied structured "
                    "fields; neither signal establishes reach, support, business "
                    "consequences, harm, or causality."
                )
            return (
                "## 代表性内容\n\n"
                f"监测期内 {values['articles']} 篇内容中，"
                f"{values['positiveEngagementArticles']} 篇有正向存储互动，"
                f"{values['highRiskSignalArticles']} 篇符合明确高风险信号规则；"
                f"入选 {values['selectedCount']} 篇去重代表内容：双信号 "
                f"{values['dualSignalCount']} 篇、仅高互动 "
                f"{values['engagementOnlyCount']} 篇、仅高风险 "
                f"{values['riskOnlyCount']} 篇。入选内容存储互动合计 "
                f"{values['selectedEngagement']}（占全部存储互动 "
                f"{values['selectedEngagementShare']}）。\n\n{lines}\n\n"
                "不同平台的互动计数口径可能不同；高风险角色只由数据库提供的结构化"
                "字段触发，不能据此推断触达、支持度、业务后果、伤害或因果影响。"
            )

        if request.section_id is SectionId.TIMELINE:
            role_labels_en = {
                "first_observed": "first observed",
                "tagged_response": "response-tagged record",
                "peak_day_representative": "peak-day representative",
                "last_observed": "last observed",
            }
            sentiment_labels_en = {
                "positive": "positive",
                "neutral": "neutral",
                "negative": "negative",
            }
            evidence_lines = []
            for index, evidence in enumerate(request.evidence.records, start=1):
                prefix = f"milestone{index}"
                peak_key = f"{prefix}PeakEngagement"
                role_keys = values[f"{prefix}RoleKeys"].split(",")
                if request.language is Language.EN:
                    roles = ", ".join(role_labels_en[role] for role in role_keys)
                    engagement = (
                        f" Captured engagement-counter snapshot: {values[peak_key]}."
                        if peak_key in values
                        else ""
                    )
                    evidence_lines.append(
                        f"- [Evidence: {evidence.record_id}] "
                        f"{values[f'{prefix}PublishedAt']} | {roles} | "
                        f"{values[f'{prefix}Platform']} | "
                        f"{sentiment_labels_en[evidence.sentiment]} | "
                        f"{evidence.title}: {evidence.summary}{engagement}"
                    )
                else:
                    engagement = (
                        f" 存储互动计数快照：{values[peak_key]}。"
                        if peak_key in values
                        else ""
                    )
                    evidence_lines.append(
                        f"- [Evidence: {evidence.record_id}] "
                        f"{values[f'{prefix}PublishedAt']}｜"
                        f"{values[f'{prefix}Roles']}｜"
                        f"{values[f'{prefix}Platform']}｜"
                        f"{values[f'{prefix}Sentiment']}｜"
                        f"{evidence.title}：{evidence.summary}{engagement}"
                    )
            lines = "\n".join(evidence_lines)
            if request.language is Language.EN:
                response_note = (
                    f"The scope contains {values['responseTaggedArticles']} record "
                    "with the exact official-response tag; the earliest one is shown."
                    if values["responseTaggedArticles"] != "0"
                    else "No scoped record carries the exact official-response tag; "
                    "this does not establish that no response occurred."
                )
                return (
                    "## Event timeline\n\n"
                    f"Across {values['articles']} captured records, the volume peak is "
                    f"{values['peakDay']} with {values['peakArticles']} records. The "
                    f"first-to-last observed span is {values['observedCalendarDays']} "
                    f"calendar days, represented by {values['milestoneCount']} "
                    f"deduplicated milestones. {response_note}\n\n{lines}\n\n"
                    "The order is an observed chronology, not evidence of causality, "
                    "speaker authority, response effectiveness, reach, or impact."
                )
            response_note = (
                f"范围内有 {values['responseTaggedArticles']} 篇带精确 "
                "official-response 标签的记录，时间线展示其中最早一篇。"
                if values["responseTaggedArticles"] != "0"
                else "范围内没有带精确 official-response 标签的记录；这不等于没有发生回应。"
            )
            return (
                "## 事件时间线\n\n"
                f"监测期内共 {values['articles']} 篇收录内容，讨论量于 "
                f"{values['peakDay']} 达峰，当日 {values['peakArticles']} 篇。"
                f"首末收录跨 {values['observedCalendarDays']} 个自然日，去重后展示 "
                f"{values['milestoneCount']} 个里程碑。{response_note}\n\n"
                f"{lines}\n\n以上顺序仅表示可观测收录时间，不证明因果、发言者权威性、"
                "回应效果、触达或影响。"
            )

        if request.section_id is SectionId.MEDIA_SOCIAL:
            comparable = values["comparisonStatus"] == "comparable"
            if request.language is Language.EN:
                volume = (
                    f"Across {values['articles']} captured records, media contains "
                    f"{values['mediaArticles']} ({values['mediaArticleShare']}) and "
                    f"social contains {values['socialArticles']} "
                    f"({values['socialArticleShare']})."
                )
                if comparable:
                    comparison = (
                        f"Media has {values['mediaNegativeArticles']} negative records "
                        f"among {values['mediaArticles']} ({values['mediaNegativeShare']}), "
                        f"while social has {values['socialNegativeArticles']} among "
                        f"{values['socialArticles']} ({values['socialNegativeShare']}); "
                        f"social minus media is "
                        f"{values['socialMinusMediaNegativeShare']}."
                    )
                else:
                    comparison = (
                        "Only one stored source type has samples, so the cross-group "
                        "sentiment comparison is unavailable."
                    )
                return (
                    "## Media and social\n\n"
                    f"{volume} {comparison}\n\nThe classification comes from the "
                    "database source_type field. These captured records do not establish "
                    "audience demographics, causes, or the full media ecosystem."
                )
            volume = (
                f"监测期内共 {values['articles']} 篇收录内容：媒体内容 "
                f"{values['mediaArticles']} 篇（{values['mediaArticleShare']}），"
                f"社交内容 {values['socialArticles']} 篇（"
                f"{values['socialArticleShare']}）。"
            )
            if comparable:
                comparison = (
                    f"媒体内容 {values['mediaArticles']} 篇中负面 "
                    f"{values['mediaNegativeArticles']} 篇（"
                    f"{values['mediaNegativeShare']}），社交内容 "
                    f"{values['socialArticles']} 篇中负面 "
                    f"{values['socialNegativeArticles']} 篇（"
                    f"{values['socialNegativeShare']}）；社交减媒体为 "
                    f"{values['socialMinusMediaNegativeShare']}。"
                )
            else:
                comparison = "只有一种存储来源类型有样本，跨组情感不可比较。"
            return (
                "## 媒体与社媒对比\n\n"
                f"{volume} {comparison}\n\n分类直接来自数据库 source_type 字段；"
                "结论只描述本次收录内容，不代表受众人群、差异原因或完整媒体生态。"
            )

        if request.section_id is SectionId.ENGAGEMENT:
            evidence_lines = []
            for index, evidence in enumerate(request.evidence.records, start=1):
                prefix = f"record{index}"
                if request.language is Language.EN:
                    evidence_lines.append(
                        f"- [Evidence: {evidence.record_id}] {evidence.title} "
                        f"({values[f'{prefix}Platform']}, "
                        f"{values[f'{prefix}Sentiment']}): "
                        f"{values[f'{prefix}Total']} interactions "
                        f"(likes {values[f'{prefix}Likes']}, comments "
                        f"{values[f'{prefix}Comments']}, shares "
                        f"{values[f'{prefix}Shares']}, favorites "
                        f"{values[f'{prefix}Favorites']})."
                    )
                else:
                    evidence_lines.append(
                        f"- [Evidence: {evidence.record_id}] {evidence.title}（"
                        f"{values[f'{prefix}Platform']}，"
                        f"{values[f'{prefix}Sentiment']}）：总互动 "
                        f"{values[f'{prefix}Total']}（赞 "
                        f"{values[f'{prefix}Likes']}、评 "
                        f"{values[f'{prefix}Comments']}、转 "
                        f"{values[f'{prefix}Shares']}、藏 "
                        f"{values[f'{prefix}Favorites']}）。"
                    )
            lines = "\n".join(evidence_lines)
            tied = int(values["leadingRecordCount"].replace(",", "")) > 1
            if request.language is Language.EN:
                concentration = (
                    f"{values['leadingRecordCount']} records tie at "
                    f"{values['leadingRecordTotal']} interactions; the first "
                    f"{values['topThreeRecordCount']} records represent "
                    f"{values['topThreeRecordsShare']} of the total."
                    if tied
                    else f"{values['leadingRecordId']} is the highest-count record at "
                    f"{values['leadingRecordTotal']} interactions "
                    f"({values['topRecordShare']} of the total); the first "
                    f"{values['topThreeRecordCount']} records represent "
                    f"{values['topThreeRecordsShare']}."
                )
                return (
                    "## Engagement\n\n"
                    f"Across {values['articles']} records, the stored counters total "
                    f"{values['totalEngagement']}: {values['likes']} likes, "
                    f"{values['comments']} comments, {values['shares']} shares, and "
                    f"{values['favorites']} favorites. Comments plus shares total "
                    f"{values['commentsAndShares']} "
                    f"({values['commentsAndSharesShare']}). {concentration}\n\n"
                    f"{lines}\n\nThese are raw stored counters whose definitions "
                    "may differ by platform. Without impression or unique-user "
                    "denominators, they are not engagement rate, reach, or support."
                )
            concentration = (
                f"{values['leadingRecordCount']} 篇内容并列最高，单篇均为 "
                f"{values['leadingRecordTotal']}；前 "
                f"{values['topThreeRecordCount']} 篇占总互动的 "
                f"{values['topThreeRecordsShare']}。"
                if tied
                else f"{values['leadingRecordId']} 单篇最高，为 "
                f"{values['leadingRecordTotal']}，占总互动的 "
                f"{values['topRecordShare']}；前 "
                f"{values['topThreeRecordCount']} 篇合计占 "
                f"{values['topThreeRecordsShare']}。"
            )
            return (
                "## 互动传播\n\n"
                f"监测期内 {values['articles']} 篇内容共记录原始互动 "
                f"{values['totalEngagement']}：点赞 {values['likes']}、评论 "
                f"{values['comments']}、转发 {values['shares']}、收藏 "
                f"{values['favorites']}；评论与转发合计 "
                f"{values['commentsAndShares']}（"
                f"{values['commentsAndSharesShare']}）。{concentration}\n\n"
                f"{lines}\n\n以上为不同平台存储的原始计数快照，口径可能不同；"
                "缺少曝光量和独立用户分母，不代表互动率、真实触达或支持度。"
            )

        if request.section_id is SectionId.KEYWORDS:
            display_count = int(values["displayPhraseCount"].replace(",", ""))
            lines = []
            for index in range(1, min(display_count, 5) + 1):
                prefix = f"keyword{index}"
                if request.language is Language.EN:
                    lines.append(
                        f"- {values[f'{prefix}Text']}: "
                        f"{values[f'{prefix}Documents']} articles "
                        f"({values[f'{prefix}Coverage']}), including "
                        f"{values[f'{prefix}NegativeDocuments']} negative "
                        f"({values[f'{prefix}NegativeShare']}); first seen "
                        f"{values[f'{prefix}FirstDay']}."
                    )
                else:
                    lines.append(
                        f"- {values[f'{prefix}Text']}：覆盖 "
                        f"{values[f'{prefix}Documents']} 篇（"
                        f"{values[f'{prefix}Coverage']}），其中负面 "
                        f"{values[f'{prefix}NegativeDocuments']} 篇（"
                        f"{values[f'{prefix}NegativeShare']}），首次出现于 "
                        f"{values[f'{prefix}FirstDay']}。"
                    )
            phrase_lines = "\n".join(lines)
            if request.language is Language.EN:
                emergence = (
                    f"Late-emerging recurring phrases from "
                    f"{values['lateWindowStart']}: {values['emergingPhrases']} "
                    f"({values['emergingPhraseCount']} total)."
                    if values["emergingPhraseCount"] != "0"
                    else f"From {values['lateWindowStart']}, no late-only phrase met "
                    f"the {values['minimumDocuments']}-article recurrence threshold."
                )
                return (
                    "## Keywords and topics\n\n"
                    f"Across {values['articles']} articles, deterministic extraction "
                    f"finds {values['recurringPhraseCount']} recurring exact phrases. "
                    f"{values['leadingPhraseCount']} phrases tie for the broadest "
                    f"coverage at {values['leadingDocumentCount']} articles each.\n\n"
                    f"{phrase_lines}\n\n{emergence} These are exact-phrase coverage "
                    "signals, not semantic topic clusters or measures of support."
                )
            emergence = (
                f"后半期自 {values['lateWindowStart']} 起新增重复短语为"
                f"{values['emergingPhrases']}，共 {values['emergingPhraseCount']} 项。"
                if values["emergingPhraseCount"] != "0"
                else f"后半期自 {values['lateWindowStart']} 起，没有短语满足“前半期"
                f"零出现且后半期至少 {values['minimumDocuments']} 篇”的新增阈值。"
            )
            return (
                "## 关键词与话题\n\n"
                f"从 {values['articles']} 篇标题与摘要中确定性提取出 "
                f"{values['recurringPhraseCount']} 个重复原文短语；"
                f"{values['leadingPhraseCount']} 项并列最高，均覆盖 "
                f"{values['leadingDocumentCount']} 篇。\n\n"
                f"{phrase_lines}\n\n{emergence}本章展示精确短语覆盖，不等同于"
                "语义主题聚类或公众支持度。"
            )

        if request.section_id is SectionId.SENTIMENT_EVOLUTION:
            if request.language is Language.EN:
                if values["direction"] == "仅单阶段有数据":
                    return (
                        "## Sentiment evolution\n\n"
                        f"Only {values['firstPhaseLabel']} "
                        f"({values['firstPhaseDateRange']}) contains data: "
                        f"{values['firstPhaseArticles']} items, with "
                        f"{values['firstPhaseNegativeShare']} negative. There is "
                        "insufficient information for a phase comparison. Composition "
                        "does not indicate discussion volume or renewed attention."
                    )
                return (
                    "## Sentiment evolution\n\n"
                    f"Negative share moves from {values['firstPhaseNegativeShare']} "
                    f"across {values['firstPhaseArticles']} items in "
                    f"{values['firstPhaseLabel']} ({values['firstPhaseDateRange']}) to "
                    f"{values['lastPhaseNegativeShare']} across "
                    f"{values['lastPhaseArticles']} items in "
                    f"{values['lastPhaseLabel']} ({values['lastPhaseDateRange']}), a "
                    f"change of {values['negativeShareDelta']} classified as "
                    f"{values['direction']}. Composition change does not indicate "
                    "discussion volume or renewed attention."
                )
            if values["direction"] == "仅单阶段有数据":
                return (
                    "## 情感演变\n\n"
                    f"仅{values['firstPhaseLabel']}（{values['firstPhaseDateRange']}）"
                    f"有数据，共 {values['firstPhaseArticles']} 篇，负面占比为 "
                    f"{values['firstPhaseNegativeShare']}，不足以进行阶段比较。"
                    "情感构成不代表讨论量变化或热度回升。"
                )
            return (
                "## 情感演变\n\n"
                f"{values['firstPhaseLabel']}（{values['firstPhaseDateRange']}）共 "
                f"{values['firstPhaseArticles']} 篇，负面占比 "
                f"{values['firstPhaseNegativeShare']}；"
                f"{values['lastPhaseLabel']}（{values['lastPhaseDateRange']}）共 "
                f"{values['lastPhaseArticles']} 篇，负面占比 "
                f"{values['lastPhaseNegativeShare']}，变化为 "
                f"{values['negativeShareDelta']}，判定为{values['direction']}。"
                "情感构成变化不等于讨论量上升或热度回升。"
            )

        if request.section_id is SectionId.VIEWPOINTS:
            labels = (
                {
                    "negative": "Concerns and opposition",
                    "neutral": "Neutral explanations",
                    "positive": "Support and easing signals",
                }
                if request.language is Language.EN
                else {
                    "negative": "质疑/反对",
                    "neutral": "中性/解释",
                    "positive": "支持/缓和",
                }
            )
            blocks: list[str] = []
            for sentiment in ("negative", "neutral", "positive"):
                records = [
                    record
                    for record in request.evidence.records
                    if record.sentiment == sentiment
                ]
                if not records:
                    continue
                lines = "\n".join(
                    (
                        f"- [Evidence: {record.record_id}] {record.title}: "
                        f"{record.summary} ({record.platform})"
                        if request.language is Language.EN
                        else f"- [Evidence: {record.record_id}] {record.title}："
                        f"{record.summary}（{record.platform}）"
                    )
                    for record in records
                )
                blocks.append(f"### {labels[sentiment]}\n\n{lines}")

            body = "\n\n".join(blocks)
            if request.language is Language.EN:
                return (
                    "## Main viewpoints\n\n"
                    f"The scope contains {values['articleCount']} items: "
                    f"{values['negativeArticles']} negative "
                    f"({values['negativeShare']}), {values['neutralArticles']} neutral "
                    f"({values['neutralShare']}), and {values['positiveArticles']} "
                    f"positive ({values['positiveShare']}). The records below are "
                    "representative source evidence, not a complete theme census or "
                    "an estimate of viewpoint prevalence.\n\n"
                    f"{body}"
                )
            return (
                "## 主要观点\n\n"
                f"监测期内共 {values['articleCount']} 篇内容：负面 "
                f"{values['negativeArticles']} 篇（{values['negativeShare']}）、中性 "
                f"{values['neutralArticles']} 篇（{values['neutralShare']}）、正面 "
                f"{values['positiveArticles']} 篇（{values['positiveShare']}）。"
                "以下为代表性原始证据，不是完整主题普查，也不用于估计观点流行度。\n\n"
                f"{body}"
            )

        if request.section_id is SectionId.RISK:
            if request.language is Language.EN:
                band_en = {"低": "low", "中": "medium", "高": "high"}
                return (
                    "## Risk assessment\n\n"
                    f"The {values['evaluatedSignalCount']} equally weighted structured "
                    f"signals produce a {values['riskSignalIndex']} diagnostic index, "
                    f"classified as {band_en[values['riskLevel']]}. This is a "
                    "non-probability diagnostic, not an event probability or forecast.\n\n"
                    f"- Sentiment pressure is {values['sentimentPressure']} "
                    f"({band_en[values['sentimentPressureBand']]}), while severity "
                    f"pressure is {values['severityPressure']} "
                    f"({band_en[values['severityPressureBand']]}).\n"
                    f"- Spread pressure is {values['spreadPressure']} "
                    f"({band_en[values['spreadPressureBand']]}), while persistence "
                    f"pressure is {values['persistencePressure']} "
                    f"({band_en[values['persistencePressureBand']]}).\n"
                    f"- Amplification pressure is {values['amplificationPressure']} "
                    f"({band_en[values['amplificationPressureBand']]}).\n\n"
                    "Data capability boundary: executive association and rumor "
                    "verification fields are unavailable and excluded from the index."
                )
            return (
                "## 风险评估\n\n"
                f"{values['evaluatedSignalCount']} 项结构化信号的等权诊断指数为 "
                f"{values['riskSignalIndex']}，档位为{values['riskLevel']}。这是"
                f"{values['diagnosticKind']}，用于比较监测数据中的信号强度，不代表"
                "事件发生概率或趋势预测。\n\n"
                f"- 负面情绪压力为 {values['sentimentPressure']}（"
                f"{values['sentimentPressureBand']}），高危程度压力为 "
                f"{values['severityPressure']}（{values['severityPressureBand']}）。\n"
                f"- 平台扩散压力为 {values['spreadPressure']}（"
                f"{values['spreadPressureBand']}），持续覆盖压力为 "
                f"{values['persistencePressure']}（{values['persistencePressureBand']}）。\n"
                f"- 互动放大压力为 {values['amplificationPressure']}（"
                f"{values['amplificationPressureBand']}）。\n\n"
                f"数据能力边界：当前数据源未提供{values['unavailableDimensions']}"
                "结构化字段，这些维度未纳入指数。"
            )

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
