"""Five-signal diagnostic chart for the risk-assessment section."""

from __future__ import annotations

from pathlib import Path

from matplotlib import rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter

from report_engine.assets import report_font_path
from report_engine.charts.theme import ChartTheme
from report_engine.sections.risk import RISK_BAND_LABELS, RiskBand, RiskSnapshot


class RiskChartBuilder:
    filename = "risk-signal-index.png"
    band_colors = {
        RiskBand.LOW: ChartTheme.POSITIVE,
        RiskBand.MEDIUM: ChartTheme.NEUTRAL,
        RiskBand.HIGH: ChartTheme.NEGATIVE,
    }

    def build(self, snapshot: RiskSnapshot, output_directory: Path) -> Path:
        if not snapshot.has_data:
            raise ValueError("cannot chart an empty risk snapshot")

        output_directory.mkdir(parents=True, exist_ok=True)
        facts = snapshot.to_fact_set()
        signals = snapshot.signals
        font_path = report_font_path()
        fontManager.addfont(font_path)
        font_family = FontProperties(fname=font_path).get_name()

        with rc_context(
            {
                "font.sans-serif": [font_family],
                "axes.unicode_minus": False,
            }
        ):
            figure = Figure(figsize=(7.2, 3.35))
            FigureCanvasAgg(figure)
            axes = figure.subplots()
            ChartTheme.apply(figure, axes)

            positions = list(range(len(signals)))
            bars = axes.barh(
                positions,
                [signal.ratio for signal in signals],
                color=[self.band_colors[signal.band] for signal in signals],
                height=0.58,
            )
            axes.set_yticks(positions, [signal.label_zh for signal in signals])
            axes.invert_yaxis()
            axes.set_xlim(0, 1.08)
            axes.xaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
            axes.set_xlabel("信号强度（诊断指数，非概率）", color=ChartTheme.MUTED)
            axes.axvline(
                snapshot.low_threshold,
                color=ChartTheme.NEUTRAL,
                linewidth=1,
                linestyle="--",
                alpha=0.45,
            )
            axes.axvline(
                snapshot.high_threshold,
                color=ChartTheme.NEGATIVE,
                linewidth=1,
                linestyle="--",
                alpha=0.45,
            )
            axes.bar_label(
                bars,
                labels=[
                    f"{RISK_BAND_LABELS[signal.band]} {signal.ratio:.1%}"
                    for signal in signals
                ],
                padding=4,
                color=ChartTheme.TEXT,
                fontsize=9,
            )
            figure.suptitle(
                (
                    f"综合风险信号指数 {facts.get('riskSignalIndex').formatted_value}，"
                    f"{facts.get('highSignalCount').formatted_value}/"
                    f"{facts.get('evaluatedSignalCount').formatted_value} 项高位"
                ),
                x=0.07,
                ha="left",
                color=ChartTheme.TEXT,
                fontsize=13,
            )
            figure.tight_layout(rect=(0, 0, 1, 0.9))

            output_path = output_directory / self.filename
            figure.savefig(
                output_path,
                dpi=ChartTheme.DPI,
                facecolor=ChartTheme.BACKGROUND,
                bbox_inches="tight",
            )
            figure.clear()

        return output_path
