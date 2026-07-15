from __future__ import annotations

from PIL import Image
import pytest

from report_engine.charts.risk import RiskChartBuilder
from report_engine.charts.theme import ChartTheme
from report_engine.sections.risk import RiskSnapshot
from tests.test_risk import empty_snapshot, fixture_snapshot


def low_pressure_snapshot() -> RiskSnapshot:
    return RiskSnapshot(
        article_count=10,
        negative_articles=3,
        high_critical_negative_articles=0,
        platform_count=5,
        negative_platform_count=1,
        calendar_days=10,
        negative_active_days=3,
        total_engagement=100,
        negative_engagement=20,
        query_id="risk.v1",
    )


def image_palette(path) -> set[tuple[int, int, int]]:
    with Image.open(path) as image:
        colors = image.convert("RGB").getcolors(maxcolors=image.width * image.height)
    assert colors is not None
    return {color for _, color in colors}


def test_risk_chart_uses_band_colors_required_dpi_and_filename(
    tmp_path,
    caplog,
) -> None:
    output = RiskChartBuilder().build(fixture_snapshot(), tmp_path / "elevated")
    low_output = RiskChartBuilder().build(low_pressure_snapshot(), tmp_path / "low")

    assert output.name == "risk-signal-index.png"
    assert output.is_file() and low_output.is_file()
    assert "Failed to find font weight" not in caplog.text
    with Image.open(output) as image:
        assert round(image.info["dpi"][0]) == ChartTheme.DPI
    palette = image_palette(output) | image_palette(low_output)
    assert (16, 185, 129) in palette
    assert (245, 158, 11) in palette
    assert (220, 38, 38) in palette


def test_risk_chart_rejects_a_no_data_snapshot(tmp_path) -> None:
    with pytest.raises(ValueError, match="empty risk snapshot"):
        RiskChartBuilder().build(empty_snapshot(), tmp_path)
