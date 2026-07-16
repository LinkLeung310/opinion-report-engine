from __future__ import annotations

from PIL import Image
import pytest

from report_engine.charts.theme import ChartTheme
from report_engine.charts.timeline import TimelineChartBuilder
from tests.test_timeline import empty_timeline, fixture_snapshot


def test_timeline_chart_uses_equal_sentiment_markers_and_required_dpi(
    tmp_path,
    caplog,
) -> None:
    output = TimelineChartBuilder().build(fixture_snapshot(), tmp_path)

    assert output.name == "event-timeline.png"
    assert output.is_file()
    assert "Failed to find font weight" not in caplog.text
    with Image.open(output) as image:
        assert round(image.info["dpi"][0]) == ChartTheme.DPI
        colors = image.convert("RGB").getcolors(maxcolors=image.width * image.height)
    assert colors is not None
    palette = {color for _, color in colors}
    assert (16, 185, 129) in palette
    assert (220, 38, 38) in palette


def test_timeline_chart_rejects_empty_snapshot(tmp_path) -> None:
    with pytest.raises(ValueError, match="empty timeline"):
        TimelineChartBuilder().build(empty_timeline(), tmp_path)
