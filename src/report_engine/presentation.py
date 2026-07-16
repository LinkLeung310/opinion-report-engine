"""Shared, deterministic presentation strings for report localization."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from report_engine.config import Language, SectionId
from report_engine.domain.facts import Fact, FactSet


_SECTION_HEADINGS = {
    SectionId.VERDICT: ("核心结论", "Executive verdict"),
    SectionId.METRICS: ("全网数据概览", "Monitoring overview"),
    SectionId.TREND: ("热度趋势", "Volume trend"),
    SectionId.VIEWPOINTS: ("主要观点", "Main viewpoints"),
    SectionId.PLATFORMS: ("平台表现", "Platform performance"),
    SectionId.SEVERITY: ("负面严重程度", "Negative severity"),
    SectionId.RISK: ("风险评估", "Risk assessment"),
    SectionId.SENTIMENT_EVOLUTION: ("情感演变", "Sentiment evolution"),
    SectionId.KEYWORDS: ("关键词与话题", "Keywords and topics"),
    SectionId.ENGAGEMENT: ("互动传播", "Engagement"),
    SectionId.MEDIA_SOCIAL: ("媒体与社媒对比", "Media and social comparison"),
    SectionId.TIMELINE: ("事件时间线", "Event timeline"),
    SectionId.TOP_CONTENT: ("代表性内容", "Representative content"),
    SectionId.NEGATIVE_THEMES: ("负面议题拆解", "Negative issue themes"),
    SectionId.SPREAD_PATH: ("传播路径（可观测顺序）", "Observable platform sequence"),
    SectionId.RESPONSE: ("回应前后对比", "Response comparison"),
    SectionId.BENCHMARK: ("历史事件对标", "Historical benchmark"),
    SectionId.BIZ_IMPACT: ("商业影响", "Business impact"),
    SectionId.RECOMMENDATIONS: ("行动建议", "Recommended actions"),
}

_SENTIMENT_LABELS = {
    "positive": ("正面", "Positive"),
    "neutral": ("中性", "Neutral"),
    "negative": ("负面", "Negative"),
}

_SEVERITY_LABELS = {
    None: ("未分类", "Unclassified"),
    "low": ("低", "Low"),
    "medium": ("中", "Medium"),
    "high": ("高", "High"),
    "critical": ("危急", "Critical"),
}


def select(language: Language, zh: str, en: str) -> str:
    return en if language is Language.EN else zh


def section_heading(section_id: SectionId, language: Language) -> str:
    zh, en = _SECTION_HEADINGS[section_id]
    return select(language, zh, en)


def sentiment_label(sentiment: str, language: Language) -> str:
    zh, en = _SENTIMENT_LABELS[sentiment]
    return select(language, zh, en)


def severity_label(severity: str | None, language: Language) -> str:
    zh, en = _SEVERITY_LABELS[severity]
    return select(language, zh, en)


def unavailable(language: Language) -> str:
    return select(language, "不可用", "Unavailable")


def not_available(language: Language) -> str:
    return select(language, "暂无", "N/A")


def join_display(values: Iterable[str], language: Language) -> str:
    return select(language, "、", ", ").join(values)


def percentage_points(value: Decimal | float, language: Language) -> str:
    return select(
        language,
        f"{float(value) * 100:+.1f} 个百分点",
        f"{float(value) * 100:+.1f} percentage points",
    )


def failed_section_markdown(section_id: SectionId, language: Language) -> str:
    return (
        f"## {section_heading(section_id, language)}\n\n"
        + select(
            language,
            "本章节生成失败，请检查输入或稍后重试。",
            "This section could not be generated. Check its input or try again later.",
        )
    )


_RISK_BANDS_EN = {"低": "Low", "中": "Medium", "高": "High"}
_PHASES_EN = {
    "全期": "Full period",
    "前期": "Early phase",
    "中期": "Middle phase",
    "后期": "Late phase",
}
_DIRECTIONS_EN = {
    "负面占比上升": "Negative share increased",
    "负面占比下降": "Negative share decreased",
    "基本稳定": "Broadly stable",
    "仅单阶段有数据": "Only one phase contains data",
}
_SOURCE_TYPES_EN = {"媒体内容": "Media", "社交内容": "Social"}
_TIMELINE_ROLES_EN = {
    "首次收录": "first observed",
    "回应标签记录": "response-tagged record",
    "峰值日代表": "peak-day representative",
    "最后收录": "last observed",
}
_TOP_CONTENT_CATEGORIES_EN = {
    "双信号代表": "dual-signal representative",
    "仅高互动代表": "engagement-only representative",
    "仅高风险代表": "risk-only representative",
}
_THEME_LABELS_EN = {
    "用户自主权": "User agency and control",
    "透明度与解释": "Transparency and explanation",
    "反馈有效性": "Feedback effectiveness",
}
_RISK_SIGNAL_LABELS_EN = {
    "sentimentPressure": "Negative sentiment",
    "severityPressure": "High/critical severity",
    "spreadPressure": "Platform spread",
    "persistencePressure": "Persistent coverage",
    "amplificationPressure": "Engagement amplification",
}


def _replace_joined(value: str, mapping: dict[str, str]) -> str:
    return ", ".join(mapping.get(part, part) for part in value.split("、"))


def phase_label(label: str, language: Language) -> str:
    return _PHASES_EN.get(label, label) if language is Language.EN else label


def source_type_label(source_type: str, language: Language) -> str:
    labels = {
        "media": ("媒体内容", "Media"),
        "social": ("社交内容", "Social"),
    }
    zh, en = labels[source_type]
    return select(language, zh, en)


def timeline_roles_label(roles: Iterable[str], language: Language) -> str:
    labels = {
        "first_observed": ("首次收录", "first observed"),
        "tagged_response": ("回应标签记录", "response-tagged record"),
        "peak_day_representative": ("峰值日代表", "peak-day representative"),
        "last_observed": ("最后收录", "last observed"),
    }
    return join_display(
        (select(language, *labels[role]) for role in roles),
        language,
    )


def top_content_category_label(category: str, language: Language) -> str:
    labels = {
        "dual_signal": ("双信号代表", "dual-signal representative"),
        "engagement_only": ("仅高互动代表", "engagement-only representative"),
        "risk_only": ("仅高风险代表", "risk-only representative"),
    }
    return select(language, *labels[category])


def risk_signal_label(key: str, label_zh: str, language: Language) -> str:
    return _RISK_SIGNAL_LABELS_EN[key] if language is Language.EN else label_zh


def _english_fact_value(section_id: SectionId, fact: Fact) -> str:
    key = fact.key
    value = fact.formatted_value

    if value == "暂无":
        return "N/A"
    if value in {"不可用", "不可比较"}:
        return "Unavailable"

    if section_id is SectionId.SEVERITY and key == "highestObservedSeverity":
        return {
            "低": "Low",
            "中": "Medium",
            "高": "High",
            "危急": "Critical",
        }.get(value, value)
    if section_id is SectionId.RISK:
        if key.endswith("Band") or key == "riskLevel":
            return _RISK_BANDS_EN.get(value, value)
        if key == "diagnosticKind":
            return "Non-probability diagnostic index"
        if key == "unavailableDimensions":
            return "Executive association, rumor verification"
    if section_id is SectionId.SENTIMENT_EVOLUTION:
        if key.endswith("Label"):
            return _PHASES_EN.get(value, value)
        if key == "negativeShareDelta" and fact.raw_value is not None:
            return percentage_points(fact.raw_value, Language.EN)
        if key == "direction":
            return _DIRECTIONS_EN.get(value, value)
    if section_id is SectionId.KEYWORDS and key.endswith("Emergence"):
        return "Late-emerging" if value == "后期新增" else "Not late-emerging"
    if section_id is SectionId.KEYWORDS and key == "emergingPhrases" and value == "无":
        return "None"
    if section_id is SectionId.ENGAGEMENT and key.endswith("Sentiment"):
        return sentiment_label(str(fact.raw_value), Language.EN)
    if section_id is SectionId.MEDIA_SOCIAL:
        if key == "sourceClassification":
            return "Stored database source_type classification"
        if key in {"mediaLabel", "socialLabel", "volumeLeaders", "negativeShareLeaders"}:
            return _replace_joined(value, _SOURCE_TYPES_EN)
        if key == "socialMinusMediaNegativeShare" and fact.raw_value is not None:
            return percentage_points(fact.raw_value, Language.EN)
    if section_id is SectionId.TIMELINE:
        if key.endswith("Roles"):
            return _replace_joined(value, _TIMELINE_ROLES_EN)
        if key.endswith("Sentiment"):
            return sentiment_label(str(fact.raw_value), Language.EN)
    if section_id is SectionId.TOP_CONTENT:
        if key.endswith("Category"):
            return _TOP_CONTENT_CATEGORIES_EN.get(value, value)
        if key.endswith("Sentiment"):
            return sentiment_label(str(fact.raw_value), Language.EN)
        if key.endswith("Severity"):
            if value == "不适用":
                return "Not applicable"
            raw_severity = fact.raw_value if isinstance(fact.raw_value, str) else None
            return severity_label(raw_severity, Language.EN)
        if key.endswith("Rank") and value == "未排名":
            return "Unranked"
        if key.endswith("NegativeScore") and value == "未提供":
            return "Unavailable"
    if section_id is SectionId.NEGATIVE_THEMES and key.endswith("Label"):
        return _THEME_LABELS_EN.get(value, value)
    if section_id is SectionId.SPREAD_PATH:
        if key.endswith("FirstSentiment"):
            return sentiment_label(str(fact.raw_value), Language.EN)
        if key == "relationshipEdges":
            return "Unavailable"
    if section_id in {SectionId.RESPONSE, SectionId.BENCHMARK}:
        if key.endswith("ShareDelta") and fact.raw_value is not None:
            return percentage_points(fact.raw_value, Language.EN)
    if section_id is SectionId.BIZ_IMPACT:
        replacements = {
            "舆情声誉压力": "Public-opinion reputation pressure",
            "公开讨论应对复杂度": "Public-discussion response complexity",
            "缺少已验证业务结果序列": "No verified business-outcome series",
            "未建立因果关系": "No causal relationship established",
        }
        if key == "dateRange":
            return value.replace(" 至 ", " to ")
        return replacements.get(value, value)
    if section_id is SectionId.PLATFORMS and value == "其他":
        return "Other"
    return value


def localize_fact_set(
    section_id: SectionId,
    facts: FactSet,
    language: Language,
) -> FactSet:
    """Localize display values while preserving raw values and provenance."""

    if language is Language.ZH:
        return facts
    return FactSet(
        facts=tuple(
            Fact(
                key=fact.key,
                raw_value=fact.raw_value,
                formatted_value=_english_fact_value(section_id, fact),
                source_id=fact.source_id,
                source_record_ids=fact.source_record_ids,
            )
            for fact in facts.facts
        )
    )
