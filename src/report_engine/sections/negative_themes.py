"""Versioned exact-indicator classification of negative-summary themes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import unicodedata

from report_engine.domain.evidence import Evidence, EvidenceSet
from report_engine.domain.facts import Fact, FactSet


MIN_THEME_ARTICLES = 2
MAX_DISPLAY_THEMES = 3
CODEBOOK_SOURCE_ID = "negative-themes.codebook.v1"
CLASSIFICATION_SOURCE_ID = "negative-themes.classification.v1"
RANKING_SOURCE_ID = "negative-themes.ranking.v1"
REPRESENTATIVE_SOURCE_ID = "negative-themes.representative.v1"

CONCERN_MARKERS = (
    "担心",
    "认为",
    "质疑",
    "不满",
    "焦虑",
    "担忧",
    "困难",
    "削弱",
    "不愿",
    "影响",
    "增加",
)
DEMAND_MARKERS = (
    "要求",
    "呼吁",
    "希望",
    "应当",
    "需要",
    "诉求",
    "恢复",
    "公开",
    "说明",
)
SEVERITY_ORDER = {None: 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass(frozen=True)
class ThemeDefinition:
    theme_id: str
    label_zh: str
    label_en: str
    indicators: tuple[str, ...]


THEME_CODEBOOK = (
    ThemeDefinition(
        "user_agency",
        "用户自主权",
        "User agency and control",
        (
            "负反馈入口",
            "表达不喜欢",
            "用户控制感",
            "选择权",
            "纠偏成本",
            "恢复原入口",
            "恢复入口",
        ),
    ),
    ThemeDefinition(
        "transparency",
        "透明度与解释",
        "Transparency and explanation",
        ("推荐透明度", "推荐原因不透明", "说明实验范围", "公开推荐与实验规则"),
    ),
    ThemeDefinition(
        "feedback_effectiveness",
        "反馈有效性",
        "Feedback effectiveness",
        ("不愿听取负面反馈", "反馈是否生效", "反馈机制"),
    ),
)


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


@dataclass(frozen=True)
class NegativeThemeSourceRecord:
    external_id: str
    title: str
    summary: str
    platform: str
    published_at: datetime
    sentiment: str
    severity: str | None
    negative_score: int | None
    likes: int
    comments: int
    shares: int
    favorites: int

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (self.external_id, self.title, self.summary, self.platform)
        ):
            raise ValueError("Negative-theme source fields cannot be blank")
        if self.published_at.utcoffset() is None:
            raise ValueError("Negative-theme publication time must be timezone-aware")
        if self.sentiment != "negative":
            raise ValueError("Negative-theme source records must be negative")
        if self.severity not in SEVERITY_ORDER:
            raise ValueError("Unsupported negative-theme severity")
        if self.negative_score is not None and not 1 <= self.negative_score <= 5:
            raise ValueError("Negative-theme score must be between one and five")
        if min(self.likes, self.comments, self.shares, self.favorites) < 0:
            raise ValueError("Negative-theme interaction counters cannot be negative")

    @property
    def normalized_summary(self) -> str:
        return normalize_text(self.summary)

    @property
    def total_engagement(self) -> int:
        return self.likes + self.comments + self.shares + self.favorites

    @property
    def has_concern(self) -> bool:
        return any(marker in self.normalized_summary for marker in CONCERN_MARKERS)

    @property
    def has_demand(self) -> bool:
        return any(marker in self.normalized_summary for marker in DEMAND_MARKERS)

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
class NegativeTheme:
    definition: ThemeDefinition
    records: tuple[NegativeThemeSourceRecord, ...]
    matched_indicators: tuple[str, ...]

    @property
    def theme_id(self) -> str:
        return self.definition.theme_id

    @property
    def label_zh(self) -> str:
        return self.definition.label_zh

    @property
    def article_count(self) -> int:
        return len(self.records)

    @property
    def source_record_ids(self) -> tuple[str, ...]:
        return tuple(record.external_id for record in self.records)

    @property
    def concern_articles(self) -> int:
        return sum(record.has_concern for record in self.records)

    @property
    def demand_articles(self) -> int:
        return sum(record.has_demand for record in self.records)

    @property
    def high_critical_articles(self) -> int:
        return sum(record.severity in {"high", "critical"} for record in self.records)

    @property
    def total_engagement(self) -> int:
        return sum(record.total_engagement for record in self.records)

    @property
    def platform_count(self) -> int:
        return len({record.platform for record in self.records})

    @property
    def representative(self) -> NegativeThemeSourceRecord:
        return sorted(
            self.records,
            key=lambda record: (
                -SEVERITY_ORDER[record.severity],
                record.negative_score is None,
                -(record.negative_score or 0),
                -record.total_engagement,
                -record.published_at.timestamp(),
                record.external_id,
            ),
        )[0]


@dataclass(frozen=True)
class NegativeThemesSnapshot:
    article_count: int
    negative_article_count: int
    records: tuple[NegativeThemeSourceRecord, ...]
    query_id: str

    def __post_init__(self) -> None:
        if min(self.article_count, self.negative_article_count) < 0:
            raise ValueError("Negative-theme aggregate counts cannot be negative")
        if self.negative_article_count > self.article_count:
            raise ValueError("Negative count cannot exceed scoped articles")
        if self.negative_article_count != len(self.records):
            raise ValueError("Negative count must equal source record count")
        if not self.query_id.strip():
            raise ValueError("Negative-theme query ID cannot be blank")
        record_ids = tuple(record.external_id for record in self.records)
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("Negative-theme source IDs must be unique")
        record_order = tuple(
            (record.published_at, record.external_id) for record in self.records
        )
        if record_order != tuple(sorted(record_order)):
            raise ValueError("Negative-theme records must use chronological query order")

    @property
    def has_negative_articles(self) -> bool:
        return self.negative_article_count > 0

    @property
    def themes(self) -> tuple[NegativeTheme, ...]:
        themes = []
        for definition in THEME_CODEBOOK:
            records = tuple(
                record
                for record in self.records
                if any(
                    indicator in record.normalized_summary
                    for indicator in definition.indicators
                )
            )
            if not records:
                continue
            indicators = tuple(
                indicator
                for indicator in definition.indicators
                if any(indicator in record.normalized_summary for record in records)
            )
            themes.append(NegativeTheme(definition, records, indicators))
        return tuple(themes)

    @property
    def display_themes(self) -> tuple[NegativeTheme, ...]:
        codebook_order = {
            definition.theme_id: index
            for index, definition in enumerate(THEME_CODEBOOK)
        }
        eligible = (
            theme for theme in self.themes if theme.article_count >= MIN_THEME_ARTICLES
        )
        return tuple(
            sorted(
                eligible,
                key=lambda theme: (
                    -theme.article_count,
                    -theme.high_critical_articles,
                    -theme.total_engagement,
                    codebook_order[theme.theme_id],
                ),
            )[:MAX_DISPLAY_THEMES]
        )

    @property
    def has_display_themes(self) -> bool:
        return bool(self.display_themes)

    @property
    def classified_record_ids(self) -> tuple[str, ...]:
        matched = {
            record_id for theme in self.themes for record_id in theme.source_record_ids
        }
        return tuple(
            record.external_id for record in self.records if record.external_id in matched
        )

    @property
    def unclassified_record_ids(self) -> tuple[str, ...]:
        classified = set(self.classified_record_ids)
        return tuple(
            record.external_id
            for record in self.records
            if record.external_id not in classified
        )

    @property
    def total_theme_memberships(self) -> int:
        return sum(theme.article_count for theme in self.themes)

    @property
    def representative_ids(self) -> tuple[str, ...]:
        return tuple(theme.representative.external_id for theme in self.display_themes)

    def to_evidence_set(self) -> EvidenceSet:
        unique: dict[str, Evidence] = {}
        for theme in self.display_themes:
            representative = theme.representative
            unique.setdefault(representative.external_id, representative.to_evidence())
        return EvidenceSet(records=tuple(unique.values()))

    def to_fact_set(self) -> FactSet:
        classified_ids = self.classified_record_ids
        unclassified_ids = self.unclassified_record_ids
        classified_share = (
            Decimal(len(classified_ids)) / Decimal(self.negative_article_count)
            if self.negative_article_count
            else Decimal(0)
        )
        facts = [
            Fact("articles", self.article_count, f"{self.article_count:,}", self.query_id),
            Fact(
                "negativeArticles",
                self.negative_article_count,
                f"{self.negative_article_count:,}",
                self.query_id,
            ),
            Fact(
                "classifiedNegativeArticles",
                len(classified_ids),
                f"{len(classified_ids):,}",
                CLASSIFICATION_SOURCE_ID,
                classified_ids,
            ),
            Fact(
                "classifiedNegativeShare",
                classified_share,
                f"{classified_share:.1%}",
                CLASSIFICATION_SOURCE_ID,
                classified_ids,
            ),
            Fact(
                "unclassifiedNegativeArticles",
                len(unclassified_ids),
                f"{len(unclassified_ids):,}",
                CLASSIFICATION_SOURCE_ID,
                unclassified_ids,
            ),
            Fact(
                "unclassifiedNegativeShare",
                Decimal(1) - classified_share if self.negative_article_count else Decimal(0),
                f"{(Decimal(1) - classified_share if self.negative_article_count else Decimal(0)):.1%}",
                CLASSIFICATION_SOURCE_ID,
                unclassified_ids,
            ),
            Fact(
                "displayThemeCount",
                len(self.display_themes),
                f"{len(self.display_themes):,}",
                RANKING_SOURCE_ID,
            ),
            Fact(
                "totalThemeMemberships",
                self.total_theme_memberships,
                f"{self.total_theme_memberships:,}",
                CLASSIFICATION_SOURCE_ID,
            ),
            Fact(
                "minimumThemeArticles",
                MIN_THEME_ARTICLES,
                str(MIN_THEME_ARTICLES),
                CODEBOOK_SOURCE_ID,
            ),
        ]
        for index, theme in enumerate(self.display_themes, start=1):
            prefix = f"theme{index}"
            source_ids = theme.source_record_ids
            share = Decimal(theme.article_count) / Decimal(self.negative_article_count)
            high_share = Decimal(theme.high_critical_articles) / Decimal(
                theme.article_count
            )
            representative = theme.representative
            values = (
                ("Id", theme.theme_id, theme.theme_id, CODEBOOK_SOURCE_ID),
                ("Label", theme.label_zh, theme.label_zh, CODEBOOK_SOURCE_ID),
                (
                    "Indicators",
                    "、".join(theme.matched_indicators),
                    "、".join(theme.matched_indicators),
                    CODEBOOK_SOURCE_ID,
                ),
                ("Articles", theme.article_count, f"{theme.article_count:,}", CLASSIFICATION_SOURCE_ID),
                ("Share", share, f"{share:.1%}", CLASSIFICATION_SOURCE_ID),
                ("ConcernArticles", theme.concern_articles, f"{theme.concern_articles:,}", CLASSIFICATION_SOURCE_ID),
                ("DemandArticles", theme.demand_articles, f"{theme.demand_articles:,}", CLASSIFICATION_SOURCE_ID),
                ("HighCriticalArticles", theme.high_critical_articles, f"{theme.high_critical_articles:,}", CLASSIFICATION_SOURCE_ID),
                ("HighCriticalShare", high_share, f"{high_share:.1%}", CLASSIFICATION_SOURCE_ID),
                ("TotalEngagement", theme.total_engagement, f"{theme.total_engagement:,}", CLASSIFICATION_SOURCE_ID),
                ("PlatformCount", theme.platform_count, f"{theme.platform_count:,}", CLASSIFICATION_SOURCE_ID),
                ("RepresentativeId", representative.external_id, representative.external_id, REPRESENTATIVE_SOURCE_ID),
            )
            facts.extend(
                Fact(
                    f"{prefix}{suffix}",
                    raw_value,
                    formatted_value,
                    source_id,
                    (representative.external_id,)
                    if suffix == "RepresentativeId"
                    else source_ids,
                )
                for suffix, raw_value, formatted_value, source_id in values
            )
        return FactSet(facts=tuple(facts))
