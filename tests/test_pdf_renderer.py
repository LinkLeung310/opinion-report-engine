from __future__ import annotations

from datetime import date
from io import BytesIO

import pytest
from pypdf import PdfReader

from report_engine.charts.metrics import MetricsChartBuilder
from report_engine.rendering.pdf import ReportLabPdfRenderer
from report_engine.sections.metrics import MetricsSnapshot


def metrics_snapshot() -> MetricsSnapshot:
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
    )


def test_renders_a4_pdf_with_chinese_text_and_chart(tmp_path) -> None:
    chart_directory = tmp_path / "charts"
    MetricsChartBuilder().build(metrics_snapshot(), chart_directory)
    markdown = """# B站猜你不喜欢算法调整事件舆情分析报告

> 监测范围：2026-03-17 至 2026-03-23（Asia/Shanghai）

## 全网数据概览

监测期内共收集 12 篇内容，负面内容占比达到 58.3%。

![metrics chart](charts/sentiment-overview.png)

_方法说明：所有数字由固定 SQL 与 Python 计算。_
"""

    pdf_bytes = ReportLabPdfRenderer().render(markdown, chart_directory)

    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 20_000
    reader = PdfReader(BytesIO(pdf_bytes))
    assert len(reader.pages) == 1
    page = reader.pages[0]
    assert float(page.mediabox.width) == pytest.approx(595.28, abs=0.5)
    assert float(page.mediabox.height) == pytest.approx(841.89, abs=0.5)
    extracted_text = page.extract_text()
    assert "舆情分析报告" in extracted_text
    assert "负面内容占比达到 58.3%" in extracted_text


def test_rejects_chart_paths_outside_the_bundle(tmp_path) -> None:
    markdown = "# Report\n\n![unsafe](../secret.png)\n"

    with pytest.raises(ValueError, match="charts/<filename>"):
        ReportLabPdfRenderer().render(markdown, tmp_path / "charts")
