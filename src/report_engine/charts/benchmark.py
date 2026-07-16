"""Equal-window historical benchmark chart."""

from pathlib import Path

from matplotlib import rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties, fontManager

from report_engine.assets import report_font_path
from report_engine.charts.theme import ChartTheme
from report_engine.sections.benchmark import BenchmarkSnapshot


class BenchmarkChartBuilder:
    filename = "historical-benchmark-comparison.png"

    def build(self, snapshot: BenchmarkSnapshot, output_directory: Path) -> Path:
        if not snapshot.has_data:
            raise ValueError("cannot chart an empty benchmark")
        output_directory.mkdir(parents=True, exist_ok=True)
        sides = (snapshot.current, snapshot.comparison)
        labels = ("当前事件", "历史对标")
        font = report_font_path(); fontManager.addfont(font)
        family = FontProperties(fname=font).get_name()
        with rc_context({"font.sans-serif": [family], "axes.unicode_minus": False}):
            figure = Figure(figsize=(6.8, 3.4)); FigureCanvasAgg(figure)
            volume, sentiment = figure.subplots(1, 2)
            ChartTheme.apply(figure, volume); ChartTheme.apply(figure, sentiment)
            positions = (0, 1)
            averages = [float(side.daily_average) for side in sides]
            bars = volume.bar(positions, averages, color=ChartTheme.ACCENT, width=.55)
            volume.set_xticks(positions, labels); volume.set_ylabel("日均收录篇数")
            volume.bar_label(bars, labels=[f"{v:.1f}" for v in averages], padding=3)
            for position, side in zip(positions, sides, strict=True):
                volume.text(position, averages[position] * .48,
                            f"n={side.article_count}\n篇均互动 {side.engagement_per_article:,.1f}",
                            ha="center", color="white", fontsize=8)
            bottoms = [0.0, 0.0]
            for name, color in (("positive", ChartTheme.POSITIVE),
                                ("neutral", ChartTheme.NEUTRAL),
                                ("negative", ChartTheme.NEGATIVE)):
                shares = [float(side.share(name)) for side in sides]
                sentiment.bar(positions, shares, bottom=bottoms, color=color,
                              label={"positive":"正面","neutral":"中性","negative":"负面"}[name])
                bottoms = [a + b for a, b in zip(bottoms, shares, strict=True)]
            sentiment.set_xticks(positions, labels); sentiment.set_ylim(0, 1)
            sentiment.set_ylabel("情感构成")
            for position, side in zip(positions, sides, strict=True):
                sentiment.text(position, 1.03,
                               f"负面 {side.share('negative'):.1%}\n高/危 {side.high_critical_share:.1%}",
                               ha="center", fontsize=8)
            handles, legend_labels = sentiment.get_legend_handles_labels()
            figure.legend(handles, legend_labels, frameon=False, ncol=3,
                          loc="upper right", bbox_to_anchor=(.97, .97))
            figure.suptitle(
                f"等长窗口日均收录 {snapshot.current.daily_average:.1f} vs "
                f"{snapshot.comparison.daily_average:.1f} 篇",
                x=.07, ha="left", color=ChartTheme.TEXT, fontsize=12.5)
            figure.text(.07, .01,
                        f"窗口：{snapshot.current.date_range_label} vs {snapshot.comparison.date_range_label}；"
                        "等长日历不代表采集条件或事件严重性相同。",
                        fontsize=8, color=ChartTheme.MUTED)
            figure.tight_layout(rect=(0, .11, 1, .82))
            target = output_directory / self.filename
            figure.savefig(target, dpi=ChartTheme.DPI, facecolor="white", bbox_inches="tight")
            figure.clear()
        return target
