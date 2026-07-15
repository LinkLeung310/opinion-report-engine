"""Two-panel comparison chart for the platform-performance section."""

from __future__ import annotations

from pathlib import Path

from matplotlib import rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.figure import Figure

from report_engine.assets import report_font_path
from report_engine.charts.theme import ChartTheme
from report_engine.sections.platforms import PlatformsSnapshot


class PlatformsChartBuilder:
    filename = "platform-performance.png"

    def build(self, snapshot: PlatformsSnapshot, output_directory: Path) -> Path:
        if not snapshot.has_data:
            raise ValueError("cannot chart an empty platforms snapshot")

        output_directory.mkdir(parents=True, exist_ok=True)
        rows = snapshot.display_rows
        facts = snapshot.to_fact_set()
        font_path = report_font_path()
        fontManager.addfont(font_path)
        font_family = FontProperties(fname=font_path).get_name()
        positions = list(range(len(rows)))
        positive = [row.positive_articles for row in rows]
        neutral = [row.neutral_articles for row in rows]
        negative = [row.negative_articles for row in rows]
        neutral_left = positive
        negative_left = [
            positive_count + neutral_count
            for positive_count, neutral_count in zip(positive, neutral, strict=True)
        ]
        engagement = [row.total_engagement for row in rows]

        with rc_context(
            {
                "font.sans-serif": [font_family],
                "axes.unicode_minus": False,
            }
        ):
            height = max(3.1, min(5.5, 0.46 * len(rows) + 1.2))
            figure = Figure(figsize=(7.2, height))
            FigureCanvasAgg(figure)
            volume_axes, engagement_axes = figure.subplots(
                1,
                2,
                sharey=True,
                gridspec_kw={"width_ratios": (1.25, 1)},
            )
            ChartTheme.apply(figure, volume_axes)
            ChartTheme.apply(figure, engagement_axes)

            volume_axes.barh(
                positions, positive, color=ChartTheme.POSITIVE, label="正面"
            )
            volume_axes.barh(
                positions,
                neutral,
                left=neutral_left,
                color=ChartTheme.NEUTRAL,
                label="中性",
            )
            volume_axes.barh(
                positions,
                negative,
                left=negative_left,
                color=ChartTheme.NEGATIVE,
                label="负面",
            )
            volume_axes.set_yticks(positions, [row.platform for row in rows])
            volume_axes.invert_yaxis()
            volume_axes.set_xlabel("文章数", color=ChartTheme.MUTED)
            volume_axes.set_title("文章量与情感", loc="left", color=ChartTheme.TEXT)
            volume_axes.set_xlim(0, max(row.article_count for row in rows) * 1.28)
            for position, row in zip(positions, rows, strict=True):
                volume_axes.text(
                    row.article_count + 0.08,
                    position,
                    f"{row.article_count:,}",
                    va="center",
                    color=ChartTheme.TEXT,
                    fontsize=9,
                )
            bars = engagement_axes.barh(
                positions, engagement, color=ChartTheme.ACCENT, height=0.68
            )
            engagement_axes.set_xlabel("总互动", color=ChartTheme.MUTED)
            engagement_axes.set_title("互动集中度", loc="left", color=ChartTheme.TEXT)
            engagement_axes.set_xlim(0, max(engagement or [0]) * 1.3 or 1)
            engagement_axes.bar_label(
                bars,
                labels=[f"{value:,}" for value in engagement],
                padding=3,
                color=ChartTheme.TEXT,
                fontsize=9,
            )
            leaders = facts.get("volumeLeaders").formatted_value
            count = facts.get("leadingArticleCount").formatted_value
            tie_count = facts.get("volumeLeaderCount").raw_value
            volume_insight = (
                f"{leaders}并列 {count} 篇"
                if isinstance(tie_count, int) and tie_count > 1
                else f"{leaders}以 {count} 篇居首"
            )
            engagement_leader = facts.get("engagementLeader").formatted_value
            figure.suptitle(
                f"{volume_insight}，{engagement_leader}互动最高",
                x=0.07,
                ha="left",
                color=ChartTheme.TEXT,
                fontsize=13,
            )
            legend_handles, legend_labels = volume_axes.get_legend_handles_labels()
            figure.legend(
                legend_handles,
                legend_labels,
                frameon=False,
                ncol=3,
                loc="upper center",
                bbox_to_anchor=(0.39, 0.82),
            )
            figure.tight_layout(rect=(0, 0, 1, 0.92))

            output_path = output_directory / self.filename
            figure.savefig(
                output_path,
                dpi=ChartTheme.DPI,
                facecolor=ChartTheme.BACKGROUND,
                bbox_inches="tight",
            )
            figure.clear()

        return output_path
