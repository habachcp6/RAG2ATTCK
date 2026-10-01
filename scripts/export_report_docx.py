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


def extract_braced(text: str, start_idx: int) -> tuple[str, int]:
    """Extract content inside balanced { ... } starting at text[start_idx] == '{'."""
    if start_idx >= len(text) or text[start_idx] != "{":
        return "", start_idx
    depth = 0
    content = []
    i = start_idx
    while i < len(text):
        c = text[i]
        if c == "{":
            depth += 1
            if depth > 1:
                content.append(c)
        elif c == "}":
            depth -= 1
            if depth == 0:
                return "".join(content), i + 1
            else:
                content.append(c)
        else:
            content.append(c)
        i += 1
    return "".join(content), len(text)


def replace_fractions(text: str) -> str:
    """Replace \\frac{num}{den} with (num) / (den) handling nested braces safely."""
    while "\\frac{" in text:
        idx = text.find("\\frac{")
        num_start = idx + len("\\frac")
        num, num_end = extract_braced(text, num_start)
        while num_end < len(text) and text[num_end].isspace():
            num_end += 1
        if num_end < len(text) and text[num_end] == "{":
            den, den_end = extract_braced(text, num_end)
            text = text[:idx] + f"({num}) / ({den})" + text[den_end:]
        else:
            text = text[:idx] + num + text[num_end:]
    return text


def latex_to_unicode(text: str) -> str:
    """Convert LaTeX mathematical notation to clean, structured Unicode math text."""
    s = text.strip()

    # Replace escaped currency amounts like \$19.99
    s = re.sub(r"\\\$([0-9.]+)", r"$\1", s)

    # Strip $$ delimiters if present
    if s.startswith("$$") and s.endswith("$$"):
        s = s[2:-2].strip()

    # Replace fractions with balanced braces first
    s = replace_fractions(s)

    # Strip text/formatting wrappers
    for tag in (r"\\text", r"\\mathrm", r"\\mathbf", r"\\mathit"):
        while re.search(tag + r"\{", s):
            m = re.search(tag + r"\{", s)
            start = m.start()
            content, end = extract_braced(s, m.end() - 1)
            s = s[:start] + content + s[end:]

    # Blackboard bold / Calligraphic
    s = re.sub(r"\\mathbb\{I\}", "I", s)
    s = re.sub(r"\\mathcal\{C\}", "C", s)

    # Greek, set, logic, and relational symbols
    replacements = [
        (r"\\Delta", "Δ"),
        (r"\\to", "→"),
        (r"\\in", "∈"),
        (r"\\notin", "∉"),
        (r"\\subseteq", "⊆"),
        (r"\\cap", "∩"),
        (r"\\cup", "∪"),
        (r"\\emptyset", "∅"),
        (r"\\neq", "≠"),
        (r"\\le(?![a-zA-Z])", "≤"),
        (r"\\ge(?![a-zA-Z])", "≥"),
        (r"\\approx", "≈"),
        (r"\\sim", "~"),
        (r"\\times", "×"),
        (r"\\cdot", "·"),
        (r"\\forall", "∀"),
        (r"\\equiv", "≡"),
        (r"\\land", "∧"),
        (r"\\lor", "∨"),
        (r"\\quad", "  "),
        (r"\\qquad", "    "),
        (r"\\langle", "⟨"),
        (r"\\rangle", "⟩"),
        (r"\\cos", "cos"),
        (r"\\\|", "||"),
        (r"\\\{", "{"),
        (r"\\\}", "}"),
        (r"\\hat\{y\}_i", "ŷ_i"),
        (r"\\hat\{y\}", "ŷ"),
        (r"\\hat\{q\}", "q̂"),
        (r"\\hat\{d\}_i", "d̂_i"),
        (r"\\hat\{d\}", "d̂"),
        (r"\\left\(", "("),
        (r"\\right\)", ")"),
        (r"\\left\{", "{"),
        (r"\\right\}", "}"),
        (r"\\left\[", "["),
        (r"\\right\]", "]"),
        (r"\\_", "_"),
    ]
    for pattern, rep in replacements:
        s = re.sub(pattern, rep, s)

    # Summations
    s = re.sub(r"\\sum_\{([^}]+)\}\^\{([^}]+)\}", r"∑_{(\1)}^\2", s)
    s = re.sub(r"\\sum_\{([^}]+)\}", r"∑_{(\1)}", s)
    s = re.sub(r"\\sum", "∑", s)

    # Cases environment
    s = re.sub(r"\\begin\{cases\}", "", s)
    s = re.sub(r"\\end\{cases\}", "", s)
    s = re.sub(r"\\\\", "; ", s)
    s = re.sub(r"\\&", " ", s)
    s = re.sub(r"&", " ", s)

    # Subscripts and superscripts cleanup
    s = re.sub(r"_\{([^}]+)\}", r"_\1", s)
    s = re.sub(r"\^\{([^}]+)\}", r"^\1", s)

    # Strip any remaining backslash command tokens
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def set_cell_margins(cell, top=80, bottom=80, left=100, right=100):
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


