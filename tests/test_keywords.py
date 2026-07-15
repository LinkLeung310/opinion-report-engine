from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from report_engine.sections.keywords import KeywordSourceRecord, KeywordsSnapshot


TIMEZONE = ZoneInfo("Asia/Shanghai")


def record(
    external_id: str,
    day: int,
    title: str,
    summary: str,
    sentiment: str = "negative",
) -> KeywordSourceRecord:
    published_at = datetime(2026, 3, day, 12, tzinfo=TIMEZONE)
    return KeywordSourceRecord(
        external_id=external_id,
        title=title,
        summary=summary,
        published_at=published_at,
        published_day=published_at.date(),
        sentiment=sentiment,
    )


def snapshot(records: tuple[KeywordSourceRecord, ...]) -> KeywordsSnapshot:
    return KeywordsSnapshot(records, date(2026, 3, 17), date(2026, 3, 23), "keywords.v1")


def test_repeated_mentions_count_once_and_identical_sources_keep_longest_phrase() -> None:
    result = snapshot(
        (
            record("a", 17, "负反馈入口调整", "负反馈入口反复出现"),
            record("b", 18, "负反馈入口讨论", "用户关注负反馈入口"),
        )
    )

    phrase = next(item for item in result.recurring_phrases if item.text == "负反馈入口")
    assert phrase.document_count == 2
    assert phrase.source_record_ids == ("a", "b")
    assert all(item.text != "负反馈" for item in result.recurring_phrases)


def test_ranking_uses_document_and_title_coverage_not_negative_count() -> None:
    result = snapshot(
        (
            record("a", 17, "入口调整说明", "反馈机制需要说明", "neutral"),
            record("b", 18, "入口调整测试", "反馈机制仍受质疑", "negative"),
            record("c", 19, "其他标题", "反馈机制再次出现", "negative"),
        )
    )

    assert [phrase.text for phrase in result.display_phrases[:2]] == [
        "反馈机制",
        "入口调整",
    ]
    assert result.display_phrases[0].document_count == 3
    assert result.display_phrases[1].document_count == 2


def test_late_emerging_requires_two_late_documents_and_no_early_document() -> None:
    result = snapshot(
        (
            record("a", 17, "早期短语出现", "没有重复信号"),
            record("b", 21, "后期新增议题", "后期新增议题出现"),
            record("c", 22, "后期新增议题", "继续讨论后期新增议题"),
        )
    )

    assert result.late_window_start == date(2026, 3, 21)
    emerging = next(
        phrase for phrase in result.display_phrases if phrase.text == "后期新增议题"
    )
    assert emerging.late_emerging is True


def test_nonempty_articles_without_repeated_phrase_are_analytical_no_data() -> None:
    result = snapshot(
        (
            record("a", 17, "完全不同标题", "第一条独立摘要"),
            record("b", 18, "另一种表达", "第二条没有交集"),
        )
    )

    assert result.has_articles is True
    assert result.has_data is False
    with pytest.raises(ValueError, match="without recurring phrases"):
        result.to_fact_set()


def test_facts_keep_source_ids_unrounded_coverage_and_honest_emergence() -> None:
    result = snapshot(
        (
            record("a", 17, "透明度诉求", "需要更多透明度", "negative"),
            record("b", 18, "透明度讨论", "透明度仍受关注", "neutral"),
            record("c", 19, "其他内容", "没有相同短语", "positive"),
        )
    )

    facts = result.to_fact_set()
    assert facts.get("keyword1Text").raw_value == "透明度"
    assert facts.get("keyword1Text").source_record_ids == ("a", "b")
    assert facts.get("keyword1Coverage").raw_value == Decimal(2) / Decimal(3)
    assert facts.get("keyword1Coverage").formatted_value == "66.7%"
    assert facts.get("keyword1NegativeShare").formatted_value == "50.0%"
    assert facts.get("emergingPhraseCount").raw_value == 0
    assert facts.get("emergingPhrases").formatted_value == "无"
