"""
MD → PDF converter with Korean font support (Malgun Gothic)
Usage: python tools/md_to_pdf.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos
except ImportError:
    print("fpdf2 not found. Run: pip install fpdf2")
    sys.exit(1)

KOREAN_FONT = r"C:\Windows\Fonts\malgun.ttf"
KOREAN_FONT_BOLD = r"C:\Windows\Fonts\malgunbd.ttf"

MARGIN = 18
LINE_HEIGHT = 6
CODE_LINE_HEIGHT = 5

# ── Color palette ──────────────────────────────────────────────────────────────
COLOR_H1 = (15, 23, 42)
COLOR_H2 = (30, 64, 175)
COLOR_H3 = (55, 65, 81)
COLOR_BODY = (30, 30, 30)
COLOR_CODE_BG = (245, 247, 250)
COLOR_CODE_TEXT = (31, 41, 55)
COLOR_TABLE_HEADER = (30, 64, 175)
COLOR_TABLE_HEADER_TEXT = (255, 255, 255)
COLOR_TABLE_ROW_ALT = (241, 245, 249)
COLOR_BORDER = (203, 213, 225)
COLOR_QUOTE_BG = (248, 250, 252)
COLOR_QUOTE_BAR = (99, 102, 241)
COLOR_HR = (203, 213, 225)


class MdToPdf(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("Korean", style="", fname=KOREAN_FONT)
        self.add_font("Korean", style="B", fname=KOREAN_FONT_BOLD)
        self.set_auto_page_break(auto=True, margin=20)
        self.add_page()
        self.set_margins(MARGIN, MARGIN, MARGIN)
        self._in_code_block = False
        self._code_lines: list[str] = []
        self._table_rows: list[list[str]] = []
        self._in_table = False
        self._list_indent = 0

    def _set_body(self, size: int = 10):
        self.set_font("Korean", size=size)
        self.set_text_color(*COLOR_BODY)

    def _render_h1(self, text: str):
        self.ln(4)
        self.set_font("Korean", style="B", size=18)
        self.set_text_color(*COLOR_H1)
        self.multi_cell(0, 10, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # underline
        y = self.get_y()
        self.set_draw_color(*COLOR_H2)
        self.set_line_width(0.8)
        self.line(MARGIN, y, self.w - MARGIN, y)
        self.ln(3)

    def _render_h2(self, text: str):
        self.ln(5)
        self.set_fill_color(*COLOR_H2)
        self.set_text_color(*COLOR_TABLE_HEADER_TEXT)
        self.set_font("Korean", style="B", size=13)
        self.set_x(MARGIN)
        self.cell(0, 8, f"  {text}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def _render_h3(self, text: str):
        self.ln(3)
        self.set_font("Korean", style="B", size=11)
        self.set_text_color(*COLOR_H3)
        self.multi_cell(0, 7, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def _render_h4(self, text: str):
        self.ln(2)
        self.set_font("Korean", style="B", size=10)
        self.set_text_color(*COLOR_H3)
        self.multi_cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def _render_blockquote(self, text: str):
        self.ln(2)
        x0 = MARGIN
        y0 = self.get_y()
        usable_w = self.w - MARGIN * 2
        self.set_fill_color(*COLOR_QUOTE_BG)
        self.set_font("Korean", size=9)
        self.set_text_color(*COLOR_H3)
        self.set_x(x0 + 5)
        clean = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        clean = re.sub(r"`(.*?)`", r"\1", clean)
        self.multi_cell(usable_w - 5, LINE_HEIGHT, clean,
                        fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        y1 = self.get_y()
        self.set_fill_color(*COLOR_QUOTE_BAR)
        self.rect(x0, y0, 2.5, y1 - y0, style="F")
        self.ln(2)

    def _flush_code_block(self):
        if not self._code_lines:
            return
        self.ln(2)
        usable_w = self.w - MARGIN * 2
        line_count = len(self._code_lines)
        block_h = line_count * CODE_LINE_HEIGHT + 6
        if self.get_y() + block_h > self.h - 25:
            self.add_page()
        self.set_fill_color(*COLOR_CODE_BG)
        self.set_draw_color(*COLOR_BORDER)
        self.set_line_width(0.3)
        self.rect(MARGIN, self.get_y(), usable_w, block_h, style="FD")
        self.set_font("Korean", size=7.5)
        self.set_text_color(*COLOR_CODE_TEXT)
        self.set_x(MARGIN)
        for line in self._code_lines:
            if self.get_y() + CODE_LINE_HEIGHT > self.h - 25:
                self.add_page()
                self.set_fill_color(*COLOR_CODE_BG)
            self.set_x(MARGIN + 3)
            display = line[:110] + ("…" if len(line) > 110 else "")
            self.cell(usable_w - 6, CODE_LINE_HEIGHT, display,
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self._code_lines = []
        self.ln(3)

    def _flush_table(self):
        if not self._table_rows:
            return
        self.ln(2)
        usable_w = self.w - MARGIN * 2
        rows = [r for r in self._table_rows if not all(re.match(r"^[-:]+$", c.strip()) for c in r)]
        if not rows:
            self._table_rows = []
            return

        # auto column widths
        col_count = max(len(r) for r in rows)
        col_w = usable_w / col_count
        col_widths = [col_w] * col_count

        for i, row in enumerate(rows):
            is_header = (i == 0)
            self.set_x(MARGIN)
            if is_header:
                self.set_fill_color(*COLOR_TABLE_HEADER)
                self.set_text_color(*COLOR_TABLE_HEADER_TEXT)
                self.set_font("Korean", style="B", size=8.5)
            else:
                if i % 2 == 0:
                    self.set_fill_color(*COLOR_TABLE_ROW_ALT)
                else:
                    self.set_fill_color(255, 255, 255)
                self.set_text_color(*COLOR_BODY)
                self.set_font("Korean", size=8.5)

            self.set_draw_color(*COLOR_BORDER)
            self.set_line_width(0.2)

            row_h = 6.5
            for j, cell in enumerate(row[:col_count]):
                w = col_widths[j]
                txt = cell.strip()
                txt = re.sub(r"\*\*(.*?)\*\*", r"\1", txt)
                txt = re.sub(r"`(.*?)`", r"\1", txt)
                self.cell(w, row_h, txt, border=1, fill=True,
                          new_x=XPos.RIGHT, new_y=YPos.TOP)
            # fill remaining cells if row is shorter
            for _ in range(col_count - len(row)):
                self.cell(col_widths[len(row)], row_h, "", border=1, fill=True,
                          new_x=XPos.RIGHT, new_y=YPos.TOP)
            self.ln(row_h)

        self._table_rows = []
        self.ln(3)

    def _render_body(self, text: str):
        self._set_body(10)
        # strip inline markdown bold/code
        clean = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        clean = re.sub(r"`(.*?)`", r"\1", clean)
        clean = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", clean)  # links
        if clean.strip():
            self.multi_cell(0, LINE_HEIGHT, clean, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def _render_list_item(self, text: str, indent: int = 0):
        self._set_body(9.5)
        clean = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        clean = re.sub(r"`(.*?)`", r"\1", clean)
        clean = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", clean)
        prefix = "  " * indent + "•  "
        usable_w = self.w - MARGIN * 2 - indent * 4
        self.set_x(MARGIN + indent * 4)
        self.multi_cell(usable_w, LINE_HEIGHT, prefix + clean,
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def _render_checkbox(self, text: str, checked: bool):
        self._set_body(9.5)
        clean = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        clean = re.sub(r"`(.*?)`", r"\1", clean)
        mark = "[v]  " if checked else "[ ]  "
        self.set_x(MARGIN + 4)
        self.multi_cell(0, LINE_HEIGHT, mark + clean,
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def _render_hr(self):
        self.ln(3)
        self.set_draw_color(*COLOR_HR)
        self.set_line_width(0.4)
        self.line(MARGIN, self.get_y(), self.w - MARGIN, self.get_y())
        self.ln(4)

    def render_md(self, md_text: str):
        lines = md_text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]

            # code block
            if line.strip().startswith("```"):
                if not self._in_code_block:
                    self._in_code_block = True
                else:
                    self._in_code_block = False
                    self._flush_code_block()
                i += 1
                continue

            if self._in_code_block:
                self._code_lines.append(line)
                i += 1
                continue

            # table row
            if line.startswith("|"):
                if not self._in_table:
                    self._in_table = True
                cells = [c for c in line.split("|") if c != ""]
                self._table_rows.append(cells)
                i += 1
                continue
            else:
                if self._in_table:
                    self._in_table = False
                    self._flush_table()

            # hr
            if re.match(r"^-{3,}$", line.strip()) or re.match(r"^_{3,}$", line.strip()):
                self._render_hr()
                i += 1
                continue

            # headings
            if line.startswith("#### "):
                self._render_h4(line[5:])
            elif line.startswith("### "):
                self._render_h3(line[4:])
            elif line.startswith("## "):
                self._render_h2(line[3:])
            elif line.startswith("# "):
                self._render_h1(line[2:])
            # blockquote
            elif line.startswith("> "):
                self._render_blockquote(line[2:])
            # checkbox list
            elif re.match(r"^- \[[ xX]\]", line):
                checked = line[3] in ("x", "X")
                self._render_checkbox(line[6:], checked)
            # unordered list
            elif re.match(r"^(\s*)[-*] ", line):
                match = re.match(r"^(\s*)[-*] (.*)", line)
                indent = len(match.group(1)) // 2
                self._render_list_item(match.group(2), indent)
            # ordered list
            elif re.match(r"^\d+\. ", line):
                text = re.sub(r"^\d+\. ", "", line)
                self._render_list_item(text)
            # blank line
            elif line.strip() == "":
                if self.get_y() < self.h - 30:
                    self.ln(2)
            else:
                self._render_body(line)

            i += 1

        # flush any remaining
        if self._in_code_block:
            self._flush_code_block()
        if self._in_table:
            self._flush_table()

    def footer(self):
        self.set_y(-13)
        self.set_font("Korean", size=7.5)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f"Imalytix Confidential  |  Page {self.page_no()}", align="C")


def convert(md_path: str, pdf_path: str, title: str):
    text = Path(md_path).read_text(encoding="utf-8")
    pdf = MdToPdf()
    pdf.set_title(title)
    pdf.set_author("Imalytix Team")
    pdf.render_md(text)
    pdf.output(pdf_path)
    print(f"  Generated: {pdf_path}")


if __name__ == "__main__":
    base = Path(__file__).parent.parent

    print("Generating PDFs...")
    convert(
        md_path=str(base / "Imalytix_개발현황_보고서.md"),
        pdf_path=str(base / "Imalytix_개발현황_보고서_KO.pdf"),
        title="Imalytix 개발현황 보고서",
    )
    convert(
        md_path=str(base / "Imalytix_Developer_Guide_EN.md"),
        pdf_path=str(base / "Imalytix_Developer_Guide_EN.pdf"),
        title="Imalytix Developer Guide",
    )
    print("Done.")
