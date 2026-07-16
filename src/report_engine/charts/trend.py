"""Daily stacked-sentiment chart for the heat-trend section."""

from __future__ import annotations

from math import ceil
from pathlib import Path

from matplotlib import rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.figure import Figure

from report_engine.assets import report_font_path
from report_engine.charts.theme import ChartTheme
from report_engine.config import Language
from report_engine.presentation import sentiment_label, select
from report_engine.sections.trend import TrendSnapshot


class TrendChartBuilder:
    filename = "daily-sentiment-trend.png"
    max_x_ticks = 10

    @classmethod
    def tick_positions(cls, point_count: int) -> tuple[int, ...]:
        if point_count <= 0:
            return ()
        if point_count <= cls.max_x_ticks:
            return tuple(range(point_count))
        final_position = point_count - 1
        step = ceil(final_position / (cls.max_x_ticks - 1))
        positions = list(range(0, final_position, step))
        positions.append(final_position)
        return tuple(positions)

    def build(
        self,
        snapshot: TrendSnapshot,
        output_directory: Path,
        language: Language = Language.ZH,
    ) -> Path:
        if not snapshot.has_data:
            raise ValueError("cannot chart an empty trend snapshot")

        output_directory.mkdir(parents=True, exist_ok=True)
        facts = snapshot.to_fact_set()
        font_path = report_font_path()
        fontManager.addfont(font_path)
        font_family = FontProperties(fname=font_path).get_name()
        positions = list(range(len(snapshot.points)))
        positive = [point.positive_articles for point in snapshot.points]
        neutral = [point.neutral_articles for point in snapshot.points]
        negative = [point.negative_articles for point in snapshot.points]
        neutral_bottom = positive
        negative_bottom = [
            positive_count + neutral_count
            for positive_count, neutral_count in zip(positive, neutral, strict=True)
        ]

        with rc_context(
            {
                "font.sans-serif": [font_family],
                "axes.unicode_minus": False,
            }
        ):
            figure = Figure(figsize=(7.2, 4.2))
            FigureCanvasAgg(figure)
            axes = figure.subplots()
            ChartTheme.apply(figure, axes)
            axes.bar(
                positions,
                positive,
                color=ChartTheme.POSITIVE,
                label=sentiment_label("positive", language),
            )
            axes.bar(
                positions,
                neutral,
                bottom=neutral_bottom,
                color=ChartTheme.NEUTRAL,
                label=sentiment_label("neutral", language),
            )
            axes.bar(
                positions,
                negative,
                bottom=negative_bottom,
                color=ChartTheme.NEGATIVE,
                label=sentiment_label("negative", language),
            )
            ticks = self.tick_positions(len(snapshot.points))
            axes.set_xticks(
                ticks,
                [
                    f"{snapshot.points[index].day.month}/{snapshot.points[index].day.day}"
                    for index in ticks
                ],
            )
            axes.set_title(
                select(
                    language,
                    f"{facts.get('peakDay').formatted_value} 达峰，单日 "
                    f"{facts.get('peakArticles').formatted_value} 篇内容",
                    f"Peak on {facts.get('peakDay').formatted_value}: "
                    f"{facts.get('peakArticles').formatted_value} articles",
                ),
                loc="left",
                color=ChartTheme.TEXT,
                pad=16,
            )
            axes.set_ylabel(
                select(language, "文章数", "Articles"),
                color=ChartTheme.MUTED,
            )
            axes.set_ylim(
                0,
                max(point.article_count for point in snapshot.points) * 1.25,
            )
            axes.legend(frameon=False, ncol=3, loc="upper right")
            figure.tight_layout()

            output_path = output_directory / self.filename
            figure.savefig(
                output_path,
                dpi=ChartTheme.DPI,
                facecolor=ChartTheme.BACKGROUND,
                bbox_inches="tight",
            )
            figure.clear()

        return output_path
