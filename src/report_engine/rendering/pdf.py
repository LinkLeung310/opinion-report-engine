"""Cross-platform A4 PDF rendering with an embedded CJK font."""

from __future__ import annotations

import re
from html import unescape
from io import BytesIO
from pathlib import Path, PurePosixPath
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from report_engine.assets import report_font_path


IMAGE_PATTERN = re.compile(r"^!\[(?P<alt>.*?)]\((?P<path>.*?)\)$")
FONT_NAME = "NotoSansSC"


class ReportLabPdfRenderer:
    def __init__(self) -> None:
        self._register_font()
        self._styles = self._create_styles()

    def render(self, markdown: str, chart_directory: Path) -> bytes:
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title="舆情分析报告",
            author="Opinion Report Engine",
        )
        story = self._build_story(markdown, chart_directory, document.width)
        document.build(
            story,
            onFirstPage=self._draw_page_frame,
            onLaterPages=self._draw_page_frame,
        )
        return buffer.getvalue()

    @staticmethod
    def _register_font() -> None:
        try:
            pdfmetrics.getFont(FONT_NAME)
        except KeyError:
            pdfmetrics.registerFont(TTFont(FONT_NAME, report_font_path()))

    @staticmethod
    def _create_styles() -> dict[str, ParagraphStyle]:
        return {
            "title": ParagraphStyle(
                "ReportTitle",
                fontName=FONT_NAME,
                fontSize=23,
                leading=32,
                textColor=colors.HexColor("#111827"),
                alignment=TA_CENTER,
                spaceAfter=7 * mm,
                wordWrap="CJK",
            ),
            "scope": ParagraphStyle(
                "ReportScope",
                fontName=FONT_NAME,
                fontSize=9.5,
                leading=16,
                textColor=colors.HexColor("#4B5563"),
                backColor=colors.HexColor("#F3F4F6"),
                borderColor=colors.HexColor("#E5E7EB"),
                borderWidth=0.5,
                borderPadding=9,
                spaceAfter=8 * mm,
                wordWrap="CJK",
            ),
            "section": ParagraphStyle(
                "SectionHeading",
                fontName=FONT_NAME,
                fontSize=16,
                leading=23,
                textColor=colors.HexColor("#111827"),
                spaceBefore=5 * mm,
                spaceAfter=3 * mm,
                keepWithNext=True,
                wordWrap="CJK",
            ),
            "subsection": ParagraphStyle(
                "SubsectionHeading",
                fontName=FONT_NAME,
                fontSize=12,
                leading=18,
                textColor=colors.HexColor("#1F2937"),
                spaceBefore=3 * mm,
                spaceAfter=1.5 * mm,
                keepWithNext=True,
                wordWrap="CJK",
            ),
            "body": ParagraphStyle(
                "Body",
                fontName=FONT_NAME,
                fontSize=10.5,
                leading=18,
                textColor=colors.HexColor("#374151"),
                alignment=TA_LEFT,
                spaceAfter=3 * mm,
                wordWrap="CJK",
            ),
            "method": ParagraphStyle(
                "Method",
                fontName=FONT_NAME,
                fontSize=8.5,
                leading=14,
                textColor=colors.HexColor("#6B7280"),
                spaceBefore=7 * mm,
                borderColor=colors.HexColor("#E5E7EB"),
                borderWidth=0.5,
                borderPadding=7,
                wordWrap="CJK",
            ),
            "caption": ParagraphStyle(
                "ChartCaption",
                fontName=FONT_NAME,
                fontSize=8.5,
                leading=12,
                textColor=colors.HexColor("#6B7280"),
                alignment=TA_CENTER,
                spaceAfter=4 * mm,
                wordWrap="CJK",
            ),
        }

    def _build_story(
        self,
        markdown: str,
        chart_directory: Path,
        content_width: float,
    ) -> list:
        story: list = []
        paragraph_lines: list[str] = []

        def flush_paragraph() -> None:
            if paragraph_lines:
                text = "<br/>".join(escape(line) for line in paragraph_lines)
                story.append(Paragraph(text, self._styles["body"]))
                paragraph_lines.clear()

        for raw_line in markdown.splitlines():
            line = raw_line.strip()
            if not line:
                flush_paragraph()
                continue
            if line.startswith("# "):
                flush_paragraph()
                story.append(Paragraph(escape(line[2:]), self._styles["title"]))
                continue
            if line.startswith("## "):
                flush_paragraph()
                story.append(Paragraph(escape(line[3:]), self._styles["section"]))
                continue
            if line.startswith("### "):
                flush_paragraph()
                story.append(
                    Paragraph(escape(line[4:]), self._styles["subsection"])
                )
                continue
            if line.startswith("> "):
                flush_paragraph()
                story.append(
                    Paragraph(
                        escape(unescape(line[2:])),
                        self._styles["scope"],
                    )
                )
                continue

            image_match = IMAGE_PATTERN.match(line)
            if image_match:
                flush_paragraph()
                image_path = self._resolve_chart(
                    image_match.group("path"),
                    chart_directory,
                )
                image = Image(image_path)
                scale = min(
                    content_width / image.imageWidth,
                    (100 * mm) / image.imageHeight,
                    1,
                )
                image.drawWidth = image.imageWidth * scale
                image.drawHeight = image.imageHeight * scale
                image.hAlign = "CENTER"
                story.extend(
                    [
                        Spacer(1, 2 * mm),
                        image,
                        Paragraph(
                            escape(image_match.group("alt")),
                            self._styles["caption"],
                        ),
                    ]
                )
                continue

            if line.startswith("_") and line.endswith("_"):
                flush_paragraph()
                story.append(Paragraph(escape(line[1:-1]), self._styles["method"]))
                continue
            paragraph_lines.append(line)

        flush_paragraph()
        return story

    @staticmethod
    def _resolve_chart(markdown_path: str, chart_directory: Path) -> Path:
        relative = PurePosixPath(markdown_path)
        if len(relative.parts) != 2 or relative.parts[0] != "charts":
            raise ValueError("PDF chart references must use charts/<filename>")
        chart_name = relative.parts[1]
        if chart_name in {"", ".", ".."}:
            raise ValueError("invalid PDF chart filename")
        chart_path = chart_directory / chart_name
        if not chart_path.is_file():
            raise FileNotFoundError(f"PDF chart is missing: {chart_name}")
        return chart_path

    @staticmethod
    def _draw_page_frame(canvas, document) -> None:
        canvas.saveState()
        width, height = A4
        canvas.setStrokeColor(colors.HexColor("#DC2626"))
        canvas.setLineWidth(1.5)
        canvas.line(18 * mm, height - 11 * mm, width - 18 * mm, height - 11 * mm)
        canvas.setFont(FONT_NAME, 7.5)
        canvas.setFillColor(colors.HexColor("#9CA3AF"))
        canvas.drawString(18 * mm, 9 * mm, "Opinion Report Engine")
        canvas.drawRightString(width - 18 * mm, 9 * mm, f"{document.page}")
        canvas.restoreState()
