"""Deterministic recurring-phrase extraction and auditable keyword facts."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
import re
import unicodedata

from report_engine.domain.facts import Fact, FactSet


MIN_CJK_CHARACTERS = 3
MAX_CJK_CHARACTERS = 6
MIN_ASCII_CHARACTERS = 3
MAX_ASCII_CHARACTERS = 32
MIN_DOCUMENTS = 2
MAX_DISPLAY_PHRASES = 8

PHRASE_SOURCE_ID = "keywords.phrase-extraction.v1"
RANKING_SOURCE_ID = "keywords.ranking.v1"
EMERGENCE_SOURCE_ID = "keywords.emergence.v1"

CJK_RUN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")
ASCII_TOKEN_RE = re.compile(
    rf"(?<![A-Za-z0-9_-])[A-Za-z][A-Za-z0-9_-]"
    rf"{{{MIN_ASCII_CHARACTERS - 1},{MAX_ASCII_CHARACTERS - 1}}}"
    rf"(?![A-Za-z0-9_-])"
)
VALID_SENTIMENTS = frozenset({"positive", "neutral", "negative"})


@dataclass(frozen=True)
class KeywordSourceRecord:
    external_id: str
    title: str
    summary: str
    published_at: datetime
    published_day: date
    sentiment: str

    def __post_init__(self) -> None:
        if not self.external_id.strip():
            raise ValueError("Keyword source ID cannot be blank")
        if not self.title.strip() or not self.summary.strip():
            raise ValueError("Keyword source text cannot be blank")
        if self.sentiment not in VALID_SENTIMENTS:
            raise ValueError("Keyword source sentiment is invalid")


@dataclass(frozen=True)
class KeywordPhrase:
    text: str
    source_record_ids: tuple[str, ...]
    title_record_ids: tuple[str, ...]
    positive_record_ids: tuple[str, ...]
    neutral_record_ids: tuple[str, ...]
    negative_record_ids: tuple[str, ...]
    first_day: date
    last_day: date
    late_emerging: bool

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Keyword phrase cannot be blank")
        if len(self.source_record_ids) < MIN_DOCUMENTS:
            raise ValueError("Keyword phrase must recur across distinct records")
        if len(self.source_record_ids) != len(set(self.source_record_ids)):
            raise ValueError("Keyword phrase source IDs must be unique")
        if not set(self.title_record_ids).issubset(self.source_record_ids):
            raise ValueError("Keyword title records must be supporting records")
        sentiment_ids = (
            self.positive_record_ids
            + self.neutral_record_ids
            + self.negative_record_ids
        )
        if len(sentiment_ids) != len(set(sentiment_ids)):
            raise ValueError("Keyword sentiment record groups must be disjoint")
        if set(sentiment_ids) != set(self.source_record_ids):
            raise ValueError("Keyword sentiment records must cover all sources")
        if self.first_day > self.last_day:
            raise ValueError("Keyword phrase dates must be chronological")

    @property
    def document_count(self) -> int:
        return len(self.source_record_ids)

    @property
    def title_document_count(self) -> int:
        return len(self.title_record_ids)

    @property
    def positive_documents(self) -> int:
        return len(self.positive_record_ids)

    @property
    def neutral_documents(self) -> int:
        return len(self.neutral_record_ids)

    @property
    def negative_documents(self) -> int:
        return len(self.negative_record_ids)

    @property
    def negative_share(self) -> Decimal:
        return Decimal(self.negative_documents) / Decimal(self.document_count)


@dataclass
class _Candidate:
    source_record_ids: set[str]
    title_record_ids: set[str]


@dataclass(frozen=True)
class KeywordsSnapshot:
    records: tuple[KeywordSourceRecord, ...]
    from_date: date
    to_date: date
    query_id: str

    def __post_init__(self) -> None:
        if self.from_date > self.to_date:
            raise ValueError("Keyword date range must be chronological")
        if not self.query_id.strip():
            raise ValueError("Keyword query ID cannot be blank")
        record_ids = tuple(record.external_id for record in self.records)
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("Keyword source IDs must be unique")
        record_order = tuple(
            (record.published_at, record.external_id) for record in self.records
        )
        if record_order != tuple(sorted(record_order)):
            raise ValueError("Keyword source records must use stable chronological order")
        if any(
            record.published_day < self.from_date
            or record.published_day > self.to_date
            for record in self.records
        ):
            raise ValueError("Keyword source day falls outside the selected range")

    @property
    def article_count(self) -> int:
        return len(self.records)

    @property
    def has_articles(self) -> bool:
        return bool(self.records)

    @property
    def late_window_start(self) -> date:
        calendar_days = (self.to_date - self.from_date).days + 1
        early_days = (calendar_days + 1) // 2
        return self.from_date + timedelta(days=early_days)

    @property
    def recurring_phrases(self) -> tuple[KeywordPhrase, ...]:
        candidates: dict[str, _Candidate] = defaultdict(
            lambda: _Candidate(set(), set())
        )
        record_by_id = {record.external_id: record for record in self.records}
        order_by_id = {
            record.external_id: index for index, record in enumerate(self.records)
        }

        for record in self.records:
            title_candidates = self._extract_candidates(record.title)
            summary_candidates = self._extract_candidates(record.summary)
            for text in title_candidates | summary_candidates:
                candidates[text].source_record_ids.add(record.external_id)
                if text in title_candidates:
                    candidates[text].title_record_ids.add(record.external_id)

        recurring = {
            text: candidate
            for text, candidate in candidates.items()
            if len(candidate.source_record_ids) >= MIN_DOCUMENTS
        }
        grouped: dict[tuple[str, ...], list[tuple[str, _Candidate]]] = defaultdict(list)
        for text, candidate in recurring.items():
            source_ids = tuple(
                sorted(candidate.source_record_ids, key=order_by_id.__getitem__)
            )
            grouped[source_ids].append((text, candidate))

        phrases: list[KeywordPhrase] = []
        for source_ids, nested_candidates in grouped.items():
            text, candidate = sorted(
                nested_candidates,
                key=lambda item: (
                    -len(item[0]),
                    -len(item[1].title_record_ids),
                    item[0],
                ),
            )[0]
            source_records = tuple(record_by_id[record_id] for record_id in source_ids)
            title_ids = tuple(
                record_id
                for record_id in source_ids
                if record_id in candidate.title_record_ids
            )
            phrases.append(
                KeywordPhrase(
                    text=text,
                    source_record_ids=source_ids,
                    title_record_ids=title_ids,
                    positive_record_ids=tuple(
                        record.external_id
                        for record in source_records
                        if record.sentiment == "positive"
                    ),
                    neutral_record_ids=tuple(
                        record.external_id
                        for record in source_records
                        if record.sentiment == "neutral"
                    ),
                    negative_record_ids=tuple(
                        record.external_id
                        for record in source_records
                        if record.sentiment == "negative"
                    ),
                    first_day=min(record.published_day for record in source_records),
                    last_day=max(record.published_day for record in source_records),
                    late_emerging=all(
                        record.published_day >= self.late_window_start
                        for record in source_records
                    ),
                )
            )

        return tuple(
            sorted(
                phrases,
                key=lambda phrase: (
                    -phrase.document_count,
                    -phrase.title_document_count,
                    phrase.first_day,
                    phrase.text,
                ),
            )
        )

    @property
    def display_phrases(self) -> tuple[KeywordPhrase, ...]:
        return self.recurring_phrases[:MAX_DISPLAY_PHRASES]

    @property
    def has_data(self) -> bool:
        return bool(self.display_phrases)

    @property
    def leading_phrases(self) -> tuple[KeywordPhrase, ...]:
        if not self.recurring_phrases:
            return ()
        leading_count = self.recurring_phrases[0].document_count
        return tuple(
            phrase
            for phrase in self.recurring_phrases
            if phrase.document_count == leading_count
        )

    @property
    def emerging_phrases(self) -> tuple[KeywordPhrase, ...]:
        return tuple(phrase for phrase in self.display_phrases if phrase.late_emerging)

    @staticmethod
    def _extract_candidates(text: str) -> set[str]:
        normalized = unicodedata.normalize("NFKC", text)
        candidates = {
            match.group(0).lower() for match in ASCII_TOKEN_RE.finditer(normalized)
        }
        for run in CJK_RUN_RE.findall(normalized):
            for size in range(MIN_CJK_CHARACTERS, MAX_CJK_CHARACTERS + 1):
                candidates.update(
                    run[index : index + size]
                    for index in range(len(run) - size + 1)
                )
        return candidates

    @staticmethod
    def _day_label(value: date) -> str:
        return f"{value.month}/{value.day}"

    def to_fact_set(self) -> FactSet:
        if not self.has_data:
            raise ValueError("Cannot create keyword facts without recurring phrases")

        leading = self.leading_phrases
        emerging = self.emerging_phrases
        phrase_source_ids = tuple(
            dict.fromkeys(
                source_id
                for phrase in self.display_phrases
                for source_id in phrase.source_record_ids
            )
        )
        facts = [
            Fact("articles", self.article_count, f"{self.article_count:,}", self.query_id),
            Fact(
                "recurringPhraseCount",
                len(self.recurring_phrases),
                f"{len(self.recurring_phrases):,}",
                PHRASE_SOURCE_ID,
                phrase_source_ids,
            ),
            Fact(
                "displayPhraseCount",
                len(self.display_phrases),
                f"{len(self.display_phrases):,}",
                RANKING_SOURCE_ID,
                phrase_source_ids,
            ),
            Fact(
                "leadingDocumentCount",
                leading[0].document_count,
                f"{leading[0].document_count:,}",
                RANKING_SOURCE_ID,
                tuple(
                    dict.fromkeys(
                        source_id
                        for phrase in leading
                        for source_id in phrase.source_record_ids
                    )
                ),
            ),
            Fact(
                "leadingPhraseCount",
                len(leading),
                f"{len(leading):,}",
                RANKING_SOURCE_ID,
            ),
            Fact(
                "leadingPhrases",
                "、".join(phrase.text for phrase in leading),
                "、".join(phrase.text for phrase in leading),
                RANKING_SOURCE_ID,
            ),
            Fact(
                "emergingPhraseCount",
                len(emerging),
                f"{len(emerging):,}",
                EMERGENCE_SOURCE_ID,
            ),
            Fact(
                "emergingPhrases",
                "、".join(phrase.text for phrase in emerging) or "无",
                "、".join(phrase.text for phrase in emerging) or "无",
                EMERGENCE_SOURCE_ID,
            ),
            Fact(
                "lateWindowStart",
                self.late_window_start,
                self._day_label(self.late_window_start),
                EMERGENCE_SOURCE_ID,
            ),
            Fact(
                "minimumDocuments",
                MIN_DOCUMENTS,
                str(MIN_DOCUMENTS),
                PHRASE_SOURCE_ID,
            ),
        ]

        for index, phrase in enumerate(self.display_phrases, start=1):
            prefix = f"keyword{index}"
            coverage = Decimal(phrase.document_count) / Decimal(self.article_count)
            source_ids = phrase.source_record_ids
            facts.extend(
                (
                    Fact(
                        f"{prefix}Text",
                        phrase.text,
                        phrase.text,
                        PHRASE_SOURCE_ID,
                        source_ids,
                    ),
                    Fact(
                        f"{prefix}Documents",
                        phrase.document_count,
                        f"{phrase.document_count:,}",
                        PHRASE_SOURCE_ID,
                        source_ids,
                    ),
                    Fact(
                        f"{prefix}Coverage",
                        coverage,
                        f"{coverage:.1%}",
                        PHRASE_SOURCE_ID,
                        source_ids,
                    ),
                    Fact(
                        f"{prefix}PositiveDocuments",
                        phrase.positive_documents,
                        f"{phrase.positive_documents:,}",
                        PHRASE_SOURCE_ID,
                        source_ids,
                    ),
                    Fact(
                        f"{prefix}NeutralDocuments",
                        phrase.neutral_documents,
                        f"{phrase.neutral_documents:,}",
                        PHRASE_SOURCE_ID,
                        source_ids,
                    ),
                    Fact(
                        f"{prefix}NegativeDocuments",
                        phrase.negative_documents,
                        f"{phrase.negative_documents:,}",
                        PHRASE_SOURCE_ID,
                        source_ids,
                    ),
                    Fact(
                        f"{prefix}NegativeShare",
                        phrase.negative_share,
                        f"{phrase.negative_share:.1%}",
                        PHRASE_SOURCE_ID,
                        source_ids,
                    ),
                    Fact(
                        f"{prefix}FirstDay",
                        phrase.first_day,
                        self._day_label(phrase.first_day),
                        PHRASE_SOURCE_ID,
                        source_ids,
                    ),
                    Fact(
                        f"{prefix}LastDay",
                        phrase.last_day,
                        self._day_label(phrase.last_day),
                        PHRASE_SOURCE_ID,
                        source_ids,
                    ),
                    Fact(
                        f"{prefix}Emergence",
                        "late-emerging" if phrase.late_emerging else "not-emerging",
                        "后期新增" if phrase.late_emerging else "非后期新增",
                        EMERGENCE_SOURCE_ID,
                        source_ids,
                    ),
                )
            )
        return FactSet(facts=tuple(facts))
