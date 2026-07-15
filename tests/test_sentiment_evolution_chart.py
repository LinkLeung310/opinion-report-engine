from __future__ import annotations

from datetime import date, timedelta

import pytest
from PIL import Image

from report_engine.charts.sentiment_evolution import (
    SentimentEvolutionChartBuilder,
)
from report_engine.charts.theme import ChartTheme
from report_engine.sections.sentiment_evolution import (
    DailySentimentPoint,
    SentimentEvolutionSnapshot,
)


def snapshot(has_data: bool = True) -> SentimentEvolutionSnapshot:
    counts = (
        ((1, 0, 1), (0, 1, 1), (1, 0, 1), (0, 0, 0), (0, 1, 1), (0, 0, 1), (0, 0, 1))
        if has_data
        else ((0, 0, 0),) * 7
    )
    return SentimentEvolutionSnapshot(
        tuple(
            DailySentimentPoint(
                date(2026, 3, 17) + timedelta(days=index),
                sum(sentiments),
                sentiments[0],
                sentiments[1],
                sentiments[2],
            )
            for index, sentiments in enumerate(counts)
        ),
        "sentiment-evolution.v1",
    )


def test_chart_uses_required_palette_dpi_and_filename(tmp_path, caplog) -> None:
    output = SentimentEvolutionChartBuilder().build(snapshot(), tmp_path)

    assert output.name == "sentiment-evolution.png"
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


def test_chart_rejects_an_all_zero_calendar(tmp_path) -> None:
    with pytest.raises(ValueError, match="empty sentiment-evolution"):
        SentimentEvolutionChartBuilder().build(snapshot(False), tmp_path)
