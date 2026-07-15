"""Paths to redistributable assets bundled with the Python package."""

from pathlib import Path


def report_font_path() -> Path:
    path = Path(__file__).parent / "fonts" / "NotoSansSC-Regular.ttf"
    if not path.is_file():
        raise FileNotFoundError("bundled Noto Sans SC font is missing")
    return path


__all__ = ["report_font_path"]
