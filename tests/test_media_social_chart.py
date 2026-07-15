from __future__ import annotations

import pytest
from PIL import Image

from report_engine.charts.media_social import MediaSocialChartBuilder
from report_engine.charts.theme import ChartTheme
from report_engine.sections.media_social import MediaSocialSnapshot
from tests.test_media_social import fixture_snapshot, row


def test_chart_uses_required_palette_dpi_labels_and_filename(tmp_path, caplog) -> None:
    output = MediaSocialChartBuilder().build(fixture_snapshot(), tmp_path)

    assert output.name == "media-social-comparison.png"
    with Image.open(output) as image:
        assert image.info["dpi"][0] == pytest.approx(ChartTheme.DPI, abs=0.1)
        assert image.width > image.height
    assert not [record for record in caplog.records if record.levelname == "WARNING"]


def test_chart_keeps_an_absent_group_visible(tmp_path) -> None:
    snapshot = MediaSocialSnapshot(
        rows=(row("media", 0, 0, 0, 0, 0), row("social", 2, 1, 0, 1, 1)),
        query_id="media-social.v1",
    )

    output = MediaSocialChartBuilder().build(snapshot, tmp_path)
    assert output.is_file() and output.stat().st_size > 0


def test_chart_rejects_an_empty_scope(tmp_path) -> None:
    snapshot = MediaSocialSnapshot(
        rows=(row("media", 0, 0, 0, 0, 0), row("social", 0, 0, 0, 0, 0)),
        query_id="media-social.v1",
    )

    try:
        MediaSocialChartBuilder().build(snapshot, tmp_path)
    except ValueError as error:
        assert "empty media-social" in str(error)
    else:
        raise AssertionError("empty snapshots must not be charted")
