"""Observable platform participation over time without inferred propagation edges."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from report_engine.domain.evidence import Evidence, EvidenceSet
from report_engine.domain.facts import Fact, FactSet


MAX_DISPLAY_PLATFORMS = 6
SELECTION_SOURCE_ID = "spread-path.platform-selection.v1"
MATRIX_SOURCE_ID = "spread-path.daily-matrix.v1"
ENTRY_SOURCE_ID = "spread-path.first-observation.v1"
SCHEMA_SOURCE_ID = "spread-path.schema-capability.v1"
SENTIMENT_LABELS = {
    "positive": "正面",
    "neutral": "中性",
    "negative": "负面",
}


@dataclass(frozen=True)
class SpreadPathSourceRecord:
    external_id: str
    title: str
    summary: str
    platform: str
    published_at: datetime
    sentiment: str
    likes: int
    comments: int
    shares: int
    favorites: int

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (self.external_id, self.title, self.summary, self.platform)
        ):
            raise ValueError("Spread-path source fields cannot be blank")
        if self.published_at.utcoffset() is None:
            raise ValueError("Spread-path publication time must be timezone-aware")
        if self.sentiment not in SENTIMENT_LABELS:
            raise ValueError("Unsupported spread-path sentiment")
        if min(self.likes, self.comments, self.shares, self.favorites) < 0:
            raise ValueError("Spread-path interaction counters cannot be negative")

    @property
    def total_engagement(self) -> int:
        return self.likes + self.comments + self.shares + self.favorites

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
class PlatformObservation:
    platform: str
    records: tuple[SpreadPathSourceRecord, ...]
    entry_wave: int = 0

    def __post_init__(self) -> None:
        if not self.platform.strip() or not self.records:
            raise ValueError("Platform observation requires a platform and records")
        if any(record.platform != self.platform for record in self.records):
            raise ValueError("Platform observation cannot mix platforms")
        order = tuple((record.published_at, record.external_id) for record in self.records)
        if order != tuple(sorted(order)):
            raise ValueError("Platform records must be chronological")
        if self.entry_wave < 0:
            raise ValueError("Platform entry wave cannot be negative")

    @property
    def first_record(self) -> SpreadPathSourceRecord:
        return self.records[0]

    @property
    def last_record(self) -> SpreadPathSourceRecord:
        return self.records[-1]

    @property
    def first_observed_at(self) -> datetime:
        return self.first_record.published_at

    @property
    def last_observed_at(self) -> datetime:
        return self.last_record.published_at

    @property
    def article_count(self) -> int:
        return len(self.records)

    @property
    def negative_article_count(self) -> int:
        return sum(record.sentiment == "negative" for record in self.records)

    @property
    def total_engagement(self) -> int:
        return sum(record.total_engagement for record in self.records)

    @property
    def source_record_ids(self) -> tuple[str, ...]:
        return tuple(record.external_id for record in self.records)

    def active_days(self, timezone: ZoneInfo) -> int:
        return len(
            {
                record.published_at.astimezone(timezone).date()
                for record in self.records
            }
        )


@dataclass(frozen=True)
class SpreadPathSnapshot:
    from_date: date
    to_date: date
    records: tuple[SpreadPathSourceRecord, ...]
    timezone_name: str
    query_id: str

    def __post_init__(self) -> None:
        if self.from_date > self.to_date:
            raise ValueError("Spread-path calendar cannot be inverted")
        if not self.timezone_name.strip() or not self.query_id.strip():
            raise ValueError("Spread-path timezone and query ID cannot be blank")
        timezone = ZoneInfo(self.timezone_name)
        record_ids = tuple(record.external_id for record in self.records)
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("Spread-path source IDs must be unique")
        order = tuple((record.published_at, record.external_id) for record in self.records)
        if order != tuple(sorted(order)):
            raise ValueError("Spread-path records must use chronological query order")
        for record in self.records:
            local_day = record.published_at.astimezone(timezone).date()
            if not self.from_date <= local_day <= self.to_date:
                raise ValueError("Spread-path record falls outside the report calendar")

    @property
    def has_data(self) -> bool:
        return bool(self.records)

    @property
    def article_count(self) -> int:
        return len(self.records)

    @property
    def calendar_days(self) -> tuple[date, ...]:
        count = (self.to_date - self.from_date).days + 1
        return tuple(self.from_date + timedelta(days=index) for index in range(count))

    @property
    def platform_observations(self) -> tuple[PlatformObservation, ...]:
        grouped: dict[str, list[SpreadPathSourceRecord]] = {}
        for record in self.records:
            grouped.setdefault(record.platform, []).append(record)
        return tuple(
            sorted(
                (
                    PlatformObservation(platform, tuple(records))
                    for platform, records in grouped.items()
                ),
                key=lambda observation: (
                    observation.first_observed_at,
                    observation.platform,
                ),
            )
        )

    @property
    def platform_count(self) -> int:
        return len(self.platform_observations)

    @property
    def display_platforms(self) -> tuple[PlatformObservation, ...]:
        selected = sorted(
            self.platform_observations,
            key=lambda observation: (
                -observation.article_count,
                -observation.total_engagement,
                observation.first_observed_at,
                observation.platform,
            ),
        )[:MAX_DISPLAY_PLATFORMS]
        display_order = sorted(
            selected,
            key=lambda observation: (
                observation.first_observed_at,
                observation.platform,
            ),
        )
        wave_by_time = {
            timestamp: index
            for index, timestamp in enumerate(
                sorted({item.first_observed_at for item in display_order}),
                start=1,
            )
        }
        return tuple(
            PlatformObservation(
                observation.platform,
                observation.records,
                wave_by_time[observation.first_observed_at],
            )
            for observation in display_order
        )

    @property
    def entry_wave_count(self) -> int:
        return len({item.entry_wave for item in self.display_platforms})

    @property
    def daily_platform_counts(self) -> dict[date, dict[str, int]]:
        counts = {day: {} for day in self.calendar_days}
        timezone = ZoneInfo(self.timezone_name)
        for record in self.records:
            day = record.published_at.astimezone(timezone).date()
            counts[day][record.platform] = counts[day].get(record.platform, 0) + 1
        return counts

    @property
    def multi_platform_days(self) -> int:
        return sum(len(counts) > 1 for counts in self.daily_platform_counts.values())

    @property
    def max_daily_platforms(self) -> int:
        return max(
            (len(counts) for counts in self.daily_platform_counts.values()),
            default=0,
        )

    @property
    def max_daily_platform_days(self) -> tuple[date, ...]:
        maximum = self.max_daily_platforms
        if not maximum:
            return ()
        return tuple(
            day
            for day, counts in self.daily_platform_counts.items()
            if len(counts) == maximum
        )

    @property
    def first_observation_interval_hours(self) -> Decimal:
        observations = self.platform_observations
        if len(observations) < 2:
            return Decimal(0)
        seconds = (
            observations[-1].first_observed_at - observations[0].first_observed_at
        ).total_seconds()
        return Decimal(str(seconds)) / Decimal(3600)

    @property
    def earliest_platforms(self) -> tuple[str, ...]:
        observations = self.platform_observations
        if not observations:
            return ()
        first_at = observations[0].first_observed_at
        return tuple(
            item.platform for item in observations if item.first_observed_at == first_at
        )

    @property
    def latest_new_platforms(self) -> tuple[str, ...]:
        observations = self.platform_observations
        if not observations:
            return ()
        last_at = observations[-1].first_observed_at
        return tuple(
            item.platform for item in observations if item.first_observed_at == last_at
        )

    def to_evidence_set(self) -> EvidenceSet:
        return EvidenceSet(
            records=tuple(
                observation.first_record.to_evidence()
                for observation in self.display_platforms
            )
        )

    def to_fact_set(self) -> FactSet:
        timezone = ZoneInfo(self.timezone_name)
        displayed = self.display_platforms
        max_days = self.max_daily_platform_days
        facts = [
            Fact("articles", self.article_count, f"{self.article_count:,}", self.query_id),
            Fact("platformCount", self.platform_count, f"{self.platform_count:,}", MATRIX_SOURCE_ID),
            Fact("displayPlatformCount", len(displayed), f"{len(displayed):,}", SELECTION_SOURCE_ID),
            Fact("omittedPlatformCount", self.platform_count - len(displayed), f"{self.platform_count - len(displayed):,}", SELECTION_SOURCE_ID),
            Fact("calendarDays", len(self.calendar_days), f"{len(self.calendar_days):,}", MATRIX_SOURCE_ID),
            Fact("multiPlatformDays", self.multi_platform_days, f"{self.multi_platform_days:,}", MATRIX_SOURCE_ID),
            Fact("maxDailyPlatforms", self.max_daily_platforms, f"{self.max_daily_platforms:,}", MATRIX_SOURCE_ID),
            Fact(
                "maxDailyPlatformDays",
                ",".join(day.isoformat() for day in max_days),
                "、".join(f"{day.month}/{day.day}" for day in max_days) or "暂无",
                MATRIX_SOURCE_ID,
            ),
            Fact("entryWaveCount", self.entry_wave_count, f"{self.entry_wave_count:,}", ENTRY_SOURCE_ID),
            Fact("firstObservationIntervalHours", self.first_observation_interval_hours, f"{self.first_observation_interval_hours:.1f}", ENTRY_SOURCE_ID),
            Fact("earliestPlatformCount", len(self.earliest_platforms), f"{len(self.earliest_platforms):,}", ENTRY_SOURCE_ID),
            Fact(
                "earliestPlatforms",
                "、".join(self.earliest_platforms),
                "、".join(self.earliest_platforms) or "暂无",
                ENTRY_SOURCE_ID,
            ),
            Fact("latestNewPlatformCount", len(self.latest_new_platforms), f"{len(self.latest_new_platforms):,}", ENTRY_SOURCE_ID),
            Fact(
                "latestNewPlatforms",
                "、".join(self.latest_new_platforms),
                "、".join(self.latest_new_platforms) or "暂无",
                ENTRY_SOURCE_ID,
            ),
            Fact("relationshipEdges", None, "不可用", SCHEMA_SOURCE_ID),
        ]
        for index, observation in enumerate(displayed, start=1):
            prefix = f"platform{index}"
            source_ids = observation.source_record_ids
            first = observation.first_record
            first_at = observation.first_observed_at.astimezone(timezone)
            last_at = observation.last_observed_at.astimezone(timezone)
            values = (
                ("Name", observation.platform, observation.platform, SELECTION_SOURCE_ID, source_ids),
                ("EntryWave", observation.entry_wave, str(observation.entry_wave), ENTRY_SOURCE_ID, (first.external_id,)),
                ("FirstObservedAt", first_at, first_at.strftime("%Y-%m-%d %H:%M"), ENTRY_SOURCE_ID, (first.external_id,)),
                ("LastObservedAt", last_at, last_at.strftime("%Y-%m-%d %H:%M"), MATRIX_SOURCE_ID, source_ids),
                ("Articles", observation.article_count, f"{observation.article_count:,}", MATRIX_SOURCE_ID, source_ids),
                ("NegativeArticles", observation.negative_article_count, f"{observation.negative_article_count:,}", MATRIX_SOURCE_ID, source_ids),
                ("ActiveDays", observation.active_days(timezone), f"{observation.active_days(timezone):,}", MATRIX_SOURCE_ID, source_ids),
                ("TotalEngagement", observation.total_engagement, f"{observation.total_engagement:,}", MATRIX_SOURCE_ID, source_ids),
                ("FirstRecordId", first.external_id, first.external_id, ENTRY_SOURCE_ID, (first.external_id,)),
                ("FirstSentiment", first.sentiment, SENTIMENT_LABELS[first.sentiment], ENTRY_SOURCE_ID, (first.external_id,)),
            )
            facts.extend(
                Fact(f"{prefix}{suffix}", raw, formatted, source, record_ids)
                for suffix, raw, formatted, source, record_ids in values
            )
        return FactSet(facts=tuple(facts))
