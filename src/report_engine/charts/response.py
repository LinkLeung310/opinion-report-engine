"""Balanced pre/post response comparison chart."""

from __future__ import annotations

from pathlib import Path

from matplotlib import rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties, fontManager

from report_engine.assets import report_font_path
from report_engine.charts.theme import ChartTheme
from report_engine.config import Language
from report_engine.presentation import sentiment_label, select, unavailable
from report_engine.sections.response import ResponseSnapshot, ResponseWindowStats


class ResponseChartBuilder:
    filename = "response-window-comparison.png"

    @staticmethod
    def _share_label(side: ResponseWindowStats, language: Language) -> str:
        share = side.share("negative")
        return unavailable(language) if share is None else f"{share:.1%}"

    def build(
        self,
        snapshot: ResponseSnapshot,
        output_directory: Path,
        language: Language = Language.ZH,
    ) -> Path:
        if not snapshot.has_comparison_data:
            raise ValueError("cannot chart an empty response comparison")

        output_directory.mkdir(parents=True, exist_ok=True)
        pre, post = snapshot.pre, snapshot.post
        sides = (pre, post)
        positions = (0, 1)
        positive = [side.positive_articles for side in sides]
        neutral = [side.neutral_articles for side in sides]
        negative = [side.negative_articles for side in sides]
        negative_bottom = [
            positive_count + neutral_count
            for positive_count, neutral_count in zip(positive, neutral, strict=True)
        ]
        font_path = report_font_path()
        fontManager.addfont(font_path)
        font_family = FontProperties(fname=font_path).get_name()

        with rc_context(
            {"font.sans-serif": [font_family], "axes.unicode_minus": False}
        ):
            figure = Figure(
                figsize=(6.8, 3.95 if language is Language.EN else 3.65)
            )
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
                bottom=positive,
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
            axes.set_xticks(
                positions,
                [
                    select(
                        language,
                        f"回应前\n{pre.date_range_label}",
                        f"Before response\n{pre.date_range_label}",
                    ),
                    select(
                        language,
                        f"回应后\n{post.date_range_label}",
                        f"After response\n{post.date_range_label}",
                    ),
                ],
            )
            axes.set_ylabel(
                select(language, "收录篇数", "Observed articles"),
                color=ChartTheme.MUTED,
            )
            maximum = max(pre.article_count, post.article_count, 1)
            axes.set_ylim(0, maximum * 1.38)
            axes.set_yticks(range(0, maximum + 1))
            for position, side in zip(positions, sides, strict=True):
                axes.text(
                    position,
                    side.article_count + maximum * 0.06,
                    select(
                        language,
                        f"{side.article_count} 篇｜日均 {side.daily_average:.1f}\n"
                        f"负面 {self._share_label(side, language)}",
                        f"{side.article_count} articles | daily avg "
                        f"{side.daily_average:.1f}\nNegative "
                        f"{self._share_label(side, language)}",
                    ),
                    ha="center",
                    va="bottom",
                    color=ChartTheme.TEXT,
                    fontsize=9,
                )

            figure.suptitle(
                select(
                    language,
                    f"回应日前后收录 {pre.article_count}→{post.article_count} 篇，"
                    f"负面占比 {self._share_label(pre, language)}→"
                    f"{self._share_label(post, language)}",
                    f"Observed volume {pre.article_count}→{post.article_count}; "
                    f"negative share {self._share_label(pre, language)}→"
                    f"{self._share_label(post, language)}",
                ),
                x=0.08,
                y=0.98,
                ha="left",
                color=ChartTheme.TEXT,
                fontsize=12.5,
            )
            handles, labels = axes.get_legend_handles_labels()
            figure.legend(
                handles,
                labels,
                frameon=False,
                ncol=3,
                loc="upper center" if language is Language.EN else "upper right",
                bbox_to_anchor=(
                    (0.72, 0.86) if language is Language.EN else (0.97, 0.98)
                ),
            )
            figure.text(
                0.08,
                0.015,
                select(
                    language,
                    f"等长窗口：{pre.date_range_label} 与 {post.date_range_label}；"
                    f"回应日 {snapshot.window.response_date.isoformat()} 整体排除。"
                    "前后差异仅为观察结果，不证明因果或回应效果。",
                    f"Equal windows: {pre.date_range_label} and {post.date_range_label}; "
                    f"response day {snapshot.window.response_date.isoformat()} excluded. "
                    "Observed differences do not establish causality or effectiveness.",
                ),
                color=ChartTheme.MUTED,
                fontsize=8.2,
            )
            figure.tight_layout(
                rect=(0, 0.09, 1, 0.70 if language is Language.EN else 0.86)
            )

            output_path = output_directory / self.filename
            figure.savefig(
                output_path,
                dpi=ChartTheme.DPI,
                facecolor=ChartTheme.BACKGROUND,
                bbox_inches="tight",
            )
            figure.clear()

        return output_path
