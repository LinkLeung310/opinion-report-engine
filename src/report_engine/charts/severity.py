"""Two-panel risk distribution chart for the negative-severity section."""

from __future__ import annotations

from pathlib import Path

from matplotlib import rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.figure import Figure

from report_engine.assets import report_font_path
from report_engine.charts.theme import ChartTheme
from report_engine.config import Language
from report_engine.presentation import severity_label, select
from report_engine.sections.severity import SeveritySnapshot


class SeverityChartBuilder:
    filename = "severity-distribution.png"
    risk_colors = (
        ChartTheme.POSITIVE,
        "#84CC16",
        ChartTheme.NEUTRAL,
        "#F97316",
        ChartTheme.NEGATIVE,
    )

    def build(
        self,
        snapshot: SeveritySnapshot,
        output_directory: Path,
        language: Language = Language.ZH,
    ) -> Path:
        if not snapshot.has_data:
            raise ValueError("cannot chart an empty severity snapshot")

        output_directory.mkdir(parents=True, exist_ok=True)
        facts = snapshot.to_fact_set()
        severity_labels = tuple(
            severity_label(value, language)
            for value in ("low", "medium", "high", "critical")
        )
        severity_counts = (
            snapshot.low_articles,
            snapshot.medium_articles,
            snapshot.high_articles,
            snapshot.critical_articles,
        )
        score_labels = ("1", "2", "3", "4", "5")
        score_counts = (
            snapshot.score_1_articles,
            snapshot.score_2_articles,
            snapshot.score_3_articles,
            snapshot.score_4_articles,
            snapshot.score_5_articles,
        )
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
            severity_axes, score_axes = figure.subplots(1, 2)
            ChartTheme.apply(figure, severity_axes)
            ChartTheme.apply(figure, score_axes)

            severity_bars = severity_axes.bar(
                severity_labels,
                severity_counts,
                color=(
                    self.risk_colors[0],
                    self.risk_colors[2],
                    self.risk_colors[3],
                    self.risk_colors[4],
                ),
                width=0.62,
            )
            severity_axes.set_title(
                select(language, "严重性分级", "Severity classification"),
                loc="left",
                color=ChartTheme.TEXT,
            )
            severity_axes.set_ylabel(
                select(language, "负面文章数", "Negative articles"),
                color=ChartTheme.MUTED,
            )
            severity_axes.set_ylim(0, max((*severity_counts, 1)) * 1.28)
            severity_axes.bar_label(
                severity_bars,
                labels=[f"{value:,}" for value in severity_counts],
                padding=3,
                color=ChartTheme.TEXT,
                fontsize=9,
            )

            score_bars = score_axes.bar(
                score_labels,
                score_counts,
                color=self.risk_colors,
                width=0.62,
            )
            score_axes.set_title(
                select(language, "负面程度分数", "Negative score"),
                loc="left",
                color=ChartTheme.TEXT,
            )
            score_axes.set_xlabel(
                select(language, "分数（1–5）", "Score (1–5)"),
                color=ChartTheme.MUTED,
            )
            score_axes.set_ylabel(
                select(language, "负面文章数", "Negative articles"),
                color=ChartTheme.MUTED,
            )
            score_axes.set_ylim(0, max((*score_counts, 1)) * 1.28)
            score_axes.bar_label(
                score_bars,
                labels=[f"{value:,}" for value in score_counts],
                padding=3,
                color=ChartTheme.TEXT,
                fontsize=9,
            )

            figure.suptitle(
                select(
                    language,
                    f"高/危负面占比 {facts.get('highCriticalRatio').formatted_value}",
                    "High/critical negatives account for "
                    f"{facts.get('highCriticalRatio').formatted_value}",
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
