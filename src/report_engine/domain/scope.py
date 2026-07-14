"""A single, immutable interpretation of the report analysis scope."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from report_engine.config import Language, ReportConfig, ReportType


@dataclass(frozen=True)
class AnalysisScope:
    topic_tag: str
    topic_display_name: str
    event_title: str
    from_date: date
    to_date: date
    to_exclusive: date
    language: Language
    report_type: ReportType

    @classmethod
    def from_config(cls, config: ReportConfig) -> AnalysisScope:
        """Include the full configured end date using a half-open interval."""

        return cls(
            topic_tag=config.topic.tag,
            topic_display_name=config.topic.display_name,
            event_title=config.topic.event_title,
            from_date=config.date_range.from_date,
            to_date=config.date_range.to_date,
            to_exclusive=config.date_range.to_date + timedelta(days=1),
            language=config.language,
            report_type=config.report_type,
        )
