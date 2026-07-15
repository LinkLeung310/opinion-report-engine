"""Volume and sentiment-composition chart for stored source types."""

from __future__ import annotations

from pathlib import Path

from matplotlib import rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator, PercentFormatter

from report_engine.assets import report_font_path
from report_engine.charts.theme import ChartTheme
from report_engine.sections.media_social import MediaSocialSnapshot


class MediaSocialChartBuilder:
    filename = "media-social-comparison.png"

    def build(
        self,
        snapshot: MediaSocialSnapshot,
        output_directory: Path,
    ) -> Path:
        if not snapshot.has_data:
            raise ValueError("cannot chart an empty media-social snapshot")

        output_directory.mkdir(parents=True, exist_ok=True)
        font_path = report_font_path()
        fontManager.addfont(font_path)
        font_family = FontProperties(fname=font_path).get_name()
        positions = [0, 1]
        labels = [f"{row.label_zh}\nn={row.article_count}" for row in snapshot.rows]
        positive_counts = [row.positive_articles for row in snapshot.rows]
        neutral_counts = [row.neutral_articles for row in snapshot.rows]
        negative_counts = [row.negative_articles for row in snapshot.rows]
        shares = [row.sentiment_shares for row in snapshot.rows]
        positive_shares = [float(value[0]) if value is not None else 0 for value in shares]
        neutral_shares = [float(value[1]) if value is not None else 0 for value in shares]
        negative_shares = [float(value[2]) if value is not None else 0 for value in shares]

        with rc_context(
            {
                "font.sans-serif": [font_family],
                "axes.unicode_minus": False,
            }
        ):
            figure = Figure(figsize=(7.2, 3.25))
            FigureCanvasAgg(figure)
            count_axes, share_axes = figure.subplots(1, 2)
            for axes in (count_axes, share_axes):
                ChartTheme.apply(figure, axes)

            count_axes.bar(
                positions,
                positive_counts,
                color=ChartTheme.POSITIVE,
                label="正面",
            )
            count_axes.bar(
                positions,
                neutral_counts,
                bottom=positive_counts,
                color=ChartTheme.NEUTRAL,
                label="中性",
            )
            count_bottom = [
                positive + neutral
                for positive, neutral in zip(
                    positive_counts, neutral_counts, strict=True
                )
            ]
            count_axes.bar(
                positions,
                negative_counts,
                bottom=count_bottom,
                color=ChartTheme.NEGATIVE,
                label="负面",
            )
            count_axes.set_title("内容量与情感", loc="left", color=ChartTheme.TEXT)
            count_axes.set_xticks(positions, labels)
            count_axes.set_ylabel("文章数", color=ChartTheme.MUTED)
            count_axes.yaxis.set_major_locator(MaxNLocator(integer=True))
            count_axes.set_ylim(0, max(row.article_count for row in snapshot.rows) * 1.18)
            for position, row in zip(positions, snapshot.rows, strict=True):
                count_axes.text(
                    position,
                    row.article_count + max(snapshot.article_count * 0.012, 0.08),
                    f"{row.article_count}",
                    ha="center",
                    va="bottom",
                    color=ChartTheme.TEXT,
                    fontsize=9,
                )

            share_axes.bar(
                positions,
                positive_shares,
                color=ChartTheme.POSITIVE,
                label="正面",
            )
            share_axes.bar(
                positions,
                neutral_shares,
                bottom=positive_shares,
                color=ChartTheme.NEUTRAL,
                label="中性",
            )
            share_bottom = [
                positive + neutral
                for positive, neutral in zip(
                    positive_shares, neutral_shares, strict=True
                )
            ]
            share_axes.bar(
                positions,
                negative_shares,
                bottom=share_bottom,
                color=ChartTheme.NEGATIVE,
                label="负面",
            )
            share_axes.set_title("组内情感构成", loc="left", color=ChartTheme.TEXT)
            share_axes.set_xticks(positions, labels)
            share_axes.set_ylabel("组内占比", color=ChartTheme.MUTED)
            share_axes.set_ylim(0, 1)
            share_axes.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
            for position, row in zip(positions, snapshot.rows, strict=True):
                if row.article_count == 0:
                    share_axes.text(
                        position,
                        0.04,
                        "无样本",
                        ha="center",
                        va="bottom",
                        color=ChartTheme.MUTED,
                        fontsize=9,
                    )

            figure.suptitle(
                self._title(snapshot),
                x=0.07,
                y=0.98,
                ha="left",
                color=ChartTheme.TEXT,
                fontsize=13,
            )
            handles, legend_labels = count_axes.get_legend_handles_labels()
            figure.legend(
                handles,
                legend_labels,
                frameon=False,
                ncol=3,
                loc="upper right",
                bbox_to_anchor=(0.97, 0.94),
            )
            figure.text(
                0.5,
                0.04,
                "存储 source_type 的绝对量与组内构成",
                ha="center",
                color=ChartTheme.MUTED,
                fontsize=8,
            )
            figure.subplots_adjust(
                left=0.09,
                right=0.97,
                bottom=0.24,
                top=0.72,
                wspace=0.36,
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

    @staticmethod
    def _title(snapshot: MediaSocialSnapshot) -> str:
        media_share = snapshot.article_share(snapshot.media)
        social_share = snapshot.article_share(snapshot.social)
        if not snapshot.comparison_available:
            populated = snapshot.media if snapshot.media.article_count else snapshot.social
            return f"仅{populated.label_zh}有样本，跨组情感不可比较"
        delta = snapshot.social_minus_media_negative_share
        if delta is None:
            raise ValueError("Comparable source types require a negative-share delta")
        if delta > 0:
            comparison = f"社交负面占比高 {delta * 100:.1f} 个百分点"
        elif delta < 0:
            comparison = f"社交负面占比低 {abs(delta) * 100:.1f} 个百分点"
        else:
            comparison = "两组负面占比相同"
        return (
            f"媒体/社交量级 {media_share:.1%}/{social_share:.1%}，{comparison}"
        )
