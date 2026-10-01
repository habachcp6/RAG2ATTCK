"""Export Markdown scientific report to formatted DOCX."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner padding for table cells (in twips: 1/20 of a pt)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_background(cell, fill_hex="F0F4F8"):
    """Set background shading for a table cell."""
    shading_xml = f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))


def set_cell_border(cell, **kwargs):
    """Set individual cell borders."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f"w:{edge}"
            element = parse_xml(
                f'<{tag} {nsdecls("w")} w:val="{edge_data.get("val", "single")}" '
                f'w:sz="{edge_data.get("sz", 4)}" w:space="0" '
                f'w:color="{edge_data.get("color", "CCCCCC")}"/>'
            )
            tcBorders.append(element)
    tcPr.append(tcBorders)


def format_inline_runs(paragraph, text: str):
    """Parse basic inline markdown (bold, italic, code) and append runs to paragraph."""
    # Pattern to match bold-italic, bold, italic, code
    token_pattern = re.compile(
        r"(\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))"
    )
    parts = token_pattern.split(text)

    for part in parts:
        if not part:
            continue
        if part.startswith("***") and part.endswith("***"):
            run = paragraph.add_run(part[3:-3])
            run.bold = True
            run.italic = True
        elif part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("*") and part.endswith("*"):
            run = paragraph.add_run(part[1:-1])
            run.italic = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(0x8A, 0x1F, 0x11)
        elif part.startswith("[") and "]" in part and part.endswith(")"):
            m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", part)
            if m:
                link_text, link_url = m.groups()
                run = paragraph.add_run(link_text)
                run.font.color.rgb = RGBColor(0x09, 0x69, 0xDA)
                run.underline = True
            else:
                paragraph.add_run(part)
        else:
            paragraph.add_run(part)


