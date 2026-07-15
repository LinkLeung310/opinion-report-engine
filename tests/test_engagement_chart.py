from __future__ import annotations

from PIL import Image
import pytest

from report_engine.charts.engagement import EngagementChartBuilder
from report_engine.charts.theme import ChartTheme
from report_engine.sections.engagement import EngagementSnapshot
from tests.test_engagement import fixture_snapshot


def test_engagement_chart_uses_required_dpi_palette_and_filename(
    tmp_path,
    caplog,
) -> None:
    output = EngagementChartBuilder().build(fixture_snapshot(), tmp_path)

    assert output.name == "engagement-composition.png"
    assert output.is_file()
    assert "Failed to find font weight" not in caplog.text
    assert "not compatible with tight_layout" not in caplog.text
    with Image.open(output) as image:
        assert round(image.info["dpi"][0]) == ChartTheme.DPI
        colors = image.convert("RGB").getcolors(maxcolors=image.width * image.height)
    assert colors is not None
    palette = {color for _, color in colors}
    assert (37, 99, 235) in palette
    assert (16, 185, 129) in palette
    assert (220, 38, 38) in palette


def test_engagement_chart_rejects_zero_counters(tmp_path) -> None:
    snapshot = EngagementSnapshot(
        article_count=1,
        positive_total_engagement_articles=0,
        zero_engagement_articles=1,
        likes=0,
        comments=0,
        shares=0,
        favorites=0,
        leading_record_count=0,
        records=(),
        query_id="engagement.v1",
    )

    with pytest.raises(ValueError, match="without positive counters"):
        EngagementChartBuilder().build(snapshot, tmp_path)
