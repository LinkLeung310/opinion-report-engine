"""Shared, deterministic presentation strings for report localization."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from report_engine.config import Language, SectionId


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
