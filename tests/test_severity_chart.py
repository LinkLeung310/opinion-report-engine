from __future__ import annotations

from PIL import Image
import pytest

from report_engine.charts.severity import SeverityChartBuilder
from report_engine.charts.theme import ChartTheme
from tests.test_severity import fixture_snapshot


def test_severity_chart_uses_risk_ramp_required_dpi_and_filename(
    tmp_path,
    caplog,
) -> None:
    output = SeverityChartBuilder().build(fixture_snapshot(), tmp_path)

    assert output.name == "severity-distribution.png"
    assert output.is_file()
    assert "Failed to find font weight" not in caplog.text
    with Image.open(output) as image:
        assert round(image.info["dpi"][0]) == ChartTheme.DPI
        colors = image.convert("RGB").getcolors(maxcolors=image.width * image.height)
    assert colors is not None
    palette = {color for _, color in colors}
    assert (16, 185, 129) in palette
    assert (245, 158, 11) in palette
    assert (249, 115, 22) in palette
    assert (220, 38, 38) in palette


def test_severity_chart_rejects_a_no_data_snapshot(tmp_path) -> None:
    from tests.test_severity import empty_snapshot

    with pytest.raises(ValueError, match="empty severity snapshot"):
        SeverityChartBuilder().build(empty_snapshot(), tmp_path)
