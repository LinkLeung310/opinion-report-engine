"""Aligned stored-interaction and structured-risk signal chart."""

from __future__ import annotations

from pathlib import Path

from matplotlib import rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.patches import Patch

from report_engine.assets import report_font_path
from report_engine.charts.theme import ChartTheme
from report_engine.sections.top_content import TopContentSnapshot


class TopContentChartBuilder:
    filename = "top-content-signals.png"
    sentiment_colors = {
        "positive": ChartTheme.POSITIVE,
        "neutral": ChartTheme.NEUTRAL,
        "negative": ChartTheme.NEGATIVE,
    }
    severity_positions = {
        None: 0,
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4,
    }

    def build(self, snapshot: TopContentSnapshot, output_directory: Path) -> Path:
        if not snapshot.has_selected_records:
            raise ValueError("cannot chart top-content without selected records")

        output_directory.mkdir(parents=True, exist_ok=True)
        rows = snapshot.records
        positions = list(range(len(rows)))
        totals = [record.total_engagement for record in rows]
        colors = [self.sentiment_colors[record.sentiment] for record in rows]
        labels = [
            f"{record.category_label} · {record.external_id}\n{record.title}"
            for record in rows
        ]
        severity_values = [
            -1
            if record.sentiment != "negative"
            else self.severity_positions[record.severity]
            for record in rows
        ]
        score_labels = [
            "不适用"
            if record.sentiment != "negative"
            else (
                f"负面分 {record.negative_score}"
                if record.negative_score is not None
                else "负面分未提供"
            )
            for record in rows
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
            height = max(3.0, 0.35 * len(rows) + 1.6)
            figure = Figure(figsize=(7.2, height))
            FigureCanvasAgg(figure)
            engagement_axes, risk_axes = figure.subplots(
                1,
                2,
                gridspec_kw={"width_ratios": (1.35, 1)},
                sharey=True,
            )
            ChartTheme.apply(figure, engagement_axes)
            ChartTheme.apply(figure, risk_axes)

            bars = engagement_axes.barh(
                positions,
                totals,
                color=colors,
                height=0.58,
            )
            engagement_axes.set_yticks(positions, labels)
            engagement_axes.invert_yaxis()
            engagement_axes.set_xlabel("单篇存储互动计数", color=ChartTheme.MUTED)
            engagement_axes.set_title("互动信号", loc="left", color=ChartTheme.TEXT)
            max_total = max(totals) or 1
            engagement_axes.set_xlim(0, max_total * 1.28)
            engagement_axes.bar_label(
                bars,
                labels=[f"{value:,}" for value in totals],
                padding=3,
                color=ChartTheme.TEXT,
                fontsize=8.3,
            )

            risk_axes.scatter(
                severity_values,
                positions,
                s=95,
                color=colors,
                edgecolor=ChartTheme.BACKGROUND,
                linewidth=1.2,
                zorder=3,
            )
            for x_value, y_value, label in zip(
                severity_values,
                positions,
                score_labels,
                strict=True,
            ):
                risk_axes.annotate(
                    label,
                    (x_value, y_value),
                    xytext=(0, 10),
                    textcoords="offset points",
                    ha="center",
                    fontsize=7.8,
                    color=ChartTheme.TEXT,
                )
            risk_axes.set_xlim(-1.45, 4.45)
            risk_axes.set_xticks(
                (-1, 0, 1, 2, 3, 4),
                ("不适用", "未分类", "低", "中", "高", "危"),
                rotation=25,
            )
            risk_axes.set_xlabel("存储严重性分级", color=ChartTheme.MUTED)
            risk_axes.set_title("结构化风险信号", loc="left", color=ChartTheme.TEXT)
            risk_axes.tick_params(axis="y", left=False, labelleft=False)
            risk_axes.grid(axis="x", color="#E5E7EB", linewidth=0.7)

            counts = snapshot.category_counts
            figure.suptitle(
                f"{len(rows)} 篇代表内容中，{counts['dual_signal']} 篇同时进入两类前三",
                x=0.06,
                y=0.98,
                ha="left",
                color=ChartTheme.TEXT,
                fontsize=13,
            )
            figure.legend(
                handles=(
                    Patch(facecolor=ChartTheme.POSITIVE, label="正面"),
                    Patch(facecolor=ChartTheme.NEUTRAL, label="中性"),
                    Patch(facecolor=ChartTheme.NEGATIVE, label="负面"),
                ),
                frameon=False,
                ncol=3,
                loc="upper right",
                bbox_to_anchor=(0.97, 0.995),
            )
            figure.subplots_adjust(
                left=0.24,
                right=0.96,
                bottom=0.15,
                top=0.75,
                wspace=0.13,
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