def apply_table_pagination_rules(table):
    """Ensure repeat header on page break (<w:tblHeader/>) and prevent row splitting (<w:cantSplit/>)."""
    for r_idx, row in enumerate(table.rows):
        trPr = row._tr.get_or_add_trPr()
        cantSplit = parse_xml(f'<w:cantSplit {nsdecls("w")}/>')
        trPr.append(cantSplit)
        if r_idx == 0:
            tblHeader = parse_xml(f'<w:tblHeader {nsdecls("w")}/>')
            trPr.append(tblHeader)


def assign_table_column_widths(table, num_cols: int, header_texts: list[str]) -> list[float]:
    """Assign explicit column widths ensuring total table width <= 6.50 inches."""
    table.autofit = False
    MAX_WIDTH = 6.50
    hdr_joined = " ".join(header_texts).lower()

    if num_cols == 10:
        # Table 1: Multi-dimensional comparator matrix
        widths = [1.10] + [0.60] * 9
    elif num_cols == 9:
        # Table 5: Resource Consumption
        widths = [0.90] + [0.70] * 8
    elif num_cols == 8:
        # Table 4: Failure Decomposition
        widths = [0.90, 0.80, 0.90, 0.95, 0.95, 0.70, 0.65, 0.65]
    elif num_cols == 6:
        if "retrieval depth" in hdr_joined:
            # Table 2a: Attribution Performance
            widths = [1.10, 1.00, 0.90, 1.10, 1.10, 1.30]
        elif "single-event" in hdr_joined:
            # Table 3: Representation Stratification
            widths = [1.00, 1.15, 1.25, 1.05, 1.05, 1.00]
        else:
            # Table 2b: Attribution Diagnostics
            widths = [1.10, 0.90, 1.15, 1.15, 1.10, 1.10]
    elif num_cols == 4:
        # Table 6: Cryptographic Reproducibility Manifest
        widths = [1.60, 1.80, 0.90, 2.20]
    elif num_cols == 3:
        widths = [1.80, 2.70, 2.00]
    else:
        w_each = round(MAX_WIDTH / num_cols, 2)
        widths = [w_each] * num_cols
        diff = sum(widths) - MAX_WIDTH
        if diff != 0:
            widths[-1] -= diff

    for col_idx, w in enumerate(widths):
        table.columns[col_idx].width = Inches(w)
    for row in table.rows:
        for col_idx, w in enumerate(widths):
            row.cells[col_idx].width = Inches(w)

    return widths


