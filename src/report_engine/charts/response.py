"""Balanced pre/post response comparison chart."""

from __future__ import annotations

from pathlib import Path

from matplotlib import rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties, fontManager

from report_engine.assets import report_font_path
from report_engine.charts.theme import ChartTheme
from report_engine.sections.response import ResponseSnapshot, ResponseWindowStats


class ResponseChartBuilder:
    filename = "response-window-comparison.png"

    @staticmethod
    def _share_label(side: ResponseWindowStats) -> str:
        share = side.share("negative")
        return "不可用" if share is None else f"{share:.1%}"

    def build(self, snapshot: ResponseSnapshot, output_directory: Path) -> Path:
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
            figure = Figure(figsize=(6.8, 3.65))
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
                    f"回应前\n{pre.date_range_label}",
                    f"回应后\n{post.date_range_label}",
                ],
            )
            axes.set_ylabel("收录篇数", color=ChartTheme.MUTED)
            maximum = max(pre.article_count, post.article_count, 1)
            axes.set_ylim(0, maximum * 1.38)
            axes.set_yticks(range(0, maximum + 1))
            for position, side in zip(positions, sides, strict=True):
                axes.text(
                    position,
                    side.article_count + maximum * 0.06,
                    f"{side.article_count} 篇｜日均 {side.daily_average:.1f}\n"
                    f"负面 {self._share_label(side)}",
                    ha="center",
                    va="bottom",
                    color=ChartTheme.TEXT,
                    fontsize=9,
                )

            figure.suptitle(
                f"回应日前后收录 {pre.article_count}→{post.article_count} 篇，"
                f"负面占比 {self._share_label(pre)}→{self._share_label(post)}",
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
                loc="upper right",
                bbox_to_anchor=(0.97, 0.98),
            )
            figure.text(
                0.08,
                0.015,
                f"等长窗口：{pre.date_range_label} 与 {post.date_range_label}；"
                f"回应日 {snapshot.window.response_date.isoformat()} 整体排除。"
                "前后差异仅为观察结果，不证明因果或回应效果。",
                color=ChartTheme.MUTED,
                fontsize=8.2,
            )
            figure.tight_layout(rect=(0, 0.09, 1, 0.86))

            output_path = output_directory / self.filename
            figure.savefig(
                output_path,
                dpi=ChartTheme.DPI,
                facecolor=ChartTheme.BACKGROUND,
                bbox_inches="tight",
            )
            figure.clear()

        return output_path
