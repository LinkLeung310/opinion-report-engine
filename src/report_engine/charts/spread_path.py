"""Annotated date-by-platform count matrix for observable migration."""

from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

from matplotlib import rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.patches import Patch, Rectangle

from report_engine.assets import report_font_path
from report_engine.charts.theme import ChartTheme
from report_engine.config import Language
from report_engine.presentation import select
from report_engine.sections.spread_path import SpreadPathSnapshot


class SpreadPathChartBuilder:
    filename = "platform-time-matrix.png"

    @staticmethod
    def _label_indices(length: int, maximum: int = 14) -> list[int]:
        if length <= maximum:
            return list(range(length))
        return sorted(
            {
                round(index * (length - 1) / (maximum - 1))
                for index in range(maximum)
            }
        )

    def build(
        self,
        snapshot: SpreadPathSnapshot,
        output_directory: Path,
        language: Language = Language.ZH,
    ) -> Path:
        if snapshot.platform_count < 2:
            raise ValueError("cannot chart spread path without multiple platforms")

        output_directory.mkdir(parents=True, exist_ok=True)
        platforms = snapshot.display_platforms
        days = snapshot.calendar_days
        counts = snapshot.daily_platform_counts
        matrix = [
            [counts[day].get(observation.platform, 0) for day in days]
            for observation in platforms
        ]
        maximum = max(max(row) for row in matrix) or 1

        font_path = report_font_path()
        fontManager.addfont(font_path)
        font_family = FontProperties(fname=font_path).get_name()
        with rc_context(
            {
                "font.sans-serif": [font_family],
                "axes.unicode_minus": False,
            }
        ):
            width = max(7.2, min(10.5, len(days) * 0.42 + 3.0))
            height = max(2.65, len(platforms) * 0.35 + 1.15)
            figure = Figure(figsize=(width, height))
            FigureCanvasAgg(figure)
            axes = figure.subplots()
            ChartTheme.apply(figure, axes)
            color_map = LinearSegmentedColormap.from_list(
                "spread_path_volume",
                ("#EFF6FF", ChartTheme.ACCENT),
            )
            axes.imshow(
                matrix,
                aspect="auto",
                interpolation="none",
                cmap=color_map,
                vmin=0,
                vmax=maximum,
            )

            label_indices = self._label_indices(len(days))
            axes.set_xticks(
                label_indices,
                [f"{days[index].month}/{days[index].day}" for index in label_indices],
                rotation=35,
                ha="right",
            )
            axes.set_yticks(
                range(len(platforms)),
                [observation.platform for observation in platforms],
            )
            axes.set_ylabel(
                select(language, "首次收录顺序", "First-observed order"),
                color=ChartTheme.MUTED,
            )
            axes.set_xticks(
                [index - 0.5 for index in range(1, len(days))],
                minor=True,
            )
            axes.set_yticks(
                [index - 0.5 for index in range(1, len(platforms))],
                minor=True,
            )
            axes.grid(which="minor", color=ChartTheme.BACKGROUND, linewidth=1.3)
            axes.tick_params(which="minor", bottom=False, left=False)

            timezone = ZoneInfo(snapshot.timezone_name)
            day_index = {day: index for index, day in enumerate(days)}
            for row_index, observation in enumerate(platforms):
                for column_index, count in enumerate(matrix[row_index]):
                    axes.text(
                        column_index,
                        row_index,
                        str(count),
                        ha="center",
                        va="center",
                        color=(
                            ChartTheme.BACKGROUND
                            if count > maximum * 0.55
                            else ChartTheme.TEXT
                        ),
                        fontsize=8.5,
                    )
                first_day = observation.first_observed_at.astimezone(timezone).date()
                column_index = day_index[first_day]
                axes.add_patch(
                    Rectangle(
                        (column_index - 0.47, row_index - 0.42),
                        0.94,
                        0.84,
                        fill=False,
                        edgecolor=ChartTheme.NEGATIVE,
                        linewidth=2,
                    )
                )
                axes.text(
                    column_index - 0.38,
                    row_index - 0.27,
                    f"{observation.entry_wave}",
                    ha="left",
                    va="top",
                    color=ChartTheme.NEGATIVE,
                    fontsize=7.2,
                )

            figure.suptitle(
                select(
                    language,
                    f"{snapshot.platform_count} 个平台的首次收录间隔 "
                    f"{snapshot.first_observation_interval_hours:.1f} 小时",
                    f"{snapshot.platform_count} platforms observed across "
                    f"{snapshot.first_observation_interval_hours:.1f} hours",
                ),
                x=0.08,
                y=0.97,
                ha="left",
                color=ChartTheme.TEXT,
                fontsize=13,
            )
            figure.legend(
                handles=(
                    Patch(
                        facecolor="none",
                        edgecolor=ChartTheme.NEGATIVE,
                        linewidth=2,
                        label=select(
                            language,
                            "首次收录单元格 / 波次",
                            "First-observed cell / wave",
                        ),
                    ),
                ),
                frameon=False,
                loc="upper right",
                bbox_to_anchor=(0.94, 0.965),
            )
            figure.text(
                0.08,
                0.025,
                select(
                    language,
                    "数字为当日收录量；波次只表示首次收录时间，"
                    "不代表转载边或因果路径。",
                    "Numbers are daily observed counts; waves show timing, not repost "
                    "edges or causality.",
                ),
                color=ChartTheme.MUTED,
                fontsize=8.2,
            )
            figure.subplots_adjust(left=0.16, right=0.96, bottom=0.23, top=0.76)

            output_path = output_directory / self.filename
            figure.savefig(
                output_path,
                dpi=ChartTheme.DPI,
                facecolor=ChartTheme.BACKGROUND,
                bbox_inches="tight",
            )
            figure.clear()

        return output_path