def format_inline_runs(
    paragraph,
    text: str,
    font_size: Pt | None = None,
    default_bold: bool = False,
    default_italic: bool = False,
    default_color: RGBColor | None = None,
):
    """Parse inline markdown (bold, italic, code, math, links, currency) and append runs to paragraph."""
    token_pattern = re.compile(
        r"(\\\*|\\\$[0-9.]+|\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|\$[^$]+\$)"
    )
    parts = token_pattern.split(text)

    for part in parts:
        if not part:
            continue
        if part == r"\*":
            run = paragraph.add_run("*")
            if font_size:
                run.font.size = font_size
            if default_bold:
                run.bold = True
            if default_italic:
                run.italic = True
            if default_color:
                run.font.color.rgb = default_color
        elif re.match(r"^\\\$[0-9.]+$", part):
            run = paragraph.add_run(part[1:])
            if font_size:
                run.font.size = font_size
            if default_bold:
                run.bold = True
            if default_italic:
                run.italic = True
            if default_color:
                run.font.color.rgb = default_color
        elif part.startswith("***") and part.endswith("***"):
            format_inline_runs(
                paragraph,
                part[3:-3],
                font_size=font_size,
                default_bold=True,
                default_italic=True,
                default_color=default_color,
            )
        elif part.startswith("**") and part.endswith("**"):
            format_inline_runs(
                paragraph,
                part[2:-2],
                font_size=font_size,
                default_bold=True,
                default_italic=default_italic,
                default_color=default_color,
            )
        elif part.startswith("*") and part.endswith("*"):
            format_inline_runs(
                paragraph,
                part[1:-1],
                font_size=font_size,
                default_bold=default_bold,
                default_italic=True,
                default_color=default_color,
            )
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            code_size = Pt(font_size.pt * 0.9) if font_size else Pt(9.5)
            run.font.size = code_size
            run.font.color.rgb = RGBColor(0x8A, 0x1F, 0x11)
        elif part.startswith("[") and "]" in part and part.endswith(")"):
            m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", part)
            if m:
                link_text, link_url = m.groups()
                run = paragraph.add_run(link_text)
                run.font.color.rgb = RGBColor(0x09, 0x69, 0xDA)
                run.underline = True
                if font_size:
                    run.font.size = font_size
                if default_bold:
                    run.bold = True
                if default_italic:
                    run.italic = True
            else:
                run = paragraph.add_run(part)
                if font_size:
                    run.font.size = font_size
                if default_bold:
                    run.bold = True
                if default_italic:
                    run.italic = True
        elif part.startswith("$") and part.endswith("$"):
            math_content = part[1:-1]
            converted = latex_to_unicode(math_content)
            run = paragraph.add_run(converted)
            run.font.name = "Cambria Math"
            run.italic = True
            if font_size:
                run.font.size = font_size
            if default_bold:
                run.bold = True
            if default_color:
                run.font.color.rgb = default_color
        else:
            run = paragraph.add_run(part)
            if font_size:
                run.font.size = font_size
            if default_bold:
                run.bold = True
            if default_italic:
                run.italic = True
            if default_color:
                run.font.color.rgb = default_color


