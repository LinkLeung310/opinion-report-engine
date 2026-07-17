from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from report_engine.application.planner import ReportPlanner
from report_engine.config import Language, ReportConfig, SectionId
from report_engine.domain.results import FailureStage, SectionStatus
from report_engine.llm.stub import StubNarrator
from report_engine.sections.keywords import KeywordSourceRecord, KeywordsSnapshot
from report_engine.sections.keywords_runner import KeywordsSectionRunner
from report_engine.sections.registry import default_registry
from tests.test_config import sample_config


TIMEZONE = ZoneInfo("Asia/Shanghai")


def snapshot(kind: str = "data") -> KeywordsSnapshot:
    if kind == "empty":
        records = ()
    elif kind == "no_phrases":
        records = (
            source("a", 17, "完全不同标题", "第一条独立摘要", "negative"),
            source("b", 18, "另一种表达", "第二条没有交集", "neutral"),
        )
    else:
        records = (
            source("a", 17, "入口调整讨论", "透明度受到关注", "negative"),
            source("b", 18, "入口调整测试", "透明度需要说明", "neutral"),
            source("c", 19, "入口调整恢复", "其他独立摘要", "positive"),
        )
    return KeywordsSnapshot(
        records,
        date(2026, 3, 17),
        date(2026, 3, 23),
        "keywords.v1",
    )


def source(external_id, day, title, summary, sentiment):
    published_at = datetime(2026, 3, day, 12, tzinfo=TIMEZONE)
    return KeywordSourceRecord(
        external_id,
        title,
        summary,
        published_at,
        published_at.date(),
        sentiment,
    )


class FakeRepository:
    def __init__(self, result):
        self.result = result

    def fetch(self, _scope):
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class FakeChartBuilder:
    def __init__(self, error=None):
        self.error = error
        self.calls = 0

    def build(
        self,
        _snapshot,
        output_directory: Path,
        _language: Language = Language.ZH,
    ):
        self.calls += 1
        if self.error:
            raise self.error
        return output_directory / "keyword-coverage.png"


class BrokenFactsSnapshot:
    has_articles = True
    has_data = True

    def to_fact_set(self):
        raise ArithmeticError("secret")


def scope():
    return ReportPlanner(default_registry()).build(
        ReportConfig.model_validate(sample_config())
    ).scope


def test_success_charts_then_calls_narrator_once_without_evidence() -> None:
    narrator, chart = StubNarrator(), FakeChartBuilder()
    result = KeywordsSectionRunner(
        FakeRepository(snapshot()), chart, narrator
    ).run(scope(), Language.ZH, Path("charts"))

    assert result.status is SectionStatus.COMPLETE
    assert chart.calls == 1 and len(narrator.requests) == 1
    assert narrator.requests[0].evidence.records == ()
    assert result.charts == ("keyword-coverage.png",)
    assert "关键词与话题" in result.markdown
    assert "入口调整" in result.markdown
    assert "不等同于语义主题聚类" in result.markdown


def test_both_no_data_reasons_skip_chart_and_narrator() -> None:
    for kind, expected in (
        ("empty", "暂无相关数据"),
        ("no_phrases", "至少两篇文章"),
    ):
        narrator, chart = StubNarrator(), FakeChartBuilder()
        result = KeywordsSectionRunner(
            FakeRepository(snapshot(kind)), chart, narrator
        ).run(scope(), Language.ZH, Path("charts"))
        assert result.status is SectionStatus.NO_DATA
        assert expected in result.markdown
        assert chart.calls == 0 and narrator.requests == []


def test_query_calculation_chart_and_narrator_failures_are_safe() -> None:
    narrator = StubNarrator()
    query = KeywordsSectionRunner(
        FakeRepository(RuntimeError("secret")), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert query.failure.stage is FailureStage.QUERY and narrator.requests == []

    calculation = KeywordsSectionRunner(
        FakeRepository(BrokenFactsSnapshot()), FakeChartBuilder(), narrator
    ).run(scope(), Language.ZH, Path("charts"))
    assert calculation.failure.stage is FailureStage.CALCULATION

    chart = KeywordsSectionRunner(
        FakeRepository(snapshot()),
        FakeChartBuilder(RuntimeError("secret")),
        narrator,
    ).run(scope(), Language.ZH, Path("charts"))
    assert chart.failure.stage is FailureStage.CHART

    failing = StubNarrator([SectionId.KEYWORDS])
    llm = KeywordsSectionRunner(
        FakeRepository(snapshot()), FakeChartBuilder(), failing
    ).run(scope(), Language.ZH, Path("charts"))
    assert llm.failure.stage is FailureStage.LLM and len(failing.requests) == 1
    assert llm.charts == ("keyword-coverage.png",)
