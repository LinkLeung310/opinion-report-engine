"""Two-panel interaction composition and ranked-record chart."""

from __future__ import annotations

from pathlib import Path

from matplotlib import rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from report_engine.assets import report_font_path
from report_engine.charts.theme import ChartTheme
from report_engine.config import Language
from report_engine.presentation import sentiment_label, select
from report_engine.sections.engagement import EngagementSnapshot


class EngagementChartBuilder:
    filename = "engagement-composition.png"
    action_colors = (ChartTheme.ACCENT, "#7C3AED", "#0891B2", "#64748B")
    sentiment_colors = {
        "positive": ChartTheme.POSITIVE,
        "neutral": ChartTheme.NEUTRAL,
        "negative": ChartTheme.NEGATIVE,
    }

    def build(
        self,
        snapshot: EngagementSnapshot,
        output_directory: Path,
        language: Language = Language.ZH,
    ) -> Path:
        if not snapshot.has_engagement:
            raise ValueError("cannot chart engagement without positive counters")

        output_directory.mkdir(parents=True, exist_ok=True)
        facts = snapshot.to_fact_set()
        rows = snapshot.records
        font_path = report_font_path()
        fontManager.addfont(font_path)
        font_family = FontProperties(fname=font_path).get_name()

        action_labels = tuple(
            select(language, zh, en)
            for zh, en in (
                ("点赞", "Likes"),
                ("评论", "Comments"),
                ("转发", "Shares"),
                ("收藏", "Favorites"),
            )
        )
        action_counts = (snapshot.likes, snapshot.comments, snapshot.shares, snapshot.favorites)
        action_shares = tuple(snapshot.action_share(count) for count in action_counts)
        positions = list(range(len(rows)))
        record_totals = [record.total_engagement for record in rows]
        record_colors = [self.sentiment_colors[record.sentiment] for record in rows]
        record_labels = [
            f"{record.external_id}\n{record.title}" for record in rows
        ]

        with rc_context(
            {
                "font.sans-serif": [font_family],
                "axes.unicode_minus": False,
            }
        ):
            height = max(4.0, 0.62 * len(rows) + 1.45)
            figure = Figure(figsize=(7.2, height))
            FigureCanvasAgg(figure)
            action_axes, record_axes = figure.subplots(
                1,
                2,
                gridspec_kw={"width_ratios": (0.9, 1.55)},
            )
            ChartTheme.apply(figure, action_axes)
            ChartTheme.apply(figure, record_axes)

            action_bars = action_axes.barh(
                list(range(4)),
                action_counts,
                color=self.action_colors,
                height=0.62,
            )
            action_axes.set_yticks(list(range(4)), action_labels)
            action_axes.invert_yaxis()
            action_axes.set_xlabel(
                select(language, "存储互动计数", "Stored engagement count"),
                color=ChartTheme.MUTED,
            )
            action_axes.set_title(
                select(language, "互动构成", "Engagement composition"),
                loc="left",
                color=ChartTheme.TEXT,
            )
            action_axes.set_xlim(0, max(action_counts) * 1.48)
            action_axes.bar_label(
                action_bars,
                labels=[
                    select(
                        language,
                        f"{count:,}（{share:.1%}）",
                        f"{count:,} ({share:.1%})",
                    )
                    for count, share in zip(action_counts, action_shares, strict=True)
                ],
                padding=3,
                color=ChartTheme.TEXT,
                fontsize=8.5,
            )

            record_bars = record_axes.barh(
                positions,
                record_totals,
                color=record_colors,
                height=0.62,
            )
            record_axes.set_yticks(positions, record_labels)
            record_axes.invert_yaxis()
            record_axes.set_xlabel(
                select(language, "单篇总互动计数", "Stored engagement per record"),
                color=ChartTheme.MUTED,
            )
            record_axes.set_title(
                select(language, "高计数内容", "Highest-count records"),
                loc="left",
                color=ChartTheme.TEXT,
            )
            record_axes.set_xlim(0, max(record_totals) * 1.28)
            record_axes.bar_label(
                record_bars,
                labels=[f"{value:,}" for value in record_totals],
                padding=3,
                color=ChartTheme.TEXT,
                fontsize=8.5,
            )

            leader_count = facts.get("leadingRecordCount").raw_value
            title = (
                select(
                    language,
                    f"{leader_count} 篇内容并列最高，前三篇占 "
                    f"{facts.get('topThreeRecordsShare').formatted_value}",
                    f"{leader_count} records tie for first; top three account for "
                    f"{facts.get('topThreeRecordsShare').formatted_value}",
                )
                if isinstance(leader_count, int) and leader_count > 1
                else select(
                    language,
                    f"最高单篇占 {facts.get('topRecordShare').formatted_value}，"
                    f"前三篇合计 {facts.get('topThreeRecordsShare').formatted_value}",
                    f"Top record accounts for {facts.get('topRecordShare').formatted_value}; "
                    f"top three account for {facts.get('topThreeRecordsShare').formatted_value}",
                )
            )
            figure.suptitle(
                title,
                x=0.06,
                y=0.98,
                ha="left",
                color=ChartTheme.TEXT,
                fontsize=13,
            )
            legend = [
                Patch(
                    facecolor=ChartTheme.POSITIVE,
                    label=sentiment_label("positive", language),
                ),
                Patch(
                    facecolor=ChartTheme.NEUTRAL,
                    label=sentiment_label("neutral", language),
                ),
                Patch(
                    facecolor=ChartTheme.NEGATIVE,
                    label=sentiment_label("negative", language),
                ),
            ]
            figure.legend(
                handles=legend,
                frameon=False,
                ncol=3,
                loc="upper right",
                bbox_to_anchor=(0.97, 0.91),
            )
            figure.subplots_adjust(
                left=0.08,
                right=0.96,
                bottom=0.14,
                top=0.78,
                wspace=0.92,
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
