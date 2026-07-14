from __future__ import annotations

from datetime import UTC, date, datetime

from report_engine.config import ReportConfig, SectionId
from report_engine.domain.results import (
    FailureStage,
    SectionFailure,
    SectionResult,
    SectionStatus,
)
from report_engine.rendering.assembler import ReportAssembler
from report_engine.sections.metrics import MetricsSnapshot
from tests.test_config import sample_config


def config_with_sections() -> ReportConfig:
    raw = sample_config()
    raw["sections"] = [
        {"id": "metrics", "enabled": True},
        {"id": "trend", "enabled": True},
        {"id": "viewpoints", "enabled": True},
    ]
    return ReportConfig.model_validate(raw)


def metrics_facts():
    return MetricsSnapshot(
        article_count=12,
        positive_articles=2,
        neutral_articles=3,
        negative_articles=7,
        platform_count=4,
        likes=15_460,
        comments=4_705,
        shares=4_620,
        favorites=1_385,
        peak_day=date(2026, 3, 20),
        peak_article_count=3,
        query_id="metrics.v1",
    ).to_fact_set()


def section_results() -> tuple[SectionResult, ...]:
    return (
        SectionResult(
            section_id=SectionId.METRICS,
            status=SectionStatus.COMPLETE,
            markdown="## 全网数据概览\n\n共监测 12 篇。",
            facts=metrics_facts(),
            charts=("sentiment-overview.png",),
        ),
        SectionResult(
            section_id=SectionId.TREND,
            status=SectionStatus.NO_DATA,
            markdown="## 热度趋势\n\n监测范围内暂无相关数据。",
        ),
        SectionResult(
            section_id=SectionId.VIEWPOINTS,
            status=SectionStatus.FAILED,
            markdown="## 主要观点\n\n本章节生成失败，请稍后重试。",
            failure=SectionFailure(
                stage=FailureStage.LLM,
                message="Viewpoint narration failed",
            ),
        ),
    )


def test_markdown_preserves_section_order_and_chart_references() -> None:
    result = ReportAssembler().assemble(
        config_with_sections(),
        "layoff-2026-03-23-v1",
        section_results(),
        datetime(2026, 7, 15, 2, 0, tzinfo=UTC),
    )

    assert result.markdown.index("全网数据概览") < result.markdown.index("热度趋势")
    assert result.markdown.index("热度趋势") < result.markdown.index("主要观点")
    assert "charts/sentiment-overview.png" in result.markdown
    assert "Asia/Shanghai" in result.markdown


def test_meta_counts_visible_sections_charts_and_partial_success() -> None:
    result = ReportAssembler().assemble(
        config_with_sections(),
        "layoff-2026-03-23-v1",
        section_results(),
        datetime(2026, 7, 15, 10, 0).astimezone(),
    )

    assert result.meta["sections"] == 3
    assert result.meta["charts"] == 1
    assert result.meta["generation"] == {
        "requested": 3,
        "complete": 1,
        "noData": 1,
        "failed": 1,
    }
    assert result.meta["failures"] == [
        {
            "sectionId": "viewpoints",
            "stage": "llm",
            "message": "Viewpoint narration failed",
        }
    ]


def test_meta_summary_uses_the_same_metrics_fact_set() -> None:
    result = ReportAssembler().assemble(
        config_with_sections(),
        "layoff-2026-03-23-v1",
        section_results(),
        datetime(2026, 7, 15, 2, 0, tzinfo=UTC),
    )

    assert result.meta["stats"] == {
        "articles": 12,
        "negativeRatio": "58.3%",
        "peakDay": "3/20",
    }
    assert result.meta["file"] == "/reports/layoff-2026-03-23-v1.pdf"