def build_docx_from_markdown(md_path: Path, output_docx_path: Path):
    """Convert scientific_report.md into a publication-grade Word document."""
    doc = docx.Document()

    # Configure page margins (1 inch all around)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Base Normal style
    style_normal = doc.styles["Normal"]
    style_normal.font.name = "Calibri"
    style_normal.font.size = Pt(11)
    style_normal.font.color.rgb = RGBColor(0x24, 0x29, 0x2F)
    style_normal.paragraph_format.line_spacing = 1.15
    style_normal.paragraph_format.space_after = Pt(4)

    lines = md_path.read_text(encoding="utf-8").splitlines()
    in_code_block = False
    code_lines = []
    in_table = False
    table_lines = []

    def flush_table():
        nonlocal in_table, table_lines
        if not table_lines:
            in_table = False
            return

        # Parse rows
        raw_rows = []
        for tline in table_lines:
            cells = [c.strip() for c in tline.split("|")]
            if len(cells) >= 3 and cells[0] == "" and cells[-1] == "":
                cells = cells[1:-1]
            # Ignore separator row |---|---|
            if cells and all(re.match(r"^:?-+:?$", c) for c in cells if c):
                continue
            raw_rows.append(cells)

        if not raw_rows:
            table_lines = []
            in_table = False
            return

        num_cols = max(len(r) for r in raw_rows)
        table = doc.add_table(rows=len(raw_rows), cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = True

        for r_idx, row_data in enumerate(raw_rows):
            is_header = r_idx == 0
            for c_idx in range(num_cols):
                cell_text = row_data[c_idx] if c_idx < len(row_data) else ""
                cell = table.cell(r_idx, c_idx)
                cell.paragraphs[0].text = ""  # clear default empty paragraph
                p = cell.paragraphs[0]
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.line_spacing = 1.05
                format_inline_runs(p, cell_text)

                if is_header:
                    set_cell_background(cell, "092C4C")  # Dark Navy Header
                    for r in p.runs:
                        r.font.bold = True
                        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                else:
                    if r_idx % 2 == 1:
                        set_cell_background(cell, "F8FAFC")  # Subtle alternating light row
                    else:
                        set_cell_background(cell, "FFFFFF")

                set_cell_margins(cell, top=120, bottom=120, left=160, right=160)
                set_cell_border(
                    cell,
                    top={"sz": 4, "val": "single", "color": "D0D7DE"},
                    bottom={"sz": 4, "val": "single", "color": "D0D7DE"},
                    left={"sz": 2, "val": "single", "color": "E1E4E8"},
                    right={"sz": 2, "val": "single", "color": "E1E4E8"},
                )

        # Add small spacing after table
        post_p = doc.add_paragraph()
        post_p.paragraph_format.space_after = Pt(6)
        table_lines = []
        in_table = False

    def flush_code():
        nonlocal in_code_block, code_lines
        if not code_lines:
            in_code_block = False
            return
        code_text = "\n".join(code_lines)
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.right_indent = Inches(0.25)
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.0

        run = p.add_run(code_text)
        run.font.name = "Consolas"
        run.font.size = Pt(9.0)
        run.font.color.rgb = RGBColor(0x1F, 0x23, 0x28)

        # Style background
        pPr = p._element.get_or_add_pPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F6F8FA"/>')
        pPr.append(shd)

        code_lines = []
        in_code_block = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Handle fenced code block
        if line.strip().startswith("```"):
            if in_code_block:
                flush_code()
            else:
                if in_table:
                    flush_table()
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Handle Markdown table lines
        if line.strip().startswith("|") and line.strip().endswith("|"):
            in_table = True
            table_lines.append(line)
            i += 1
            continue
        elif in_table:
            flush_table()

        # Handle Headings
        if line.startswith("# "):
            h = doc.add_heading(level=0)
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after = Pt(8)
            run = h.add_run(line[2:].strip())
            run.font.name = "Georgia"
            run.font.size = Pt(20)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0x0A, 0x25, 0x40)
        elif line.startswith("## "):
            h = doc.add_heading(level=1)
            h.paragraph_format.space_before = Pt(14)
            h.paragraph_format.space_after = Pt(6)
            run = h.add_run(line[3:].strip())
            run.font.name = "Georgia"
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0x0A, 0x25, 0x40)
        elif line.startswith("### "):
            h = doc.add_heading(level=2)
            h.paragraph_format.space_before = Pt(10)
            h.paragraph_format.space_after = Pt(4)
            run = h.add_run(line[4:].strip())
            run.font.name = "Calibri"
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0x1F, 0x23, 0x28)
        elif line.startswith("#### "):
            h = doc.add_heading(level=3)
            h.paragraph_format.space_before = Pt(8)
            h.paragraph_format.space_after = Pt(2)
            run = h.add_run(line[5:].strip())
            run.font.name = "Calibri"
            run.font.size = Pt(11)
            run.font.bold = True
            run.font.italic = True
            run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
        elif line.strip() == "---":
            # Horizontal rule
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            pPr = p._element.get_or_add_pPr()
            pBdr = parse_xml(
                f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="1" w:color="D0D7DE"/></w:pBdr>'
            )
            pPr.append(pBdr)
        elif line.startswith("> "):
            # Blockquote
            quote_text = line[2:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.right_indent = Inches(0.2)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(6)
            format_inline_runs(p, quote_text)
            pPr = p._element.get_or_add_pPr()
            pBdr = parse_xml(
                f'<w:pBdr {nsdecls("w")}><w:left w:val="single" w:sz="24" w:space="8" w:color="0969DA"/></w:pBdr>'
            )
            pPr.append(pBdr)
            shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F6F8FA"/>')
            pPr.append(shd)
        elif line.strip().startswith("- ") or line.strip().startswith("* "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            content = line.strip()[2:]
            format_inline_runs(p, content)
        elif re.match(r"^\d+\.\s+", line.strip()):
            p = doc.add_paragraph(style="List Number")
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            content = re.sub(r"^\d+\.\s+", "", line.strip())
            format_inline_runs(p, content)
        elif line.strip():
            # Regular paragraph
            p = doc.add_paragraph()
            format_inline_runs(p, line.strip())

        i += 1

    if in_table:
        flush_table()
    if in_code_block:
        flush_code()

    output_docx_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_docx_path))
    print(f"Successfully generated DOCX at {output_docx_path}")


if __name__ == "__main__":
    src_md = Path("docs/report/scientific_report.md")
    dest_docx = Path("docs/report/scientific_report.docx")
    build_docx_from_markdown(src_md, dest_docx)
