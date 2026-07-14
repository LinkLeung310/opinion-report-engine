"""Typed models for the fixed report-config.json input contract."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ContractModel(BaseModel):
    """Strict base model for public input-contract objects."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ReportType(StrEnum):
    CSUITE = "csuite"
    PR = "pr"


class Language(StrEnum):
    ZH = "zh"
    EN = "en"


class SectionId(StrEnum):
    VERDICT = "verdict"
    METRICS = "metrics"
    TREND = "trend"
    VIEWPOINTS = "viewpoints"
    PLATFORMS = "platforms"
    SEVERITY = "severity"
    RISK = "risk"
    SENTIMENT_EVOLUTION = "sentiment-evolution"
    KEYWORDS = "keywords"
    ENGAGEMENT = "engagement"
    MEDIA_SOCIAL = "media-social"
    TIMELINE = "timeline"
    TOP_CONTENT = "top-content"
    NEGATIVE_THEMES = "negative-themes"
    SPREAD_PATH = "spread-path"
    RESPONSE = "response"
    BENCHMARK = "benchmark"
    BIZ_IMPACT = "biz-impact"
    RECOMMENDATIONS = "recommendations"


class TopicConfig(ContractModel):
    tag: str = Field(min_length=1)
    display_name: str = Field(alias="displayName", min_length=1)
    event_title: str = Field(alias="eventTitle", min_length=1)


class DateRange(ContractModel):
    from_date: date = Field(alias="from")
    to_date: date = Field(alias="to")

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        if self.from_date > self.to_date:
            raise ValueError("dateRange.from must be on or before dateRange.to")
        return self


class SectionConfig(ContractModel):
    id: SectionId
    enabled: bool
    input: dict[str, Any] | None = None


class ReportConfig(ContractModel):
    report_type: ReportType = Field(alias="reportType")
    language: Language
    topic: TopicConfig
    date_range: DateRange = Field(alias="dateRange")
    sections: list[SectionConfig]

    @field_validator("report_type", mode="before")
    @classmethod
    def fallback_unknown_report_type(cls, value: object) -> object:
        """Apply the brief's explicit fallback for unknown report-type strings."""

        if isinstance(value, str) and value not in {
            ReportType.CSUITE.value,
            ReportType.PR.value,
        }:
            return ReportType.CSUITE
        return value

    @model_validator(mode="after")
    def validate_sections(self) -> Self:
        section_ids = [section.id for section in self.sections]
        if len(section_ids) != len(set(section_ids)):
            raise ValueError("sections must not contain duplicate IDs")
        if not any(section.enabled for section in self.sections):
            raise ValueError("sections must enable at least one section")
        return self
