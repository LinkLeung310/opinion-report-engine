from __future__ import annotations

from datetime import date

from PIL import Image
import pytest

from report_engine.charts.spread_path import SpreadPathChartBuilder
from report_engine.charts.theme import ChartTheme
from report_engine.sections.spread_path import SpreadPathSnapshot
from tests.test_spread_path import fixture_snapshot, record


def test_spread_path_chart_uses_required_dpi_accent_and_first_entry_outline(
    tmp_path,
    caplog,
) -> None:
    output = SpreadPathChartBuilder().build(fixture_snapshot(), tmp_path)

    assert output.name == "platform-time-matrix.png"
    assert output.is_file()
    assert "Failed to find font weight" not in caplog.text
    with Image.open(output) as image:
        assert round(image.info["dpi"][0]) == ChartTheme.DPI
        colors = image.convert("RGB").getcolors(maxcolors=image.width * image.height)
    assert colors is not None
    palette = {color for _, color in colors}
    assert (37, 99, 235) in palette
    assert (220, 38, 38) in palette


def test_spread_path_chart_rejects_single_platform_snapshot(tmp_path) -> None:
    single = SpreadPathSnapshot(
        date(2026, 3, 17),
        date(2026, 3, 23),
        (record("one", "单平台", 0, 9),),
        "Asia/Shanghai",
        "spread-path.v1",
    )
    with pytest.raises(ValueError, match="without multiple platforms"):
        SpreadPathChartBuilder().build(single, tmp_path)
