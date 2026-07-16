"""Deterministic, evidence-linked event timeline facts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from report_engine.domain.evidence import Evidence, EvidenceSet
from report_engine.domain.facts import Fact, FactSet


TIMELINE_ROLES = (
    "first_observed",
    "tagged_response",
    "peak_day_representative",
    "last_observed",
)
ROLE_LABELS = {
    "first_observed": "首次收录",
    "tagged_response": "回应标签记录",
    "peak_day_representative": "峰值日代表",
    "last_observed": "最后收录",
}
SENTIMENT_LABELS = {
    "positive": "正面",
    "neutral": "中性",
    "negative": "负面",
}


@dataclass(frozen=True)
class TimelineRoleRecord:
    role: str
    external_id: str
    title: str
    summary: str
    platform: str
    published_at: datetime
    published_day: date
    sentiment: str
    total_engagement: int
    response_tagged: bool

    def __post_init__(self) -> None:
        if self.role not in TIMELINE_ROLES:
            raise ValueError("Unsupported timeline role")
        if any(
            not value.strip()
            for value in (self.external_id, self.title, self.summary, self.platform)
        ):
            raise ValueError("Timeline source text fields cannot be blank")
        if self.published_at.utcoffset() is None:
            raise ValueError("Timeline publication time must be timezone-aware")
        if self.sentiment not in SENTIMENT_LABELS:
            raise ValueError("Unsupported timeline sentiment")
        if self.total_engagement < 0:
            raise ValueError("Timeline engagement cannot be negative")
        if self.role == "tagged_response" and not self.response_tagged:
            raise ValueError("Tagged-response role requires the exact response tag")


@dataclass(frozen=True)
class TimelineMilestone:
    external_id: str
    title: str
    summary: str
    platform: str
    published_at: datetime
    published_day: date
    sentiment: str
    total_engagement: int
    response_tagged: bool
    roles: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.roles:
            raise ValueError("Timeline milestone requires at least one role")
        if len(self.roles) != len(set(self.roles)):
            raise ValueError("Timeline milestone roles must be unique")
        expected_roles = tuple(
            role for role in TIMELINE_ROLES if role in self.roles
        )
        if self.roles != expected_roles:
            raise ValueError("Timeline milestone roles must use fixed priority")

    @property
    def role_labels(self) -> tuple[str, ...]:
        return tuple(ROLE_LABELS[role] for role in self.roles)

    @property
    def role_display(self) -> str:
        return "、".join(self.role_labels)

    def to_evidence(self) -> Evidence:
        return Evidence(
            record_id=self.external_id,
            title=self.title,
            summary=self.summary,
            platform=self.platform,
            published_at=self.published_at,
            sentiment=self.sentiment,
        )


@dataclass(frozen=True)
class TimelineSnapshot:
    article_count: int
    peak_day: date | None
    peak_articles: int
    response_tagged_articles: int
    role_records: tuple[TimelineRoleRecord, ...]
    timezone_name: str
    query_id: str

    def __post_init__(self) -> None:
        if min(
            self.article_count,
            self.peak_articles,
            self.response_tagged_articles,
        ) < 0:
            raise ValueError("Timeline counts cannot be negative")
        if self.response_tagged_articles > self.article_count:
            raise ValueError("Response-tagged count cannot exceed articles")
        if not self.timezone_name.strip() or not self.query_id.strip():
            raise ValueError("Timeline timezone and query ID cannot be blank")
        timezone = ZoneInfo(self.timezone_name)
        for record in self.role_records:
            if record.published_at.astimezone(timezone).date() != record.published_day:
                raise ValueError("Timeline local day does not match report timezone")

        if not self.article_count:
            if self.peak_day is not None or self.peak_articles or self.role_records:
                raise ValueError("Empty timeline cannot have peak data or roles")
            if self.response_tagged_articles:
                raise ValueError("Empty timeline cannot have response-tagged records")
            return

        if self.peak_day is None or not 1 <= self.peak_articles <= self.article_count:
            raise ValueError("Non-empty timeline requires a valid peak")
        roles = tuple(record.role for record in self.role_records)
        if len(roles) != len(set(roles)):
            raise ValueError("Timeline query roles must be unique")
        expected_roles = tuple(
            role
            for role in TIMELINE_ROLES
            if role != "tagged_response" or self.response_tagged_articles > 0
        )
        if roles != expected_roles:
            raise ValueError("Timeline query roles must use the complete fixed order")
        if len(self.milestones) > min(4, self.article_count):
            raise ValueError("Timeline milestone count exceeds its limit")

    @property
    def has_data(self) -> bool:
        return self.article_count > 0

    @property
    def milestones(self) -> tuple[TimelineMilestone, ...]:
        grouped: dict[str, list[TimelineRoleRecord]] = {}
        for record in self.role_records:
            grouped.setdefault(record.external_id, []).append(record)

        milestones = []
        for records in grouped.values():
            first = records[0]
            payload = (
                first.title,
                first.summary,
                first.platform,
                first.published_at,
                first.published_day,
                first.sentiment,
                first.total_engagement,
                first.response_tagged,
            )
            if any(
                (
                    record.title,
                    record.summary,
                    record.platform,
                    record.published_at,
                    record.published_day,
                    record.sentiment,
                    record.total_engagement,
                    record.response_tagged,
                )
                != payload
                for record in records[1:]
            ):
                raise ValueError("Duplicate timeline IDs must preserve source fields")
            roles = tuple(
                role
                for role in TIMELINE_ROLES
                if any(record.role == role for record in records)
            )
            milestones.append(
                TimelineMilestone(
                    external_id=first.external_id,
                    title=first.title,
                    summary=first.summary,
                    platform=first.platform,
                    published_at=first.published_at,
                    published_day=first.published_day,
                    sentiment=first.sentiment,
                    total_engagement=first.total_engagement,
                    response_tagged=first.response_tagged,
                    roles=roles,
                )
            )
        return tuple(
            sorted(
                milestones,
                key=lambda milestone: (
                    milestone.published_at,
                    milestone.external_id,
                ),
            )
        )

    @property
    def observed_calendar_days(self) -> int:
        if not self.has_data:
            return 0
        return (
            self.milestones[-1].published_day
            - self.milestones[0].published_day
        ).days + 1

    def to_evidence_set(self) -> EvidenceSet:
        return EvidenceSet(
            records=tuple(milestone.to_evidence() for milestone in self.milestones)
        )

    def to_fact_set(self) -> FactSet:
        if not self.has_data:
            raise ValueError("Cannot create timeline facts for an empty snapshot")

        milestones = self.milestones
        milestone_ids = tuple(milestone.external_id for milestone in milestones)
        timezone = ZoneInfo(self.timezone_name)
        first_at = milestones[0].published_at.astimezone(timezone)
        last_at = milestones[-1].published_at.astimezone(timezone)
        facts = [
            Fact("articles", self.article_count, f"{self.article_count:,}", self.query_id),
            Fact(
                "milestoneCount",
                len(milestones),
                f"{len(milestones):,}",
                "timeline.evidence-selection.v1",
                source_record_ids=milestone_ids,
            ),
            Fact(
                "peakDay",
                self.peak_day,
                f"{self.peak_day.month}/{self.peak_day.day}",
                self.query_id,
            ),
            Fact(
                "peakArticles",
                self.peak_articles,
                f"{self.peak_articles:,}",
                self.query_id,
            ),
            Fact(
                "responseTaggedArticles",
                self.response_tagged_articles,
                f"{self.response_tagged_articles:,}",
                self.query_id,
            ),
            Fact(
                "observedCalendarDays",
                self.observed_calendar_days,
                f"{self.observed_calendar_days:,}",
                "timeline.observed-span.v1",
                source_record_ids=(milestones[0].external_id, milestones[-1].external_id),
            ),
            Fact(
                "firstObservedAt",
                first_at,
                first_at.strftime("%Y-%m-%d %H:%M"),
                self.query_id,
                source_record_ids=(milestones[0].external_id,),
            ),
            Fact(
                "lastObservedAt",
                last_at,
                last_at.strftime("%Y-%m-%d %H:%M"),
                self.query_id,
                source_record_ids=(milestones[-1].external_id,),
            ),
        ]
        for index, milestone in enumerate(milestones, start=1):
            prefix = f"milestone{index}"
            source_ids = (milestone.external_id,)
            local_time = milestone.published_at.astimezone(timezone)
            values = (
                ("Id", milestone.external_id, milestone.external_id),
                ("Roles", milestone.role_display, milestone.role_display),
                ("PublishedAt", local_time, local_time.strftime("%Y-%m-%d %H:%M")),
                ("Platform", milestone.platform, milestone.platform),
                (
                    "Sentiment",
                    milestone.sentiment,
                    SENTIMENT_LABELS[milestone.sentiment],
                ),
            )
            facts.extend(
                Fact(
                    f"{prefix}{suffix}",
                    raw_value,
                    formatted_value,
                    self.query_id,
                    source_record_ids=source_ids,
                )
                for suffix, raw_value, formatted_value in values
            )
            if "peak_day_representative" in milestone.roles:
                facts.append(
                    Fact(
                        f"{prefix}PeakEngagement",
                        milestone.total_engagement,
                        f"{milestone.total_engagement:,}",
                        self.query_id,
                        source_record_ids=source_ids,
                    )
                )
        return FactSet(facts=tuple(facts))
