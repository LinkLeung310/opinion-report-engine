from __future__ import annotations

from PIL import Image
import pytest

from report_engine.charts.negative_themes import NegativeThemesChartBuilder
from report_engine.charts.theme import ChartTheme
from report_engine.sections.negative_themes import NegativeThemesSnapshot
from tests.test_negative_themes import fixture_snapshot


def test_negative_themes_chart_uses_required_dpi_palette_and_filename(
    tmp_path,
    caplog,
) -> None:
    output = NegativeThemesChartBuilder().build(fixture_snapshot(), tmp_path)

    assert output.name == "negative-theme-coverage.png"
    assert output.is_file()
    assert "Failed to find font weight" not in caplog.text
    with Image.open(output) as image:
        assert round(image.info["dpi"][0]) == ChartTheme.DPI
        colors = image.convert("RGB").getcolors(maxcolors=image.width * image.height)
    assert colors is not None
    palette = {color for _, color in colors}
    assert (220, 38, 38) in palette
    assert (252, 165, 165) in palette


def test_negative_themes_chart_rejects_snapshot_without_display_themes(tmp_path) -> None:
    empty = NegativeThemesSnapshot(0, 0, (), "negative-themes.v1")
    with pytest.raises(ValueError, match="without display themes"):
        NegativeThemesChartBuilder().build(empty, tmp_path)
