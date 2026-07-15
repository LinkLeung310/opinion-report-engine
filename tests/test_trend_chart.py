from __future__ import annotations

from datetime import date, timedelta

from PIL import Image

from report_engine.charts.theme import ChartTheme
from report_engine.charts.trend import TrendChartBuilder
from report_engine.sections.trend import DailyTrendPoint, TrendSnapshot


def snapshot(days: int = 7) -> TrendSnapshot:
    points = []
    for index in range(days):
        total = (index % 3) + 1
        points.append(
            DailyTrendPoint(
                date(2026, 3, 1) + timedelta(days=index),
                total,
                1,
                1 if total >= 2 else 0,
                max(0, total - 2),
            )
        )
    return TrendSnapshot(tuple(points), "trend.v1")


def test_trend_chart_uses_required_palette_dpi_and_filename(tmp_path, caplog) -> None:
    output = TrendChartBuilder().build(snapshot(), tmp_path)

    assert output.name == "daily-sentiment-trend.png"
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


def test_long_ranges_limit_labels_without_dropping_final_day() -> None:
    ticks = TrendChartBuilder.tick_positions(100)

    assert len(ticks) <= 10
    assert ticks[0] == 0
    assert ticks[-1] == 99
