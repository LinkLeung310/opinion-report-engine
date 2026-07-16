"""Negative-document coverage by fixed issue dimension."""

from __future__ import annotations

from pathlib import Path

from matplotlib import rc_context
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.patches import Patch

from report_engine.assets import report_font_path
from report_engine.charts.theme import ChartTheme
from report_engine.sections.negative_themes import NegativeThemesSnapshot


class NegativeThemesChartBuilder:
    filename = "negative-theme-coverage.png"
    other_negative = "#FCA5A5"

    def build(self, snapshot: NegativeThemesSnapshot, output_directory: Path) -> Path:
        if not snapshot.has_display_themes:
            raise ValueError("cannot chart negative themes without display themes")

        output_directory.mkdir(parents=True, exist_ok=True)
        themes = snapshot.display_themes
        positions = list(range(len(themes)))
        high_critical = [theme.high_critical_articles for theme in themes]
        other = [theme.article_count - theme.high_critical_articles for theme in themes]

        font_path = report_font_path()
        fontManager.addfont(font_path)
        font_family = FontProperties(fname=font_path).get_name()
        with rc_context(
            {
                "font.sans-serif": [font_family],
                "axes.unicode_minus": False,
            }
        ):
            figure = Figure(figsize=(7.2, 3.15))
            FigureCanvasAgg(figure)
            axes = figure.subplots()
            ChartTheme.apply(figure, axes)
            axes.barh(
                positions,
                high_critical,
                color=ChartTheme.NEGATIVE,
                height=0.54,
                label="高/危负面",
            )
            axes.barh(
                positions,
                other,
                left=high_critical,
                color=self.other_negative,
                height=0.54,
                label="其他负面",
            )
            axes.set_yticks(positions, [theme.label_zh for theme in themes])
            axes.invert_yaxis()
            axes.set_xlabel("匹配负面内容数", color=ChartTheme.MUTED)
            axes.xaxis.get_major_locator().set_params(integer=True)
            axes.grid(axis="x", color="#E5E7EB", linewidth=0.7)

            max_count = max(theme.article_count for theme in themes)
            axes.set_xlim(0, max(max_count * 1.75, max_count + 3.5))
            for position, theme in zip(positions, themes, strict=True):
                share = theme.article_count / snapshot.negative_article_count
                axes.text(
                    theme.article_count + 0.12,
                    position,
                    f"{theme.article_count}/{snapshot.negative_article_count} · "
                    f"{share:.1%}｜关切 {theme.concern_articles} · 诉求 {theme.demand_articles}",
                    va="center",
                    fontsize=8.3,
                    color=ChartTheme.TEXT,
                )

            lead = themes[0]
            lead_share = lead.article_count / snapshot.negative_article_count
            figure.suptitle(
                f"{lead.label_zh}覆盖 {lead.article_count}/{snapshot.negative_article_count} "
                f"篇负面内容（{lead_share:.1%}）",
                x=0.08,
                y=0.97,
                ha="left",
                color=ChartTheme.TEXT,
                fontsize=13,
            )
            figure.legend(
                handles=(
                    Patch(facecolor=ChartTheme.NEGATIVE, label="高/危负面"),
                    Patch(facecolor=self.other_negative, label="其他负面"),
                ),
                frameon=False,
                ncol=2,
                loc="upper right",
                bbox_to_anchor=(0.94, 0.965),
            )
            figure.text(
                0.08,
                0.02,
                "议题与关切/诉求角色可重叠，数量不可相加为去重总数。",
                color=ChartTheme.MUTED,
                fontsize=8.2,
            )
            figure.subplots_adjust(left=0.20, right=0.95, bottom=0.20, top=0.75)

            output_path = output_directory / self.filename
            figure.savefig(
                output_path,
                dpi=ChartTheme.DPI,
                facecolor=ChartTheme.BACKGROUND,
                bbox_inches="tight",
            )
            figure.clear()

        return output_path
