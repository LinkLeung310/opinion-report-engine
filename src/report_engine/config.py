"""Typed models for the fixed report-config.json input contract."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ModelWrapValidatorHandler,
    PrivateAttr,
    model_validator,
)


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
    _normalization_warnings: tuple[str, ...] = PrivateAttr(default=())

    report_type: ReportType = Field(alias="reportType")
    language: Language
    topic: TopicConfig
    date_range: DateRange = Field(alias="dateRange")
    sections: list[SectionConfig]

    @model_validator(mode="wrap")
    @classmethod
    def fallback_unknown_report_type(
        cls,
        data: object,
        handler: ModelWrapValidatorHandler[Self],
    ) -> Self:
        """Apply and retain a warning for the brief's report-type fallback."""

        fell_back = False
        if isinstance(data, dict):
            field_name = "reportType" if "reportType" in data else "report_type"
            value = data.get(field_name)
            if isinstance(value, str) and value not in {
                ReportType.CSUITE.value,
                ReportType.PR.value,
            }:
                data = {**data, field_name: ReportType.CSUITE.value}
                fell_back = True

        model = handler(data)
        if fell_back:
            model._normalization_warnings = (
                "Unknown reportType was normalized to csuite",
            )
        return model

    @model_validator(mode="after")
    def validate_sections(self) -> Self:
        section_ids = [section.id for section in self.sections]
        if len(section_ids) != len(set(section_ids)):
            raise ValueError("sections must not contain duplicate IDs")
        if not any(section.enabled for section in self.sections):
            raise ValueError("sections must enable at least one section")
        return self

    @property
    def normalization_warnings(self) -> tuple[str, ...]:
        """Internal diagnostics that do not alter the public JSON contract."""

        return self._normalization_warnings