def add_display_math(doc, math_text: str):
    """Render display math block as an indented, styled formula paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.4)
    p.paragraph_format.right_indent = Inches(0.4)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15

    converted = latex_to_unicode(math_text)
    run = p.add_run(converted)
    run.font.name = "Cambria Math"
    run.font.size = Pt(10.5)
    run.italic = True
    run.font.color.rgb = RGBColor(0x0A, 0x25, 0x40)

    pPr = p._element.get_or_add_pPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8FAFC"/>')
    pPr.append(shd)
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}><w:left w:val="single" w:sz="18" w:space="8" w:color="0969DA"/></w:pBdr>'
    )
    pPr.append(pBdr)


def build_docx_from_markdown(md_path: Path, output_docx_path: Path):
    """Convert scientific_report.md into a high-quality Word document."""
    doc = docx.Document()

    # Configure page margins (1.0 inch all around)
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
        table.autofit = False

        # Select font size and margins based on column count
        if num_cols >= 9:
            cell_font_size = Pt(7.5)
            pad_top, pad_bot, pad_left, pad_right = 60, 60, 60, 60
        elif num_cols >= 7:
            cell_font_size = Pt(8.0)
            pad_top, pad_bot, pad_left, pad_right = 70, 70, 70, 70
        elif num_cols == 6:
            cell_font_size = Pt(8.5)
            pad_top, pad_bot, pad_left, pad_right = 80, 80, 80, 80
        else:
            cell_font_size = Pt(9.0)
            pad_top, pad_bot, pad_left, pad_right = 100, 100, 100, 100

        for r_idx, row_data in enumerate(raw_rows):
            is_header = r_idx == 0
            for c_idx in range(num_cols):
                cell_text = row_data[c_idx] if c_idx < len(row_data) else ""
                cell = table.cell(r_idx, c_idx)
                p = cell.paragraphs[0]
                p.text = ""
                p.paragraph_format.space_after = Pt(1)
                p.paragraph_format.line_spacing = 1.05

                if is_header:
                    set_cell_background(cell, "092C4C")  # Dark Navy Header
                    format_inline_runs(
                        p,
                        cell_text,
                        font_size=cell_font_size,
                        default_bold=True,
                        default_color=RGBColor(0xFF, 0xFF, 0xFF),
                    )
                else:
                    if r_idx % 2 == 1:
                        set_cell_background(cell, "F8FAFC")  # Subtle alternating light row
                    else:
                        set_cell_background(cell, "FFFFFF")
                    format_inline_runs(
                        p,
                        cell_text,
                        font_size=cell_font_size,
                        default_bold=False,
                        default_color=RGBColor(0x24, 0x29, 0x2F),
                    )

                set_cell_margins(cell, top=pad_top, bottom=pad_bot, left=pad_left, right=pad_right)
                set_cell_border(
                    cell,
                    top={"sz": 4, "val": "single", "color": "D0D7DE"},
                    bottom={"sz": 4, "val": "single", "color": "D0D7DE"},
                    left={"sz": 2, "val": "single", "color": "E1E4E8"},
                    right={"sz": 2, "val": "single", "color": "E1E4E8"},
                )

        # Apply OpenXML pagination rules (<w:tblHeader/>, <w:cantSplit/>)
        apply_table_pagination_rules(table)
        # Apply explicit column widths
        header_texts = raw_rows[0] if raw_rows else []
        assign_table_column_widths(table, num_cols, header_texts)

        # Spacing after table
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

        # Handle display math $$ ... $$
        if line.strip().startswith("$$"):
            if in_table:
                flush_table()
            if in_code_block:
                flush_code()

            stripped = line.strip()
            if stripped.endswith("$$") and len(stripped) > 4:
                math_content = stripped[2:-2].strip()
                add_display_math(doc, math_content)
                i += 1
                continue
            else:
                math_lines = []
                if len(stripped) > 2:
                    math_lines.append(stripped[2:].strip())
                i += 1
                while i < len(lines) and not lines[i].strip().endswith("$$"):
                    math_lines.append(lines[i].strip())
                    i += 1
                if i < len(lines):
                    closing_line = lines[i].strip()
                    if len(closing_line) > 2:
                        math_lines.append(closing_line[:-2].strip())
                    i += 1
                add_display_math(doc, " ".join(math_lines))
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
            run.font.color.rgb = RGBColor(0x33, 0x33, 0x44)
        elif line.strip() == "---":
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            pPr = p._element.get_or_add_pPr()
            pBdr = parse_xml(
                f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="1" w:color="D0D7DE"/></w:pBdr>'
            )
            pPr.append(pBdr)
        elif line.startswith("> "):
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


def audit_docx_quality(doc_path: Path):
    """Rigorous QA audit verifying rendering invariants on generated DOCX."""
    doc = docx.Document(str(doc_path))

    # Regex to detect raw LaTeX tokens or unparsed $$ blocks
    tex_pattern = re.compile(r"\\[a-zA-Z]+|\$\$")
    errors = []

    # 1. Audit all paragraphs for raw TeX leakage
    for p_idx, p in enumerate(doc.paragraphs):
        text = p.text
        # Skip paragraphs inside code blocks (identified by Consolas font)
        is_code = any(r.font.name == "Consolas" for r in p.runs)
        if not is_code:
            matches = tex_pattern.findall(text)
            if matches:
                errors.append(f"Paragraph {p_idx} has raw TeX tokens {matches}: '{text[:120]}...'")

    # 2. Audit all table cells for raw TeX leakage, pagination rules, and width constraints
    for t_idx, table in enumerate(doc.tables):
        # Header check
        row0_xml = table.rows[0]._tr.xml
        if "<w:tblHeader" not in row0_xml:
            errors.append(f"Table {t_idx} row 0 is missing <w:tblHeader/>")

        # CantSplit check on every row
        for r_idx, row in enumerate(table.rows):
            row_xml = row._tr.xml
            if "<w:cantSplit" not in row_xml:
                errors.append(f"Table {t_idx} row {r_idx} is missing <w:cantSplit/>")

        # Cell content check
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                cell_text = cell.text
                matches = tex_pattern.findall(cell_text)
                if matches:
                    errors.append(
                        f"Table {t_idx} row {r_idx} col {c_idx} has raw TeX {matches}: '{cell_text[:80]}'"
                    )

        # Width check (sum of column widths)
        col_widths_sum = sum(col.width.inches for col in table.columns if col.width)
        if col_widths_sum > 6.55:
            errors.append(f"Table {t_idx} width {col_widths_sum:.2f}in exceeds printable limit of 6.50in")

    if errors:
        error_msg = f"DOCX QA Audit FAILED with {len(errors)} error(s):\n" + "\n".join(errors)
        raise AssertionError(error_msg)

    print(
        f"DOCX QA Audit PASSED: 0 raw TeX tokens across {len(doc.paragraphs)} paragraphs and "
        f"{len(doc.tables)} tables ({sum(len(t.rows) for t in doc.tables)} rows). "
        f"All tables have cantSplit on all rows, tblHeader on row 0, and width <= 6.50 inches."
    )


if __name__ == "__main__":
    src_md = Path("docs/report/scientific_report.md")
    dest_docx = Path("docs/report/scientific_report.docx")
    build_docx_from_markdown(src_md, dest_docx)
    audit_docx_quality(dest_docx)
