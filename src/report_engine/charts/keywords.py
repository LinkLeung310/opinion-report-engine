"""Auditable phrase-coverage chart for the keywords section."""

from __future__ import annotations

from pathlib import Path

from matplotlib import rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from report_engine.assets import report_font_path
from report_engine.charts.theme import ChartTheme
from report_engine.sections.keywords import KeywordsSnapshot


class KeywordsChartBuilder:
    filename = "keyword-coverage.png"

    def build(self, snapshot: KeywordsSnapshot, output_directory: Path) -> Path:
        if not snapshot.has_data:
            raise ValueError("cannot chart keywords without recurring phrases")

        output_directory.mkdir(parents=True, exist_ok=True)
        phrases = snapshot.display_phrases
        positions = list(range(len(phrases)))
        positive = [phrase.positive_documents for phrase in phrases]
        neutral = [phrase.neutral_documents for phrase in phrases]
        negative = [phrase.negative_documents for phrase in phrases]
        negative_left = [
            positive_count + neutral_count
            for positive_count, neutral_count in zip(positive, neutral, strict=True)
        ]
        leading = snapshot.leading_phrases
        title = (
            f"{len(leading)} 个短语并列覆盖 {leading[0].document_count} 篇内容"
            if len(leading) > 1
            else f"{leading[0].text}覆盖 {leading[0].document_count} 篇内容，居首"
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
            height = max(3.2, min(4.8, 0.42 * len(phrases) + 1.25))
            figure = Figure(figsize=(7.2, height))
            FigureCanvasAgg(figure)
            axes = figure.subplots()
            ChartTheme.apply(figure, axes)
            axes.barh(
                positions,
                positive,
                color=ChartTheme.POSITIVE,
                label="正面",
            )
            axes.barh(
                positions,
                neutral,
                left=positive,
                color=ChartTheme.NEUTRAL,
                label="中性",
            )
            axes.barh(
                positions,
                negative,
                left=negative_left,
                color=ChartTheme.NEGATIVE,
                label="负面",
            )
            axes.set_yticks(
                positions,
                [
                    f"{phrase.text}（后期新增）"
                    if phrase.late_emerging
                    else phrase.text
                    for phrase in phrases
                ],
            )
            axes.invert_yaxis()
            axes.set_xlabel("提及该短语的文章数（同一文章只计一次）", color=ChartTheme.MUTED)
            axes.xaxis.set_major_locator(MaxNLocator(integer=True))
            maximum = max(phrase.document_count for phrase in phrases)
            axes.set_xlim(0, maximum * 1.32)
            for position, phrase in zip(positions, phrases, strict=True):
                axes.text(
                    phrase.document_count + maximum * 0.025,
                    position,
                    f"{phrase.document_count}",
                    va="center",
                    color=ChartTheme.TEXT,
                    fontsize=9,
                )
            figure.suptitle(
                title,
                x=0.08,
                y=0.98,
                ha="left",
                color=ChartTheme.TEXT,
                fontsize=13,
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
            figure.tight_layout(rect=(0, 0, 1, 0.88))

            output_path = output_directory / self.filename
            figure.savefig(
                output_path,
                dpi=ChartTheme.DPI,
                facecolor=ChartTheme.BACKGROUND,
                bbox_inches="tight",
            )
            figure.clear()

        return output_path
