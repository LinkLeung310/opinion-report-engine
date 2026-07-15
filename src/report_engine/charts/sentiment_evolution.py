"""Phase-composition chart for the sentiment-evolution section."""

from __future__ import annotations

from pathlib import Path

from matplotlib import rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter

from report_engine.assets import report_font_path
from report_engine.charts.theme import ChartTheme
from report_engine.sections.sentiment_evolution import SentimentEvolutionSnapshot


class SentimentEvolutionChartBuilder:
    filename = "sentiment-evolution.png"

    def build(
        self,
        snapshot: SentimentEvolutionSnapshot,
        output_directory: Path,
    ) -> Path:
        if not snapshot.has_data:
            raise ValueError("cannot chart an empty sentiment-evolution snapshot")

        output_directory.mkdir(parents=True, exist_ok=True)
        phases = snapshot.phases
        last = snapshot.populated_phases[-1]
        font_path = report_font_path()
        fontManager.addfont(font_path)
        font_family = FontProperties(fname=font_path).get_name()
        positions = list(range(len(phases)))
        positive = [float(phase.share("positive")) for phase in phases]
        neutral = [float(phase.share("neutral")) for phase in phases]
        negative = [float(phase.share("negative")) for phase in phases]
        negative_bottom = [
            positive_share + neutral_share
            for positive_share, neutral_share in zip(positive, neutral, strict=True)
        ]

        with rc_context(
            {
                "font.sans-serif": [font_family],
                "axes.unicode_minus": False,
            }
        ):
            figure = Figure(figsize=(6.8, 3.55))
            FigureCanvasAgg(figure)
            axes = figure.subplots()
            ChartTheme.apply(figure, axes)
            axes.bar(positions, positive, color=ChartTheme.POSITIVE, label="正面")
            axes.bar(
                positions,
                neutral,
                bottom=positive,
                color=ChartTheme.NEUTRAL,
                label="中性",
            )
            axes.bar(
                positions,
                negative,
                bottom=negative_bottom,
                color=ChartTheme.NEGATIVE,
                label="负面",
            )
            axes.set_xticks(
                positions,
                [
                    f"{phase.label} {phase.date_range_label}\nn={phase.article_count}"
                    for phase in phases
                ],
            )
            axes.set_ylim(0, 1)
            axes.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
            axes.set_ylabel("情感构成占比", color=ChartTheme.MUTED)
            figure.suptitle(
                f"{last.label}负面占比 {last.share('negative'):.1%}，样本 "
                f"{last.article_count} 篇",
                x=0.08,
                y=0.98,
                ha="left",
                color=ChartTheme.TEXT,
                fontsize=13,
            )
            handles, labels = axes.get_legend_handles_labels()
            figure.legend(
                handles,
                labels,
                frameon=False,
                ncol=3,
                loc="upper right",
                bbox_to_anchor=(0.97, 0.98),
            )
            figure.tight_layout(rect=(0, 0, 1, 0.88))

            output_path = output_directory / self.filename
            figure.savefig(
                output_path,
                dpi=ChartTheme.DPI,
                facecolor=ChartTheme.BACKGROUND,
                bbox_inches="tight",
            )
            figure.clear()

        return output_path
