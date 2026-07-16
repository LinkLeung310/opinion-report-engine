"""Equal-weight, evidence-linked event milestone chart."""

from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

from matplotlib import rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.dates import DateFormatter, date2num
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.patches import Patch

from report_engine.assets import report_font_path
from report_engine.charts.theme import ChartTheme
from report_engine.sections.timeline import TimelineSnapshot


class TimelineChartBuilder:
    filename = "event-timeline.png"
    sentiment_colors = {
        "positive": ChartTheme.POSITIVE,
        "neutral": ChartTheme.NEUTRAL,
        "negative": ChartTheme.NEGATIVE,
    }

    def build(self, snapshot: TimelineSnapshot, output_directory: Path) -> Path:
        if not snapshot.has_data:
            raise ValueError("cannot chart an empty timeline")

        output_directory.mkdir(parents=True, exist_ok=True)
        milestones = snapshot.milestones
        timezone = ZoneInfo(snapshot.timezone_name)
        local_times = [
            milestone.published_at.astimezone(timezone) for milestone in milestones
        ]
        x_values = [date2num(value) for value in local_times]
        colors = [
            self.sentiment_colors[milestone.sentiment] for milestone in milestones
        ]
        font_path = report_font_path()
        fontManager.addfont(font_path)
        font_family = FontProperties(fname=font_path).get_name()

        with rc_context(
            {
                "font.sans-serif": [font_family],
                "axes.unicode_minus": False,
            }
        ):
            figure = Figure(figsize=(7.2, 3.6))
            FigureCanvasAgg(figure)
            axes = figure.subplots()
            ChartTheme.apply(figure, axes)
            axes.spines["left"].set_visible(False)
            axes.axhline(0, color="#CBD5E1", linewidth=2, zorder=1)
            axes.scatter(
                x_values,
                [0] * len(milestones),
                s=115,
                color=colors,
                edgecolor=ChartTheme.BACKGROUND,
                linewidth=1.5,
                zorder=3,
            )

            offsets = (38, -52, 38, -52)
            for index, (milestone, local_time, x_value) in enumerate(
                zip(milestones, local_times, x_values, strict=True)
            ):
                label = (
                    f"{local_time:%m/%d %H:%M}\n"
                    f"{milestone.role_display} · {milestone.external_id}"
                )
                axes.annotate(
                    label,
                    xy=(x_value, 0),
                    xytext=(0, offsets[index]),
                    textcoords="offset points",
                    ha="center",
                    va="bottom" if offsets[index] > 0 else "top",
                    fontsize=8.2,
                    color=ChartTheme.TEXT,
                    arrowprops={
                        "arrowstyle": "-",
                        "color": "#CBD5E1",
                        "linewidth": 0.8,
                    },
                )

            if len(x_values) == 1:
                axes.set_xlim(x_values[0] - 0.5, x_values[0] + 0.5)
            else:
                span = max(x_values) - min(x_values)
                padding = max(0.35, span * 0.08)
                axes.set_xlim(min(x_values) - padding, max(x_values) + padding)
            axes.set_ylim(-1, 1)
            axes.set_yticks([])
            axes.xaxis.set_major_formatter(DateFormatter("%m/%d", tz=timezone))
            axes.set_xlabel("收录时间（Asia/Shanghai）", color=ChartTheme.MUTED)
            axes.set_title(
                f"首末收录跨 {snapshot.observed_calendar_days} 个自然日，"
                f"共 {len(milestones)} 个里程碑",
                loc="left",
                color=ChartTheme.TEXT,
                fontsize=13,
            )
            axes.legend(
                handles=(
                    Patch(facecolor=ChartTheme.POSITIVE, label="正面"),
                    Patch(facecolor=ChartTheme.NEUTRAL, label="中性"),
                    Patch(facecolor=ChartTheme.NEGATIVE, label="负面"),
                ),
                frameon=False,
                ncol=3,
                loc="upper right",
            )
            figure.subplots_adjust(left=0.08, right=0.96, bottom=0.2, top=0.78)

            output_path = output_directory / self.filename
            figure.savefig(
                output_path,
                dpi=ChartTheme.DPI,
                facecolor=ChartTheme.BACKGROUND,
                bbox_inches="tight",
            )
            figure.clear()

        return output_path
