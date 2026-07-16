from __future__ import annotations

from PIL import Image
import pytest

from report_engine.charts.theme import ChartTheme
from report_engine.charts.top_content import TopContentChartBuilder
from tests.test_top_content import empty_snapshot, fixture_snapshot


def test_top_content_chart_uses_required_dpi_palette_and_filename(
    tmp_path,
    caplog,
) -> None:
    output = TopContentChartBuilder().build(fixture_snapshot(), tmp_path)

    assert output.name == "top-content-signals.png"
    assert output.is_file()
    assert "Failed to find font weight" not in caplog.text
    with Image.open(output) as image:
        assert round(image.info["dpi"][0]) == ChartTheme.DPI
        colors = image.convert("RGB").getcolors(maxcolors=image.width * image.height)
    assert colors is not None
    palette = {color for _, color in colors}
    assert (16, 185, 129) in palette
    assert (220, 38, 38) in palette


def test_top_content_chart_rejects_snapshot_without_selected_records(tmp_path) -> None:
    with pytest.raises(ValueError, match="without selected records"):
        TopContentChartBuilder().build(empty_snapshot(), tmp_path)
