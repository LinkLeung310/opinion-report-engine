from __future__ import annotations

from datetime import date

from PIL import Image

from report_engine.charts.metrics import MetricsChartBuilder
from report_engine.charts.theme import ChartTheme
from report_engine.sections.metrics import MetricsSnapshot


def test_metrics_chart_uses_the_required_theme_and_dpi(tmp_path, caplog) -> None:
    snapshot = MetricsSnapshot(
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

    output = MetricsChartBuilder().build(snapshot, tmp_path)

    assert "Failed to find font weight" not in caplog.text
    assert output.name == "sentiment-overview.png"
    assert output.is_file()
    with Image.open(output) as image:
        horizontal_dpi, vertical_dpi = image.info["dpi"]
        assert round(horizontal_dpi) == ChartTheme.DPI
        assert round(vertical_dpi) == ChartTheme.DPI
        colors = image.convert("RGB").getcolors(maxcolors=image.width * image.height)
    assert colors is not None
    palette = {color for _, color in colors}
    assert (220, 38, 38) in palette
    assert (245, 158, 11) in palette
    assert (16, 185, 129) in palette


def test_assignment_color_contract_is_explicit() -> None:
    assert ChartTheme.NEGATIVE == "#DC2626"
    assert ChartTheme.NEUTRAL == "#F59E0B"
    assert ChartTheme.POSITIVE == "#10B981"
