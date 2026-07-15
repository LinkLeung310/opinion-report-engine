"""Visual constants required by the assignment."""

from __future__ import annotations

from matplotlib.axes import Axes
from matplotlib.figure import Figure


class ChartTheme:
    DPI = 150
    NEGATIVE = "#DC2626"
    NEUTRAL = "#F59E0B"
    POSITIVE = "#10B981"
    ACCENT = "#2563EB"
    BACKGROUND = "#FFFFFF"
    TEXT = "#111827"
    MUTED = "#6B7280"

    @classmethod
    def apply(cls, figure: Figure, axes: Axes) -> None:
        figure.patch.set_facecolor(cls.BACKGROUND)
        axes.set_facecolor(cls.BACKGROUND)
        axes.spines["top"].set_visible(False)
        axes.spines["right"].set_visible(False)
        axes.spines["left"].set_color("#D1D5DB")
        axes.spines["bottom"].set_color("#D1D5DB")
        axes.tick_params(colors=cls.MUTED)
