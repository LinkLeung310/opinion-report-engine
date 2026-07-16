from __future__ import annotations

import pytest
from PIL import Image

from report_engine.charts.response import ResponseChartBuilder
from report_engine.charts.theme import ChartTheme
from report_engine.sections.response import ResponseSnapshot
from tests.test_response import fixture_snapshot


def test_chart_uses_required_palette_dpi_and_filename(tmp_path, caplog) -> None:
    output = ResponseChartBuilder().build(fixture_snapshot(), tmp_path)

    assert output.name == "response-window-comparison.png"
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


def test_chart_rejects_snapshot_without_comparison_records(tmp_path) -> None:
    fixture = fixture_snapshot()
    empty = ResponseSnapshot(fixture.window, (), fixture.query_id)

    with pytest.raises(ValueError, match="empty response comparison"):
        ResponseChartBuilder().build(empty, tmp_path)
