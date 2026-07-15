from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from PIL import Image

from report_engine.charts.keywords import KeywordsChartBuilder
from report_engine.charts.theme import ChartTheme
from report_engine.sections.keywords import KeywordSourceRecord, KeywordsSnapshot


TIMEZONE = ZoneInfo("Asia/Shanghai")


def snapshot(has_data: bool = True) -> KeywordsSnapshot:
    if not has_data:
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


def test_chart_uses_required_palette_dpi_and_filename(tmp_path, caplog) -> None:
    output = KeywordsChartBuilder().build(snapshot(), tmp_path)

    assert output.name == "keyword-coverage.png"
    assert output.is_file()
    assert "Failed to find font weight" not in caplog.text
    with Image.open(output) as image:
        assert round(image.info["dpi"][0]) == ChartTheme.DPI
        colors = image.convert("RGB").getcolors(maxcolors=image.width * image.height)
    assert colors is not None
    palette = {color for _, color in colors}
    assert (220, 38, 38) in palette
    assert (245, 158, 11) in palette
    assert (16, 185, 129) in palette


def test_chart_rejects_articles_without_recurring_phrases(tmp_path) -> None:
    with pytest.raises(ValueError, match="without recurring phrases"):
        KeywordsChartBuilder().build(snapshot(False), tmp_path)
