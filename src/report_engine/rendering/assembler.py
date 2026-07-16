"""Assemble ordered section results into Markdown and frontend metadata."""

from __future__ import annotations

from datetime import datetime

from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import ReportResult, SectionResult, SectionStatus


class ReportAssembler:
    def assemble(
        self,
        config: ReportConfig,
        report_id: str,
        sections: tuple[SectionResult, ...],
        generated_at: datetime,
    ) -> ReportResult:
        title = f"{config.topic.event_title}舆情分析报告"
        markdown = self._markdown(config, title, sections)
        meta = self._meta(config, report_id, title, sections, generated_at)
        return ReportResult(
            report_id=report_id,
            config=config,
            sections=sections,
            generated_at=generated_at,
            markdown=markdown,
            meta=meta,
        )

    @staticmethod
    def _markdown(
        config: ReportConfig,
        title: str,
        sections: tuple[SectionResult, ...],
    ) -> str:
        date_range = config.date_range
        parts = [
            f"# {title}",
            (
                f"> 监测范围：{date_range.from_date.isoformat()} 至 "
                f"{date_range.to_date.isoformat()}（Asia/Shanghai）"
            ),
        ]
        for section in sections:
            parts.append(section.markdown.strip())
            chart_alt = ReportAssembler._chart_alt(section.section_id, config.language)
            parts.extend(f"![{chart_alt}](charts/{chart})" for chart in section.charts)
        parts.append(
            "_方法说明：报告数字由固定 SQL 与 Python 计算；模型仅基于批准的事实与证据撰写文字。_"
        )
        return "\n\n".join(parts) + "\n"

    @staticmethod
    def _chart_alt(section_id: SectionId, language: Language) -> str:
        if section_id is SectionId.METRICS:
            return "情感分布概览" if language is Language.ZH else "Sentiment overview"
        if section_id is SectionId.TREND:
            return "每日情感趋势" if language is Language.ZH else "Daily sentiment trend"
        if section_id is SectionId.SENTIMENT_EVOLUTION:
            return "阶段情感构成与样本量" if language is Language.ZH else "Phase sentiment composition and sample sizes"
        if section_id is SectionId.KEYWORDS:
            return "重复短语覆盖与情感构成" if language is Language.ZH else "Recurring phrase coverage and sentiment"
        if section_id is SectionId.ENGAGEMENT:
            return "互动构成与高计数内容" if language is Language.ZH else "Engagement composition and high-count records"
        if section_id is SectionId.MEDIA_SOCIAL:
            return "媒体与社交内容的量级及情感构成" if language is Language.ZH else "Media and social volume and sentiment composition"
        if section_id is SectionId.TIMELINE:
            return "带证据编号的事件收录时间线" if language is Language.ZH else "Evidence-linked event timeline"
        if section_id is SectionId.TOP_CONTENT:
            return "代表内容的互动与结构化风险信号" if language is Language.ZH else "Representative content interaction and structured risk signals"
        if section_id is SectionId.NEGATIVE_THEMES:
            return "负面议题覆盖与结构化风险信号" if language is Language.ZH else "Negative issue coverage and structured risk signals"
        if section_id is SectionId.SPREAD_PATH:
            return "平台首次收录与日历参与矩阵" if language is Language.ZH else "Platform first-capture and calendar participation matrix"
        if section_id is SectionId.PLATFORMS:
            return "平台量级、情感与互动对比" if language is Language.ZH else "Platform volume, sentiment, and engagement"
        if section_id is SectionId.SEVERITY:
            return "负面严重程度与分数分布" if language is Language.ZH else "Negative severity and score distribution"
        if section_id is SectionId.RISK:
            return "结构化风险信号指数" if language is Language.ZH else "Structured risk signal index"
        return f"{section_id.value} chart"

    def _meta(
        self,
        config: ReportConfig,
        report_id: str,
        title: str,
        sections: tuple[SectionResult, ...],
        generated_at: datetime,
    ) -> dict:
        status_counts = {
            status: sum(section.status is status for section in sections)
            for status in SectionStatus
        }
        failures = [
            {
                "sectionId": section.section_id.value,
                "stage": section.failure.stage.value,
                "message": section.failure.message,
            }
            for section in sections
            if section.failure is not None
        ]
        return {
            "id": report_id,
            "title": title,
            "reportType": config.report_type.value,
            "language": config.language.value,
            "topic": config.topic.display_name,
            "dateRange": {
                "from": config.date_range.from_date.isoformat(),
                "to": config.date_range.to_date.isoformat(),
            },
            "sections": len(sections),
            "charts": sum(len(section.charts) for section in sections),
            "stats": self._summary_stats(sections),
            "file": f"/reports/{report_id}.pdf",
            "generatedAt": generated_at.isoformat(),
            "generation": {
                "requested": len(sections),
                "complete": status_counts[SectionStatus.COMPLETE],
                "noData": status_counts[SectionStatus.NO_DATA],
                "failed": status_counts[SectionStatus.FAILED],
            },
            "failures": failures,
        }

    @staticmethod
    def _summary_stats(sections: tuple[SectionResult, ...]) -> dict:
        def first_fact(*keys: str):
            for section in sections:
                if section.facts is None:
                    continue
                for key in keys:
                    try:
                        return section.facts.get(key)
                    except KeyError:
                        continue
            return None

        articles = first_fact("articles", "articleCount")
        negative_ratio = first_fact("negativeRatio")
        peak_day = first_fact("peakDay")
        return {
            "articles": articles.raw_value if articles is not None else 0,
            "negativeRatio": (
                negative_ratio.formatted_value
                if negative_ratio is not None
                else "暂无"
            ),
            "peakDay": peak_day.formatted_value if peak_day is not None else "暂无",
        }
