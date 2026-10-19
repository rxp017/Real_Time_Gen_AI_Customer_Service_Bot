"""Export the checked-in engineering report to a paginated PDF."""

import re
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def plain(value: str) -> str:
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", value)
    return value.replace("`", "").replace("**", "")


def export(source: Path = Path("docs/REPORT.md"), destination: Path = Path("docs/REPORT.pdf")) -> None:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("ReportBody", parent=styles["BodyText"], fontSize=9, leading=13, spaceAfter=7))
    styles.add(ParagraphStyle("ReportCell", parent=styles["BodyText"], fontSize=7.8, leading=11))
    styles.add(ParagraphStyle("ReportCode", fontName="Courier", fontSize=7.5, leading=10, spaceAfter=10))
    flow = []
    lines = source.read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("```"):
            code = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                code.extend(textwrap.wrap(lines[index], width=105, replace_whitespace=False, drop_whitespace=False) or [""])
                index += 1
            flow.append(Preformatted("\n".join(code), styles["ReportCode"]))
        elif line.startswith("| "):
            rows = []
            while index < len(lines) and lines[index].startswith("| "):
                row = [v.strip() for v in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", value) for value in row):
                    rows.append([Paragraph(escape(plain(cell)), styles["ReportCell"]) for cell in row])
                index += 1
            width = A4[0] - 88
            columns = [width*.1, width*.45, width*.45] if len(rows[0]) == 3 else [width / len(rows[0])] * len(rows[0])
            table = Table(rows, colWidths=columns, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5eee8")),
                                       ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                       ("LINEBELOW", (0, 0), (-1, -1), 0.35, colors.HexColor("#c5d3cb")),
                                       ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 6)]))
            flow.extend([table, Spacer(1, 10)])
            continue
        elif line.startswith("# "):
            flow.append(Paragraph(escape(plain(line[2:])), styles["Title"]))
        elif line.startswith("## "):
            flow.append(Paragraph(escape(plain(line[3:])), styles["Heading2"]))
        elif line.startswith("### "):
            flow.append(Paragraph(escape(plain(line[4:])), styles["Heading3"]))
        elif line.strip():
            flow.append(Paragraph(escape(plain(line)), styles["ReportBody"]))
        index += 1
    def footer(canvas, document) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#52685b"))
        canvas.drawString(44, 25, "Customer service bot | Engineering report | 2026-10-19")
        canvas.drawRightString(A4[0] - 44, 25, str(document.page))
        canvas.restoreState()
    SimpleDocTemplate(str(destination), pagesize=A4, leftMargin=44, rightMargin=44, topMargin=42, bottomMargin=42,
                      title="Customer service bot engineering report", author="").build(flow, onFirstPage=footer, onLaterPages=footer)
    print(f"Exported {source} -> {destination} ({destination.stat().st_size} bytes)")


if __name__ == "__main__":
    export()
