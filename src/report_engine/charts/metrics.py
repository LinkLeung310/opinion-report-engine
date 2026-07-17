"""Charts for the all-network metrics section."""

from __future__ import annotations

from pathlib import Path

from matplotlib import rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.figure import Figure

from report_engine.assets import report_font_path
from report_engine.charts.theme import ChartTheme
from report_engine.config import Language
from report_engine.presentation import sentiment_label, select
from report_engine.sections.metrics import MetricsSnapshot


class MetricsChartBuilder:
    filename = "sentiment-overview.png"

    def build(
        self,
        snapshot: MetricsSnapshot,
        output_directory: Path,
        language: Language = Language.ZH,
    ) -> Path:
        if not snapshot.has_data:
            raise ValueError("cannot chart an empty metrics snapshot")

        output_directory.mkdir(parents=True, exist_ok=True)
        facts = snapshot.to_fact_set()
        font_path = report_font_path()
        fontManager.addfont(font_path)
        font_family = FontProperties(fname=font_path).get_name()
        labels = [
            sentiment_label(sentiment, language)
            for sentiment in ("positive", "neutral", "negative")
        ]
        values = [
            snapshot.positive_articles,
            snapshot.neutral_articles,
            snapshot.negative_articles,
        ]
        colors = [ChartTheme.POSITIVE, ChartTheme.NEUTRAL, ChartTheme.NEGATIVE]

        with rc_context(
            {
                "font.sans-serif": [
                    font_family,
                ],
                "axes.unicode_minus": False,
            }
        ):
            figure = Figure(figsize=(7.2, 4.2))
            FigureCanvasAgg(figure)
            axes = figure.subplots()
            ChartTheme.apply(figure, axes)
            bars = axes.bar(labels, values, color=colors, width=0.58)
            axes.bar_label(bars, labels=[f"{value:,}" for value in values], padding=4)
            negative_ratio = facts.get("negativeRatio").formatted_value
            axes.set_title(
                select(
                    language,
                    f"负面内容占比达到 {negative_ratio}",
                    f"Negative content accounts for {negative_ratio}",
                ),
                loc="left",
                color=ChartTheme.TEXT,
                pad=16,
            )
            axes.set_ylabel(
                select(language, "文章数", "Articles"),
                color=ChartTheme.MUTED,
            )
            axes.set_ylim(0, max(values) * 1.25)
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
