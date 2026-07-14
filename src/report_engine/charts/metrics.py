"""Charts for the all-network metrics section."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from report_engine.charts.theme import ChartTheme
from report_engine.sections.metrics import MetricsSnapshot


class MetricsChartBuilder:
    filename = "sentiment-overview.png"

    def build(self, snapshot: MetricsSnapshot, output_directory: Path) -> Path:
        if not snapshot.has_data:
            raise ValueError("cannot chart an empty metrics snapshot")

        output_directory.mkdir(parents=True, exist_ok=True)
        facts = snapshot.to_fact_set()
        labels = ["正面", "中性", "负面"]
        values = [
            snapshot.positive_articles,
            snapshot.neutral_articles,
            snapshot.negative_articles,
        ]
        colors = [ChartTheme.POSITIVE, ChartTheme.NEUTRAL, ChartTheme.NEGATIVE]

        with plt.rc_context(
            {
                "font.sans-serif": [
                    "Microsoft YaHei",
                    "Noto Sans CJK SC",
                    "Noto Sans SC",
                    "DejaVu Sans",
                ],
                "axes.unicode_minus": False,
            }
        ):
            figure, axes = plt.subplots(figsize=(7.2, 4.2))
            ChartTheme.apply(figure, axes)
            bars = axes.bar(labels, values, color=colors, width=0.58)
            axes.bar_label(bars, labels=[f"{value:,}" for value in values], padding=4)
            negative_ratio = facts.get("negativeRatio").formatted_value
            axes.set_title(
                f"负面内容占比达到 {negative_ratio}",
                loc="left",
                color=ChartTheme.TEXT,
                fontweight="bold",
                pad=16,
            )
            axes.set_ylabel("文章数", color=ChartTheme.MUTED)
            axes.set_ylim(0, max(values) * 1.25)
            figure.tight_layout()

            output_path = output_directory / self.filename
            figure.savefig(
                output_path,
                dpi=ChartTheme.DPI,
                facecolor=ChartTheme.BACKGROUND,
                bbox_inches="tight",
            )
            plt.close(figure)

        return output_path
