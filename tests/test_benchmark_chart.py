from PIL import Image

from report_engine.charts.benchmark import BenchmarkChartBuilder
from report_engine.charts.theme import ChartTheme
from tests.test_benchmark import fixture_snapshot


def test_benchmark_chart_uses_required_dpi_palette_and_filename(tmp_path) -> None:
    output = BenchmarkChartBuilder().build(fixture_snapshot(), tmp_path)
    assert output.name == "historical-benchmark-comparison.png" and output.is_file()
    with Image.open(output) as image:
        assert round(image.info["dpi"][0]) == ChartTheme.DPI
        colors = image.convert("RGB").getcolors(maxcolors=image.width * image.height)
    palette = {color for _, color in colors}
    assert {(220, 38, 38), (245, 158, 11), (16, 185, 129)} <= palette
