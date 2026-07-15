from __future__ import annotations

from PIL import Image

from report_engine.charts.platforms import PlatformsChartBuilder
from report_engine.charts.theme import ChartTheme
from tests.test_platforms import fixture_snapshot


def test_platforms_chart_uses_required_palette_dpi_and_filename(tmp_path, caplog) -> None:
    output = PlatformsChartBuilder().build(fixture_snapshot(), tmp_path)

    assert output.name == "platform-performance.png"
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
    assert (37, 99, 235) in palette


def test_platforms_chart_never_receives_more_than_eight_display_rows() -> None:
    assert len(fixture_snapshot().display_rows) <= 8
