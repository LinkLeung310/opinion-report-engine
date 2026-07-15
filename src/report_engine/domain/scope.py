"""A single, immutable interpretation of the report analysis scope."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from report_engine.config import Language, ReportConfig, ReportType


@dataclass(frozen=True)
class AnalysisScope:
    topic_tag: str
    topic_display_name: str
    event_title: str
    from_date: date
    to_date: date
    from_inclusive: datetime
    to_exclusive: datetime
    timezone_name: str
    language: Language
    report_type: ReportType

    @classmethod
    def from_config(cls, config: ReportConfig) -> AnalysisScope:
        """Include the full configured end date using a half-open interval."""

        timezone_name = "Asia/Shanghai"
        timezone = ZoneInfo(timezone_name)
        return cls(
            topic_tag=config.topic.tag,
            topic_display_name=config.topic.display_name,
            event_title=config.topic.event_title,
            from_date=config.date_range.from_date,
            to_date=config.date_range.to_date,
            from_inclusive=datetime.combine(
                config.date_range.from_date,
                time.min,
                tzinfo=timezone,
            ),
            to_exclusive=datetime.combine(
                config.date_range.to_date + timedelta(days=1),
                time.min,
                tzinfo=timezone,
            ),
            timezone_name=timezone_name,
            language=config.language,
            report_type=config.report_type,
        )
