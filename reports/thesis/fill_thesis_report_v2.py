"""Populate HOD402_CP_StudentsGuideForm_RAG2ATTCK_HoanChinh.docx with the complete, post-review-verified RAG2ATT&CK study.

Addresses every item from the independent review:
- 1.1 Complete RQ1 reporting (both Accuracy and 474-class Macro-F1 bootstrap CIs across k=1,3,5,10)
- 1.2 Strict separation of TEST (N=718 views / 278 pairs) and exploratory T20 TEST+DEV (N=756 views / 296 pairs)
- 1.3 Accurate model provenance (fixed model alias gpt-5.6-luna & inference settings, timestamped response IDs, model_version=null, system_fingerprints=[])
- 1.4 Explicit separation of Hit@k (ANY_GT_RETRIEVED) and Multi-Label Macro Recall@k
- 1.5 Observational/associational framing replacing overclaimed causal language
- 1.6 Full Table 9 financial reconciliation (token-usage estimated cost vs. conservative ledger spend for rag_k1) and separation of 7.58x token vs. 4.60x cost scaling
- 1.7 Table 13 Roadmap distinguishing Planned Schedule Window from Actual Completion Date & Audit Evidence
- 2.1 Universal inline math rendering (native Word runs with Cambria Math, Unicode operators, and <w:vertAlign> sub/superscripts) + OMML display equations
- 2.2 Complete piecewise count definition of F1_c covering TP_c=0, FP_c>0, FN_c>0 and F1_c^* aggregation
- 2.3 Consistent multi-label set intersection notation (Y_i ∩ R_{i,k} ≠ ∅ and Y_i ∩ R_{i,k} = ∅)
- 2.4 Cluster-bootstrap CI (440 clusters) as primary inferential basis vs. unclustered McNemar (N=718)
- 2.5 Support-based upper bound (8/474 ≈ 1.69%)
- 3.x Literature review precision (LADE, CAM-LDS, Okuma), exact INFERENCE_ALLOWLIST field census (TargetUserName, SubjectUserName, SubjectLogonId), and clean IEEE References
- 4.x & 5.x Fixed headings, Student's ID, sequential Table 1..14 numbering, 360 DPI zero-baseline/interval figures, verbatim worked example (view_0265275a), and zero blank pages.
"""

from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path

import docx
import win32com.client
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CODEX_REPO = Path(r"C:\Users\hahoa\.codex\artifacts\rag2attck\finalization_repo_20261003")
sys.path.insert(0, str(CODEX_REPO))
from scripts.latex_to_omml import LatexToOmml  # noqa: E402
from scripts.export_report_docx import (  # noqa: E402
    apply_table_pagination_rules,
    assign_table_column_widths,
    latex_to_unicode,
    set_cell_background,
    set_cell_border,
    set_cell_margins,
)

BACKUP_PATH = Path(r"C:\Users\hahoa\.gemini\antigravity\brain\7d8e4a5e-ef6e-4dc8-8362-f75b18a5391d\scratch\IAP491_ORIGINAL_BACKUP.docx")
SCRATCH_DIR = Path(r"C:\Users\hahoa\.gemini\antigravity\brain\8a3ff726-a1a3-499b-a40d-9a2226b3a57c\scratch")
FIGURES_DIR = SCRATCH_DIR / "figures_hires"
OUTPUT_DOCX = Path(r"C:\Users\hahoa\Downloads\HOD402_CP_StudentsGuideForm_RAG2ATTCK_HoanChinh.docx")
OUTPUT_PDF = Path(r"C:\Users\hahoa\Downloads\HOD402_CP_StudentsGuideForm_RAG2ATTCK_HoanChinh.pdf")

FONT_FAMILY = "Times New Roman"
BODY_FONT_SIZE = Pt(12)
MATH_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"


def normalize_omml_element(elem, color_hex: str, sz_val: str, default_bold: bool = False):
    """Ensure <m:nary> has non-empty <m:e> containing its summand, and <w:rPr> follows <m:rPr> in every <m:r>."""
    for nary in elem.iter(f"{MATH_NS}nary"):
        e_node = nary.find(f"{MATH_NS}e")
        if e_node is not None and len(e_node) == 0:
            sib = nary.getnext()
            while sib is not None:
                sib_text = "".join(sib.itertext()).strip()
                if sib_text in (",", ";", "="):
                    break
                next_sib = sib.getnext()
                e_node.append(sib)
                sib = next_sib

    for r_node in elem.iter(f"{MATH_NS}r"):
        rPr_parts = [
            '<w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math" w:cs="Cambria Math"/>',
            f'<w:color w:val="{color_hex}"/>',
            f'<w:sz w:val="{sz_val}"/>',
        ]
        if default_bold:
            rPr_parts.append("<w:b/>")
        wrPr = parse_xml(f'<w:rPr {nsdecls("w")}>{"".join(rPr_parts)}</w:rPr>')
        m_rPr = r_node.find(f"{MATH_NS}rPr")
        insert_idx = list(r_node).index(m_rPr) + 1 if m_rPr is not None else 0
        r_node.insert(insert_idx, wrPr)


def attach_bookmark(p_elem, bm_name: str, bm_id: int):
    """Attach a Word bookmark (<w:bookmarkStart/> ... <w:bookmarkEnd/>) around paragraph content."""
    bm_start = parse_xml(f'<w:bookmarkStart {nsdecls("w")} w:id="{bm_id}" w:name="{bm_name}"/>')
    bm_end = parse_xml(f'<w:bookmarkEnd {nsdecls("w")} w:id="{bm_id}"/>')
    pPr = p_elem.find(qn("w:pPr"))
    insert_idx = list(p_elem).index(pPr) + 1 if pPr is not None else 0
    p_elem.insert(insert_idx, bm_start)
    p_elem.append(bm_end)


def parse_inline_math_segments(latex: str) -> list[tuple[str, str]]:
    """Convert inline LaTeX string into (mode, text) segments with zero raw LaTeX residue."""
    s = latex.strip()
    if s.startswith("$") and s.endswith("$"):
        s = s[1:-1].strip()
    s = s.replace(r"\{", "\x01").replace(r"\}", "\x02").replace(r"\%", "%").replace(r"\_", "_")
    for cmd in ["text", "mathrm", "mathbf", "operatorname"]:
        while f"\\{cmd}{{" in s:
            idx = s.find(f"\\{cmd}{{")
            start_b = idx + len(cmd) + 1
            depth = 0
            end_b = start_b
            while end_b < len(s):
                if s[end_b] == "{":
                    depth += 1
                elif s[end_b] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                end_b += 1
            inner = s[start_b + 1 : end_b]
            s = s[:idx] + inner + s[end_b + 1 :]
    repls = [
        (r"\mathcal{C}", "C"),
        (r"\hat{y}", "ŷ"),
        (r"\hat{q}", "q̂"),
        (r"\hat{d}", "d̂"),
        (r"\tilde{F1}", "F1*"),
        (r"\Delta", "Δ"),
        (r"\to", "→"),
        (r"\in", "∈"),
        (r"\notin", "∉"),
        (r"\subseteq", "⊆"),
        (r"\subset", "⊂"),
        (r"\cap", "∩"),
        (r"\cup", "∪"),
        (r"\emptyset", "∅"),
        (r"\varnothing", "∅"),
        (r"\neq", "≠"),
        (r"\ne", "≠"),
        (r"\le", "≤"),
        (r"\leq", "≤"),
        (r"\ge", "≥"),
        (r"\geq", "≥"),
        (r"\approx", "≈"),
        (r"\times", "×"),
        (r"\cdot", "·"),
        (r"\forall", "∀"),
        (r"\equiv", "≡"),
        (r"\land", "∧"),
        (r"\lor", "∨"),
        (r"\mid", " | "),
        (r"\pm", "±"),
        (r"\|", "‖"),
        (r"\,", " "),
        (r"\;", " "),
        (r"\quad", "  "),
        (r"\qquad", "    "),
    ]
    for k, v in repls:
        s = s.replace(k, v)

    segs: list[tuple[str, str]] = []
    i = 0
    n = len(s)
    buf: list[str] = []
    while i < n:
        if s[i] in ("_", "^"):
            if buf:
                segs.append(("normal", "".join(buf).replace("\x01", "{").replace("\x02", "}")))
                buf = []
            mode = "sub" if s[i] == "_" else "sup"
            i += 1
            if i < n and s[i] == "{":
                depth = 0
                start_b = i
                while i < n:
                    if s[i] == "{":
                        depth += 1
                    elif s[i] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    i += 1
                val = s[start_b + 1 : i]
                i += 1
            elif i < n:
                val = s[i]
                i += 1
            else:
                val = ""
            segs.append((mode, val.replace("\x01", "{").replace("\x02", "}")))
        else:
            buf.append(s[i])
            i += 1
    if buf:
        segs.append(("normal", "".join(buf).replace("\x01", "{").replace("\x02", "}")))
    return segs


def append_inline_math_runs(
    paragraph,
    math_content: str,
    font_size: Pt,
    default_bold: bool,
    default_color: RGBColor | None,
):
    """Render inline math using native Word runs (<w:r> with Cambria Math and sub/superscript)
    so it renders 100% identically across Microsoft Word, LibreOffice, PDF, and Web Previewers."""
    segs = parse_inline_math_segments(math_content)
    for mode, txt in segs:
        if not txt:
            continue
        run = paragraph.add_run(txt)
        run.font.name = "Cambria Math"
        run.font.size = font_size
        run.bold = default_bold
        if mode == "sub":
            run.font.subscript = True
        elif mode == "sup":
            run.font.superscript = True
        else:
            # Italicize single-letter variables or short variable expressions
            stripped = txt.strip()
            if re.match(r"^[a-zA-Zŷ]$", stripped):
                run.italic = True
        if default_color:
            run.font.color.rgb = default_color


def format_runs_tns(
    paragraph,
    text: str,
    font_size: Pt = BODY_FONT_SIZE,
    default_bold: bool = False,
    default_italic: bool = False,
    default_color: RGBColor | None = None,
    font_name: str = FONT_FAMILY,
):
    """Parse inline markdown (bold, italic, code, math, links, currency) using Times New Roman."""
    text = text.replace(r"\%", "%")
    token_pattern = re.compile(
        r"(\\\*|\\\$[0-9.]+|\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|\$[^$]+\$)"
    )
    parts = token_pattern.split(text)

    for part in parts:
        if not part:
            continue
        if part == r"\*":
            run = paragraph.add_run("*")
            run.font.name = font_name
            run.font.size = font_size
            run.bold = default_bold
            run.italic = default_italic
            if default_color:
                run.font.color.rgb = default_color
        elif re.match(r"^\\\$[0-9.]+$", part):
            run = paragraph.add_run(part[1:])
            run.font.name = font_name
            run.font.size = font_size
            run.bold = default_bold
            run.italic = default_italic
            if default_color:
                run.font.color.rgb = default_color
        elif part.startswith("***") and part.endswith("***"):
            format_runs_tns(
                paragraph,
                part[3:-3],
                font_size=font_size,
                default_bold=True,
                default_italic=True,
                default_color=default_color,
                font_name=font_name,
            )
        elif part.startswith("**") and part.endswith("**"):
            format_runs_tns(
                paragraph,
                part[2:-2],
                font_size=font_size,
                default_bold=True,
                default_italic=default_italic,
                default_color=default_color,
                font_name=font_name,
            )
        elif part.startswith("*") and part.endswith("*"):
            format_runs_tns(
                paragraph,
                part[1:-1],
                font_size=font_size,
                default_bold=default_bold,
                default_italic=True,
                default_color=default_color,
                font_name=font_name,
            )
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = max(Pt(font_size.pt - 1.5), Pt(8.5))
            run.bold = default_bold
            run.font.color.rgb = default_color if default_color else RGBColor(0x8A, 0x1F, 0x11)
        elif part.startswith("[") and "]" in part and part.endswith(")"):
            m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", part)
            if m:
                link_text, _ = m.groups()
                run = paragraph.add_run(link_text)
                run.font.name = font_name
                run.font.size = font_size
                run.font.color.rgb = RGBColor(0x09, 0x69, 0xDA)
                run.underline = True
                run.bold = default_bold
                run.italic = default_italic
            else:
                run = paragraph.add_run(part)
                run.font.name = font_name
                run.font.size = font_size
                run.bold = default_bold
                run.italic = default_italic
        elif part.startswith("$") and part.endswith("$"):
            math_content = part[1:-1]
            append_inline_math_runs(
                paragraph,
                math_content,
                font_size=font_size,
                default_bold=default_bold,
                default_color=default_color,
            )
        else:
            run = paragraph.add_run(part)
            run.font.name = font_name
            run.font.size = font_size
            run.bold = default_bold
            run.italic = default_italic
            if default_color:
                run.font.color.rgb = default_color


class CursorInserter:
    """Helper to insert paragraphs, tables, figures, equations, and code blocks right after a target XML element."""

    _bm_counter = 500

    def __init__(self, doc: docx.Document, anchor_elem):
        self.doc = doc
        self.curr = anchor_elem

    @classmethod
    def next_bm_id(cls) -> int:
        cls._bm_counter += 1
        return cls._bm_counter

    def add_p(
        self,
        text: str = "",
        bold: bool = False,
        italic: bool = False,
        font_size: Pt = BODY_FONT_SIZE,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_before: float = 2,
        space_after: float = 6,
        left_indent_in: float = 0.0,
        first_line_indent_in: float = 0.0,
        keep_with_next: bool = False,
        color: RGBColor | None = None,
    ):
        p = self.doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.15
        if left_indent_in:
            p.paragraph_format.left_indent = Inches(left_indent_in)
        if first_line_indent_in:
            p.paragraph_format.first_line_indent = Inches(first_line_indent_in)
        if keep_with_next:
            p.paragraph_format.keep_with_next = True
        if text:
            format_runs_tns(
                p,
                text,
                font_size=font_size,
                default_bold=bold,
                default_italic=italic,
                default_color=color,
            )
        self.curr.addnext(p._p)
        self.curr = p._p
        return p

    def add_subheading(self, title: str):
        return self.add_p(
            text=f"**{title}**",
            bold=True,
            font_size=Pt(12.5),
            align=WD_ALIGN_PARAGRAPH.LEFT,
            space_before=8,
            space_after=4,
            keep_with_next=True,
            color=RGBColor(0x0A, 0x25, 0x40),
        )

    def add_bullet(self, text: str, level: int = 0):
        indent = 0.30 + (level * 0.25)
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Inches(indent)
        p.paragraph_format.first_line_indent = Inches(-0.18)
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        bullet_char = "•  " if level == 0 else "◦  "
        r_b = p.add_run(bullet_char)
        r_b.bold = True
        r_b.font.name = FONT_FAMILY
        r_b.font.size = BODY_FONT_SIZE
        format_runs_tns(p, text, font_size=BODY_FONT_SIZE)
        self.curr.addnext(p._p)
        self.curr = p._p
        return p

    def add_numbered_item(self, num_label: str, text: str, hanging_in: float = 0.30):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Inches(hanging_in)
        p.paragraph_format.first_line_indent = Inches(-hanging_in)
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        r_n = p.add_run(f"{num_label} ")
        r_n.bold = True
        r_n.font.name = FONT_FAMILY
        r_n.font.size = BODY_FONT_SIZE
        format_runs_tns(p, text, font_size=BODY_FONT_SIZE)
        self.curr.addnext(p._p)
        self.curr = p._p
        return p

    def add_toc_ref_item(self, num_label: str, text: str, bm_name: str, hanging_in: float = 0.25):
        """Insert a List of Figures / List of Tables entry with dot-leader tab and PAGEREF field."""
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Inches(hanging_in)
        p.paragraph_format.first_line_indent = Inches(-hanging_in)
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        pPr = p._element.get_or_add_pPr()
        pPr.append(parse_xml(f'<w:tabs {nsdecls("w")}><w:tab w:val="right" w:leader="dot" w:pos="9063"/></w:tabs>'))
        r_n = p.add_run(f"{num_label} ")
        r_n.bold = True
        r_n.font.name = FONT_FAMILY
        r_n.font.size = BODY_FONT_SIZE
        format_runs_tns(p, text, font_size=BODY_FONT_SIZE)
        p._element.append(
            parse_xml(
                f'<w:r {nsdecls("w")}>'
                f'<w:rPr><w:rFonts w:ascii="{FONT_FAMILY}" w:hAnsi="{FONT_FAMILY}"/><w:sz w:val="24"/></w:rPr>'
                f"<w:tab/>"
                f"</w:r>"
            )
        )
        p._element.append(parse_xml(f'<w:r {nsdecls("w")}><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'))
        p._element.append(
            parse_xml(f'<w:r {nsdecls("w")}><w:instrText xml:space="preserve"> PAGEREF {bm_name} \\h </w:instrText></w:r>')
        )
        p._element.append(parse_xml(f'<w:r {nsdecls("w")}><w:fldChar w:fldCharType="separate"/></w:r>'))
        p._element.append(
            parse_xml(
                f'<w:r {nsdecls("w")}>'
                f'<w:rPr><w:rFonts w:ascii="{FONT_FAMILY}" w:hAnsi="{FONT_FAMILY}"/><w:b/><w:sz w:val="24"/></w:rPr>'
                f"<w:t>1</w:t>"
                f"</w:r>"
            )
        )
        p._element.append(parse_xml(f'<w:r {nsdecls("w")}><w:fldChar w:fldCharType="end"/></w:r>'))
        self.curr.addnext(p._p)
        self.curr = p._p
        return p

    def add_callout(self, title: str, text: str, border_color: str = "0969DA", bg_color: str = "F0F4F8"):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.right_indent = Inches(0.20)
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.keep_together = True
        pPr = p._element.get_or_add_pPr()
        pBdr = parse_xml(
            f"<w:pBdr {nsdecls('w')}>"
            f'<w:left w:val="single" w:sz="24" w:space="8" w:color="{border_color}"/>'
            f"</w:pBdr>"
        )
        pPr.append(pBdr)
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{bg_color}"/>')
        pPr.append(shd)
        format_runs_tns(p, f"**{title}:** {text}", font_size=Pt(11))
        self.curr.addnext(p._p)
        self.curr = p._p
        return p

    def add_code_block(self, code_text: str):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.right_indent = Inches(0.25)
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.05
        p.paragraph_format.keep_together = True
        run = p.add_run(code_text)
        run.font.name = "Consolas"
        run.font.size = Pt(9.0)
        run.font.color.rgb = RGBColor(0x1F, 0x23, 0x28)
        pPr = p._element.get_or_add_pPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F6F8FA"/>')
        pPr.append(shd)
        pBdr = parse_xml(
            f"<w:pBdr {nsdecls('w')}>"
            '<w:top w:val="single" w:sz="4" w:space="4" w:color="D0D7DE"/>'
            '<w:bottom w:val="single" w:sz="4" w:space="4" w:color="D0D7DE"/>'
            '<w:left w:val="single" w:sz="4" w:space="4" w:color="D0D7DE"/>'
            '<w:right w:val="single" w:sz="4" w:space="4" w:color="D0D7DE"/>'
            "</w:pBdr>"
        )
        pPr.append(pBdr)
        self.curr.addnext(p._p)
        self.curr = p._p
        return p

    def add_equation(self, math_latex: str):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.left_indent = Inches(0.30)
        p.paragraph_format.right_indent = Inches(0.30)
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.keep_together = True
        pPr = p._element.get_or_add_pPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8FAFC"/>')
        pPr.append(shd)
        pBdr = parse_xml(
            f"<w:pBdr {nsdecls('w')}>"
            '<w:left w:val="single" w:sz="18" w:space="8" w:color="0969DA"/>'
            "</w:pBdr>"
        )
        pPr.append(pBdr)
        try:
            omml_xml = LatexToOmml.convert_to_omml(math_latex, is_display=True)
            elem = parse_xml(omml_xml)
            normalize_omml_element(elem, color_hex="0A2540", sz_val="22", default_bold=False)
            p._element.append(elem)
        except Exception:
            converted = latex_to_unicode(math_latex)
            run = p.add_run(converted)
            run.font.name = "Cambria Math"
            run.font.size = Pt(11)
            run.italic = True
        self.curr.addnext(p._p)
        self.curr = p._p
        return p

    def add_figure(self, img_filename: str, caption_text: str, fig_id: str, width_in: float = 6.20):
        img_path = FIGURES_DIR / img_filename
        if not img_path.is_file():
            raise FileNotFoundError(f"Missing figure file: {img_path}")
        p_img = self.doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(3)
        p_img.paragraph_format.keep_with_next = True
        run_img = p_img.add_run()
        run_img.add_picture(str(img_path), width=Inches(width_in))

        sdt_elem = parse_xml(
            f'<w:sdt {nsdecls("w")}>'
            f"  <w:sdtPr>"
            f'    <w:tag w:val="{fig_id}"/>'
            f'    <w:alias w:val="{fig_id}"/>'
            f"  </w:sdtPr>"
            f"  <w:sdtContent/>"
            f"</w:sdt>"
        )
        sdt_content = sdt_elem.find(qn("w:sdtContent"))
        for r_elem in [c for c in list(p_img._element) if c.tag == qn("w:r")]:
            sdt_content.append(r_elem)
        p_img._element.append(sdt_elem)

        self.curr.addnext(p_img._p)
        self.curr = p_img._p

        p_cap = self.doc.add_paragraph(style="Caption")
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(2)
        p_cap.paragraph_format.space_after = Pt(8)
        format_runs_tns(
            p_cap,
            caption_text,
            font_size=Pt(10),
            default_italic=True,
            default_color=RGBColor(0x1F, 0x23, 0x28),
        )
        attach_bookmark(p_cap._p, f"_Ref_{fig_id}", self.next_bm_id())
        self.curr.addnext(p_cap._p)
        self.curr = p_cap._p

    def add_table(
        self,
        caption_text: str,
        rows_data: list[list[str]],
        table_id: str,
        bm_name: str | None = None,
        custom_widths: list[float] | None = None,
        caption_style: str = "Caption",
        add_page_break_after: bool = False,
        footnote_text: str | None = None,
    ):
        p_cap = self.doc.add_paragraph(style=caption_style)
        p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_cap.paragraph_format.space_before = Pt(8)
        p_cap.paragraph_format.space_after = Pt(3)
        p_cap.paragraph_format.keep_with_next = True
        format_runs_tns(
            p_cap,
            caption_text,
            font_size=Pt(10.5),
            default_bold=True,
            default_italic=True,
            default_color=RGBColor(0x0A, 0x25, 0x40),
        )
        resolved_bm = bm_name if bm_name else table_id.replace("table_", "_Ref_tbl_")
        attach_bookmark(p_cap._p, resolved_bm, self.next_bm_id())
        self.curr.addnext(p_cap._p)
        self.curr = p_cap._p

        num_cols = max(len(r) for r in rows_data)
        table = self.doc.add_table(rows=len(rows_data), cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        tblPr = table._element.tblPr
        safe_cap = (
            caption_text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "'")
        )
        safe_tid = (
            table_id.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "'")
        )
        tblPr.append(parse_xml(f'<w:tblCaption {nsdecls("w")} w:val="{safe_cap}"/>'))
        tblPr.append(parse_xml(f'<w:tblDescription {nsdecls("w")} w:val="{safe_tid}"/>'))

        cell_font_size = Pt(8.5) if num_cols >= 8 else (Pt(9.0) if num_cols >= 6 else Pt(9.5))
        pad_top, pad_bot, pad_left, pad_right = (50, 50, 40, 40) if num_cols >= 8 else (60, 60, 50, 50)

        for r_idx, row_data in enumerate(rows_data):
            is_header = r_idx == 0
            for c_idx in range(num_cols):
                cell_text = row_data[c_idx] if c_idx < len(row_data) else ""
                cell = table.cell(r_idx, c_idx)
                p = cell.paragraphs[0]
                p.text = ""
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (is_header or (c_idx > 0 and len(cell_text) < 18)) else WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(1)
                p.paragraph_format.line_spacing = 1.05

                if is_header:
                    set_cell_background(cell, "092C4C")
                    pPr = p._element.get_or_add_pPr()
                    pPr.append(parse_xml(f'<w:rPr {nsdecls("w")}><w:color w:val="FFFFFF"/><w:b/></w:rPr>'))
                    format_runs_tns(
                        p,
                        cell_text,
                        font_size=cell_font_size,
                        default_bold=True,
                        default_color=RGBColor(0xFF, 0xFF, 0xFF),
                    )
                else:
                    set_cell_background(cell, "F8FAFC" if r_idx % 2 == 1 else "FFFFFF")
                    format_runs_tns(
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

        apply_table_pagination_rules(table, table_id=table_id)
        if len(rows_data) >= 11:
            # Multi-page / tall tables must allow page breaks between body rows so the table body stays attached to its caption
            for r_i, row in enumerate(table.rows):
                if r_i > 0:
                    for cell in row.cells:
                        for p_c in cell.paragraphs:
                            p_c.paragraph_format.keep_with_next = False
        if custom_widths and len(custom_widths) == num_cols:
            for col_idx, w in enumerate(custom_widths):
                table.columns[col_idx].width = Inches(w)
            for row in table.rows:
                for col_idx, w in enumerate(custom_widths):
                    row.cells[col_idx].width = Inches(w)
        else:
            assign_table_column_widths(table, num_cols, rows_data[0])

        self.curr.addnext(table._tbl)
        self.curr = table._tbl

        if footnote_text:
            fn_p = self.doc.add_paragraph()
            fn_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            fn_p.paragraph_format.space_before = Pt(3)
            fn_p.paragraph_format.space_after = Pt(6)
            fn_p.paragraph_format.line_spacing = 1.10
            format_runs_tns(
                fn_p,
                footnote_text,
                font_size=Pt(9.5),
                default_italic=True,
                default_color=RGBColor(0x33, 0x41, 0x55),
            )
            self.curr.addnext(fn_p._p)
            self.curr = fn_p._p
        else:
            post_p = self.doc.add_paragraph()
            post_p.paragraph_format.space_before = Pt(0)
            post_p.paragraph_format.space_after = Pt(4)
            if add_page_break_after:
                r_pb = post_p.add_run()
                r_pb._r.append(parse_xml(f'<w:br {nsdecls("w")} w:type="page"/>'))
            self.curr.addnext(post_p._p)
            self.curr = post_p._p
        return table


# ==============================================================================
# CANONICAL DATA TABLES (Sequentially Numbered Table 1 .. Table 14)
# ==============================================================================

TABLE_1_RQ = [
    ["RQ", "Research Question", "Hypothesis", "Independent Variable", "Dependent Variable", "Conditions", "Primary & Diagnostic Metrics"],
    [
        "RQ1",
        "Does grounding a reasoning LLM in retrieved MITRE ATT&CK enterprise reference context improve exact technique and sub-technique attribution accuracy and 474-class Macro-F1 over an unaugmented No-RAG baseline under symmetric reasoning settings?",
        "H1: $\\text{Macro-F1}(\\text{RAG}) > \\text{Macro-F1}(\\text{No-RAG})$ and $\\text{Acc}_{\\text{e2e}}(\\text{RAG}) > \\text{Acc}_{\\text{e2e}}(\\text{No-RAG})$",
        "Presence of retrieved ATT&CK context (No-RAG vs. RAG)",
        "Exact ATT&CK Technique / Sub-technique attribution quality",
        "`no_rag`, `rag_k1`, `rag_k3`, `rag_k5`, `rag_k10`",
        "Headline Accuracy ($\\text{Acc}_{\\text{e2e}}$), Valid Accuracy ($\\text{Acc}_{\\text{valid}}$), 474-class Macro-F1, 95% Cluster-Bootstrap CI (440 clusters), Unclustered McNemar $p$",
    ],
    [
        "RQ2",
        "When attribution errors occur under RAG, how do upstream retrieval misses ($Y_i \\cap R_{i,k} = \\emptyset$) and downstream model selection discrepancies ($Y_i \\cap R_{i,k} \\neq \\emptyset \\land \\hat{y}_i \\notin Y_i$) manifest across independent measurement axes with overlaps, and how do single-event vs. contextual-event views correlate with these axes?",
        "H2: Downstream prediction correctness is higher in the post-retrieval stratum where at least one ground-truth technique is retrieved ($P(\\text{Correct}\\mid Y_i \\cap R_{i,k} \\neq \\emptyset) > P(\\text{Correct}\\mid Y_i \\cap R_{i,k} = \\emptyset)$)",
        "Ground-truth intersection with Top-$k$ candidates ($Y_i \\cap R_{i,k}$) & telemetry view type",
        "Conditional prediction correctness & error locus co-occurrence",
        "`rag_k1`, `rag_k3`, `rag_k5`, `rag_k10` (278 single vs. 440 contextual TEST views)",
        "Standalone $\\text{Hit@}k$ (`ANY_GT_RETRIEVED`), Multi-label $\\text{Macro Recall@}k$, $P(\\text{Correct}\\mid Y_i \\cap R_{i,k} \\neq \\emptyset)$, $P(\\text{Correct}\\mid Y_i \\cap R_{i,k} = \\emptyset)$, D2i Axes",
    ],
    [
        "RQ3",
        "How does varying retrieval candidate depth ($k \\in \\{1, 3, 5, 10\\}$) affect attribution performance, distractor susceptibility, wall-clock latency, and API token/ledger costs?",
        "H3: Very small $k$ ($k=1$) risks distractor susceptibility when retrieval misses, while larger $k$ increases prompt token volume, latency, and cost",
        "Retrieval candidate depth $k \\in \\{0, 1, 3, 5, 10\\}$",
        "Accuracy, Macro-F1, input/output token volume, latency, usage cost, and conservative ledger spend",
        "6,400 canonical dispatches across 5 conditions ($1,280 \\times 5$)",
        "Total & Mean Input/Output Tokens, Mean & Median Latency (s), Token-Usage Cost (USD), Conservative Ledger Spend (USD) under USD 19.99 cap",
    ],
]

TABLE_2_COMP_A = [
    ["Dimension", "Yang & Hsu (2026) [7]", "Adediran et al. (2026) [10]", "CAM-LDS (Landauer et al., 2026) [8]", "TechniqueRAG (Lekssays et al., 2025) [5]"],
    ["1. Primary Input", "Windows Sysmon process trees", "AWS CloudTrail JSON events", "Linux system logs (auditd, syslog) + IDS alerts", "Unstructured CTI text reports"],
    ["2. Target Platform", "Windows", "AWS Cloud", "Linux / Multi-source", "Cross-platform (CTI text)"],
    ["3. Core Task", "Malicious behavior detection & explanation", "Cloud threat detection & ATT&CK mapping", "Benchmark log interpretation", "CTI technique & sub-technique annotation"],
    ["4. ATT&CK Target Granularity", "Behavior explanation (Exact ID UNVERIFIED)", "Technique & Sub-technique (`Txxxx.yyy`)", "Collapses sub-techniques to parent (`Txxxx`); §5.2.2 parent-technique eval", "Technique & Sub-technique (`Txxxx.yyy`)"],
    ["5. RAG Architecture", "Semantic matching RAG", "Two-step query expansion RAG (Vertex AI)", "None (Zero-shot prompting)", "Exemplar retrieval (BM25 + DeepSeek v3 rerank)"],
    ["6. Retrieval Corpus", "UNVERIFIED", "ATT&CK Cloud, AWS catalogue, threat blogs", "N/A", "Annotated text-label pairs (TRAM, Procedures)"],
    ["7. Matched No-RAG Baseline?", "Yes (Mistral, phi-2, TinyLlama w/o RAG)", "Yes (Gemini 2.5 Pro baseline w/o RAG)", "Evaluates only zero-shot (no RAG)", "Yes (Zero-shot and fine-tuned w/o RAG)"],
    ["8. Top-k Retrieval Ablation?", "UNVERIFIED (full text unavailable)", "No (Numeric k NOT REPORTED; ablation deferred)", "Evaluates output cutoff Top-$k$ (§5.2.2); no retriever", "Evaluates pool size $K=40$, fixed set of $k=3$ exemplars"],
    ["9. Standalone Retriever Metrics?", "UNVERIFIED", "NOT REPORTED (Generation gap only)", "N/A", "P/R/F1 on ranking; standalone Hit@k NOT REPORTED"],
    ["10. Failure Decomposition?", "UNVERIFIED", "Qualitative error categories (unresolved 26% vs 60% discrepancy)*", "No", "Analyzes generator vs retriever errors"],
    ["11. Telemetry Leakage Controls", "UNVERIFIED", "Notes `stratus-red-team` agent in raw logs", "Strips explicit ATT&CK labels/tactics", "CTI text; no detector rule metadata"],
    ["12. Primary Models", "Mistral-7B, phi-2, TinyLlama-1.1B", "Gemini 2.5 Pro", "GPT-5.5, GPT-5.2, Llama 4, Qwen 3, Ministral (Journal)", "Ministral-8B (fine-tuned)"],
    ["13. Headline Metrics", "Precision, F1, False Positive Rate", "Accuracy, Precision, Recall, F1, Latency, Cost", "Technique Rank, P@k, Recall@k, MRR", "Precision, Recall, Macro-F1, Micro-F1"],
    ["14. Primary Dataset", "Attack samples + benign process trees", "200 AWS CloudTrail events (122 mal / 78 ben)", "7 scenarios, 198 log steps, 18 sources", "TRAM, Procedures, Expert CTI datasets"],
    ["15. Closest Similarity", "Sysmon logs + matched No-RAG/RAG", "Controlled No-RAG vs RAG on telemetry", "Exact technique prediction from command logs", "ATT&CK RAG with retrieval quality analysis"],
    ["16. Key Difference", "Binary detection; process tree heuristics", "AWS CloudTrail API; two-step Vertex RAG", "Zero-shot only (no RAG); Linux focus", "Unstructured CTI text; fine-tunes generator"],
]

TABLE_3_COMP_B = [
    ["Dimension", "H-TechniqueRAG (Morbiato et al., 2026) [6]", "Trace2ATT&CK (Lupinacci et al., 2026) [11]", "Okuma et al. (2023) [9]", "LADE (Gwak et al., 2026/2027) [12]", "RAG2ATT&CK (This Work)"],
    ["1. Primary Input", "Unstructured CTI text reports", "Linux eBPF provenance graphs", "Windows Sysmon event logs", "Chronological command/script traces", "Windows endpoint telemetry (Sysmon / Security logs)"],
    ["2. Target Platform", "Cross-platform (CTI text)", "Linux", "Windows", "Cross-platform host OS", "Windows Enterprise"],
    ["3. Core Task", "CTI technique annotation & context routing", "Kernel telemetry to ATT&CK mapping", "UNVERIFIED (bibliographic record only)", "APT detection & TTP mapping", "Exact ATT&CK Technique / Sub-technique attribution"],
    ["4. ATT&CK Target Granularity", "Tactic $\\to$ Technique hierarchy", "Ranked Technique & Sub-technique candidates", "UNVERIFIED", "Ranked Technique candidates (Top-3/10)", "Exact Technique & Sub-technique (`Txxxx.yyy`)"],
    ["5. RAG Architecture", "Hierarchical dense RAG (FAISS IVF)", "Dense chunk retrieval (Chroma + MMR)", "UNVERIFIED", "None (Rubric prompting with static ATT&CK text)", "Dense semantic RAG (FAISS IndexFlatIP cosine)"],
    ["6. Retrieval Corpus", "ATT&CK Enterprise (CTI-RCM, TRAM, MITRE)", "ATT&CK Enterprise KB (800-word chunks)", "UNVERIFIED", "N/A", "Official ATT&CK Enterprise v19.2 (474 active Windows docs)"],
    ["7. Matched No-RAG Baseline?", "Yes (Zero-shot Llama 3 direct-prompt baseline)", "Yes (Prompting baseline w/o RAG)", "UNVERIFIED (full text access blocked)", "Prompting only (no RAG ablation)", "Yes (Strictly matched gpt-5.6-luna alias w/o RAG)"],
    ["8. Top-k Retrieval Ablation?", "Tactic count $M$ sensitivity (peak $M=3$, quota $K_A=15$); not flat $k$ sweep", "Fixed retriever depth (5 chunks), output cutoff 5", "UNVERIFIED", "Output candidate cutoff $k \\in \\{3, 10\\}$; no RAG retriever", "Yes ($k \\in \\{1, 3, 5, 10\\}$ systematically ablated)"],
    ["9. Standalone Retriever Metrics?", "Micro P/R/F1, MAP@10; standalone Hit@k NOT REPORTED", "NOT REPORTED (Fixed 5 chunks; standalone Recall@k not separable)", "UNVERIFIED", "N/A", "Yes (Both Hit@k and Macro Recall@k reported)"],
    ["10. Failure Decomposition?", "Analyzes distractor impact in flat vs hierarchical", "No (End-to-end system evaluation)", "UNVERIFIED", "No", "Independent axes with overlaps (D2i)"],
    ["11. Telemetry Leakage Controls", "CTI text; curated benchmarks", "Kernel syscalls; no detector rule metadata", "UNVERIFIED (full text access blocked)", "Script command lines analyzed", "Strict field allowlist; detector rules/labels purged"],
    ["12. Primary Models", "Llama-3-8B-Instruct", "foundation-sec-8b, qwen3.5-9b, gpt-oss, gemma4-31b-it, deepseek-r1-qwen32b, llama3.3-70b", "NOT REPORTED / UNVERIFIED", "gpt-oss-120B, Llama-3.3-70B, Mistral-Small-3.2-24B, Gemini-2.5-Pro", "OpenAI gpt-5.6-luna (xhigh reasoning effort)"],
    ["13. Headline Metrics", "Micro P/R/F1, MAP@10, Latency, API calls", "HR@5, MRR@5, NDCG@5", "NOT REPORTED / UNVERIFIED", "Precision, Recall, F1, HR/MRR/NDCG @ 3, 10", "End-to-End Accuracy, 474-class Macro-F1, Hit@k, Recall@k"],
    ["14. Primary Dataset", "1,200 CTI-RCM + 2,800 MITRE + 450 TRAM", "347 Linux Atomic Red Team executions", "Atomic Red Team Sysmon logs (metadata only)", "AVIATOR (35/32 seqs) & Caldera-derived (33 APT seqs per 2:1 & 10:1 setting + 33 benign)", "1,280 paired synthetic TEST views (640 scenario pairs)"],
    ["15. Closest Similarity", "Investigating retrieval depth & distractor noise", "Telemetry-to-ATT&CK mapping comparing RAG/prompt", "Windows Sysmon mapped to ATT&CK", "Host command execution traces mapped to ATT&CK", "Integrates telemetry, exact attribution, depth ablation"],
    ["16. Key Difference", "Unstructured CTI text; hierarchical routing", "Linux eBPF provenance graphs; no depth ablation", "UNVERIFIED (IEEE record only; full text inaccessible)", "Prompting only (no RAG); AVIATOR & Caldera sequence evaluation", "Windows endpoint logs + exact ID + depth ablation + error split"],
]

TABLE_4_PRIMARY = [
    ["Condition", "Depth ($k$)", "Scorable ($N$)", "Headline $\\text{Acc}_{\\text{e2e}}$ (95% Cluster CI)", "$\\Delta\\text{Acc}$ vs. No-RAG (95% CI)", "474-Class Macro-F1 (0–1)", "$\\Delta\\text{Macro-F1}$ (95% Cluster CI)", "Single-GT ($N=678$)", "Multi-GT ($N=40$)"],
    ["`no_rag`", "0", "718", "77.99% [74.64%, 80.88%]", "Baseline", "0.012608 (1.26%)", "Baseline", "77.43%", "87.50%"],
    ["`rag_k1`", "1", "718", "77.02% [73.50%, 80.17%]", "-0.975 pp [-3.186, +1.124]", "0.012668 (1.27%)", "+0.000060 [-0.000242, +0.000363]", "75.66%", "100.00%"],
    ["`rag_k3`", "3", "718", "78.55% [75.00%, 81.74%]", "+0.557 pp [-2.786, +3.934]", "0.013643 (1.36%)", "+0.001034 [+0.000632, +0.001424]", "77.29%", "100.00%"],
    ["`rag_k5`", "5", "718", "78.83% [75.07%, 82.35%]", "+0.836 pp [-2.934, +4.603]", "0.013891 (1.39%)", "+0.001282 [+0.000860, +0.001679]", "77.58%", "100.00%"],
    ["`rag_k10`", "10", "718", "79.53% [75.81%, 82.85%]", "+1.532 pp [-2.355, +5.300]", "0.014024 (1.40%)", "+0.001415 [+0.001011, +0.001792]", "78.32%", "100.00%"],
]

TABLE_5_DIAG = [
    ["Condition", "Scorable Views ($N$)", "Completed Outputs (of 1,280)", "Parse Failures", "Invalid ATT&CK IDs", "Invalid ID Rate (%)"],
    ["`no_rag`", "718", "1,280", "0", "0", "0.00%"],
    ["`rag_k1`", "718", "1,280", "0", "0", "0.00%"],
    ["`rag_k3`", "718", "1,274", "0", "0", "0.00%"],
    ["`rag_k5`", "718", "1,277", "0", "0", "0.00%"],
    ["`rag_k10`", "718", "1,276", "0", "0", "0.00%"],
]

TABLE_6_REPR = [
    ["Condition", "Single-Event $\\text{Acc}_{\\text{e2e}}$ ($N=278$)", "Contextual-Event $\\text{Acc}_{\\text{e2e}}$ ($N=440$)", "Single Macro-F1", "Contextual Macro-F1", "$\\Delta\\text{Acc}$ (Context - Single)"],
    ["`no_rag`", "87.05%", "72.27%", "0.0133 (1.33%)", "0.0120 (1.20%)", "-14.78 pp"],
    ["`rag_k1`", "85.61%", "71.59%", "0.0131 (1.31%)", "0.0121 (1.21%)", "-14.02 pp"],
    ["`rag_k3`", "84.17%", "75.00%", "0.0129 (1.29%)", "0.0130 (1.30%)", "-9.17 pp"],
    ["`rag_k5`", "83.45%", "75.91%", "0.0129 (1.29%)", "0.0131 (1.31%)", "-7.54 pp"],
    ["`rag_k10`", "83.81%", "76.82%", "0.0129 (1.29%)", "0.0132 (1.32%)", "-6.99 pp"],
]

TABLE_7_PAIRED = [
    ["Condition", "Complete Pairs ($N$)", "Single Paired Acc", "Contextual Paired Acc", "Paired $\\Delta$", "Both Correct", "Single Only", "Contextual Only", "Both Incorrect", "McNemar $p_{\\text{exact}}$"],
    ["`no_rag`", "278", "87.05%", "92.45%", "+5.40 pp", "228", "14", "29", "7", "0.0315"],
    ["`rag_k1`", "278", "85.61%", "92.45%", "+6.83 pp", "229", "9", "28", "12", "0.0026"],
    ["`rag_k3`", "278", "84.17%", "88.85%", "+4.68 pp", "225", "9", "22", "22", "0.0294"],
    ["`rag_k5`", "278", "83.45%", "85.25%", "+1.80 pp", "221", "11", "16", "30", "0.4421"],
    ["`rag_k10`", "278", "83.81%", "83.81%", "+0.00 pp", "216", "17", "17", "28", "1.0000"],
]

TABLE_8_FAILURE = [
    ["Condition", "Total Errors", "Retrieval Miss ($Y_i \\cap R_{i,k} = \\emptyset$)", "Selection Failure ($Y_i \\cap R_{i,k} \\neq \\emptyset \\land \\text{Wrong}$)", "Miss & Wrong Overlap ($Y_i \\cap R_{i,k} = \\emptyset \\land \\text{Wrong}$)", "Correct Despite Miss ($Y_i \\cap R_{i,k} = \\emptyset \\land \\text{Correct}$)", "Invalid ID / Parse / Provider Failure"],
    ["`no_rag`", "158", "N/A", "N/A", "N/A", "N/A", "0 / 0 / 0"],
    ["`rag_k1`", "165", "691 (96.24%)", "0", "165 (100.00%)", "526", "0 / 0 / 0"],
    ["`rag_k3`", "154", "600 (83.57%)", "3", "151 (98.05%)", "449", "0 / 0 / 0"],
    ["`rag_k5`", "152", "545 (75.91%)", "5", "147 (96.71%)", "398", "0 / 0 / 0"],
    ["`rag_k10`", "147", "397 (55.29%)", "28", "119 (80.95%)", "278", "0 / 0 / 0"],
]

TABLE_9_COST = [
    ["Condition", "Total Input Tokens", "Total Output Tokens", "Mean Output / Req", "Mean Latency", "Median Latency", "Usage Estimated Cost (USD)", "Conservative Ledger Spend (USD)*", "Mean Ledger / Query (USD)"],
    ["`no_rag`", "863,139", "209,466", "163.6", "2.90s", "2.30s", "USD 0.4671", "USD 0.4671 (0.47)", "USD 0.000365"],
    ["`rag_k1`", "1,595,554", "299,128", "233.7", "3.51s", "2.62s", "USD 0.7575*", "USD 1.2972 (1.30)*", "USD 0.001013*"],
    ["`rag_k3`", "2,780,640", "403,100", "314.9", "4.22s", "2.74s", "USD 1.1789", "USD 1.1789 (1.18)", "USD 0.000921"],
    ["`rag_k5`", "3,917,047", "419,880", "328.0", "4.33s", "2.87s", "USD 1.4831", "USD 1.4831 (1.48)", "USD 0.001159"],
    ["`rag_k10`", "6,546,274", "427,346", "333.9", "4.37s", "2.67s", "USD 2.1494", "USD 2.1494 (2.15)", "USD 0.001679"],
]

TABLE_10_LEDGER = [
    ["Accounting Dimension", "Ledger Field Identifier", "Value", "Currency"],
    ["Total Study Authorized Budget Ceiling", "`total_study_budget_usd`", "19.9900", "USD"],
    ["Canonical Conditions Total Ledger Spend", "`canonical_conditions_total_usd`", "6.5758", "USD"],
    ["Prior Pilot Exploratory Hold", "`prior_pilot_provisional_hold_usd`", "0.0526", "USD"],
    ["Active Unsettled Reservations", "`active_reservations_usd`", "0.0000", "USD"],
    ["Orphaned Budget Claims", "`orphan_reservations_usd`", "0.0000", "USD"],
    ["Total Study Committed Spend", "`total_study_committed_spend_usd`", "6.6284", "USD"],
    ["Net Remaining Uncommitted Budget", "`net_remaining_uncommitted_budget_usd`", "13.3616", "USD"],
]

TABLE_11_MANIFEST = [
    ["Asset Description", "File Path", "Digest Type", "Canonical SHA-256 Digest"],
    ["Scientific Protocol Decisions Digest", "`config/experiment_protocol_v1.json`", "Protocol Digest", "`d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c`"],
    ["Protocol Configuration File", "`config/experiment_protocol_v1.json`", "File SHA-256", "`a402b04ab463172f9d4079bff27b089ca8a21ffd0805d097af6cb1f3c7b5a8fb`"],
    ["Model Configuration File", "`config/model.json`", "File SHA-256", "`312c34cedd84106f2004c6070b72aeac1dd84209a464e2993fee3ec87822697f`"],
    ["Retrieval Configuration File", "`config/retrieval.json`", "File SHA-256", "`b33a93913e7f6de36f6f9021f77b2c9dcb1d426929162acb250a3c73ac8e6e25`"],
    ["Benchmark Scope File", "`config/benchmark_scope.json`", "File SHA-256", "`d6aa89831dec75362b4fd48de0fd6e7082290f2be0cb7bd0afc6bc518148db8b`"],
    ["Base Prompt Template File", "`prompts/baseline_v1.txt`", "File SHA-256", "`b751fde1ee33b03ec0bdc07cbba10267002d2086cf22b91a74bdfd123856f206`"],
    ["ATT&CK Enterprise v19.2 Raw STIX", "`attack/raw/enterprise-v19.2/enterprise-attack-19.2.json`", "File SHA-256", "`dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4`"],
    ["Active Windows Retrieval Corpus", "`attack/corpus/enterprise-windows-v19.2.jsonl`", "File SHA-256", "`b219341154ddf2f12e97d622158a04ab7d57641df6a865559258d365852c3c75`"],
    ["Corpus Manifest File", "`attack/corpus/enterprise-windows-v19.2.manifest.json`", "File SHA-256", "`6bd769324f6ac9193d7df82e7f54f5a1397a41b9bc72be767da5a72b54b3a47c`"],
    ["FAISS Binary Index File", "`attack/index/enterprise-windows-v19.2.index`", "File SHA-256", "`7e3b9944870860766ebd5ba76f19a420c1bbe57cebd4e4238b06fd31128578e5`"],
    ["Index Document Mapping File", "`attack/index/enterprise-windows-v19.2.docmap.json`", "File SHA-256", "`a7de3dfcf2b6e186e639d2922fcbc27766c160ae58bbafea74b5efc0faf30586`"],
    ["Dataset Manifest File", "`data/ground_truth/synthetic/dataset_manifest.json`", "File SHA-256", "`4576b793360d02b60d619d199fd34d4555ace33215303ee847715c162a50dcc2`"],
    ["Live Execution Launcher Hash", "Runtime wrapper entrypoint", "Code SHA-256", "`05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa`"],
]

TABLE_12_PROVENANCE = [
    ["Asset Description", "File Path / Identifier", "Digest Type", "Hash / Git SHA"],
    ["Canonical Metric Bundle", "`artifacts/results/canonical_metric_bundle_v2.json`", "File SHA-256", "`442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34`"],
    ["Canonical Overall Metrics", "`artifacts/results/outputs/overall_metrics.json`", "File SHA-256", "`25662753963ecdd05d16b8607095fffb964c0d53cd2c43026c50b47b22e55074`"],
    ["Canonical Condition Metrics", "`artifacts/results/outputs/per_condition_metrics.json`", "File SHA-256", "`e6592f9a0f97739be1168f9d1448e0d209fe4a300727ff6ad78902523f1591d6`"],
    ["Canonical Retrieval Conditional", "`artifacts/results/outputs/retrieval_conditional_metrics.json`", "File SHA-256", "`2c68395f4ae923167b7cbc08835ff2772044ddc7695f69c0781ec277287d775f`"],
    ["Canonical RQ Analysis", "`artifacts/results/outputs/rq_analysis.json`", "File SHA-256", "`1604a5537b57cefbe86fd59d7fa2acfb8658a27215f7df8a98dfd0c400981156`"],
    ["Canonical Run Provenance", "`artifacts/results/outputs/run_provenance.json`", "File SHA-256", "`90918c9efe149c537c9b2cee7f7392607f273c12627bcc61b9dc9443359e63a1`"],
    ["Terminal Snapshot Seal", "`reports/evidence/canonical_run_seal_v1.json`", "File SHA-256", "`ae7a9ada86927a79e0c6916b44d3f0ba9e1f9756df55dd7b2fce712b35d48701`"],
    ["Execution Commit", "Runner execution state", "Git Commit SHA", "`80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315`"],
    ["Official Release Merge Commit", "Tag `v1.0.0-rag2attck-study` (ID `402490699`)", "Git Commit SHA", "`ca8d39824a72e80053371e208506bfdc6332dc5d`"],
    ["Documentation Sync Commit", "Branch `main` after PR #39", "Git Commit SHA", "`84b6e5071d063bd4471cc70d477458855ac9c3ea`"],
]

TABLE_13_ROADMAP = [
    ["Phase", "Planned Schedule Window", "Task IDs", "Core Deliverable & Acceptance Criteria", "Actual Completion Date & Audit Evidence", "Status"],
    ["Literature & Scope", "W1 (15–21 Sep 2026)", "T01–T04", "Freeze replication-and-extension framing, annotate 8 core comparators, finalize RQ1–RQ3, and freeze 16-dimension comparator matrix.", "21 Sep 2026 (`reports/T33_related_work.md`, PR #8)", "Done (4/4)"],
    ["Data & Ground Truth", "W2 (22–28 Sep 2026)", "T05–T10", "Audit Mendeley v3 telemetry (15,713 discrepancies stopped at Task 2), engineer `synthetic-paired-v1` (670 pairs / 1,340 views), and pass `INFERENCE_ALLOWLIST` leakage audit.", "28 Sep 2026 (`dataset_manifest.json` `4576b793...`)", "Done (6/6)"],
    ["No-RAG Baseline", "W3 (29 Sep–5 Oct 2026)", "T11–T14", "Fix `gpt-5.6-luna` alias (`reasoning_effort=xhigh`), implement OpenAI Responses API client with JSON schema & two-layer validation, and freeze `prompts/baseline_v1.txt`.", "30 Sep 2026 (`model.json` `312c34ce...`, `baseline_v1.txt` `b751fde1...`)", "Done (4/4)"],
    ["Real Telemetry Pilot", "W3 (29 Sep–5 Oct 2026)", "T15", "Real Windows telemetry pilot formally deferred per Protocol v1.1 Decision D6 (`NOT_REQUIRED_FOR_SYNTHETIC_BENCHMARK`, `DATA_UNAVAILABLE`).", "30 Sep 2026 (Protocol v1.1 Decision D6 freeze)", "Deferred / Out-of-Scope (1)"],
    ["RAG Pipeline", "W4 (6–12 Oct 2026)", "T16–T20", "Pin ATT&CK Enterprise v19.2 (474 active Windows docs), build `all-MiniLM-L6-v2` + FAISS `IndexFlatIP` retriever, and execute T20 retrieval diagnostics.", "01 Oct 2026 (`retrieval_metrics.json` `3e40e18f...`)", "Done (5/5)"],
    ["Main Experiments", "W5 (13–19 Oct 2026)", "T21–T26", "Freeze Protocol v1.1 (`D1–D7`), enforce USD 19.99 financial guard, and execute 6,400 canonical live dispatches (`live-66b94b1676bf46a9`).", "02 Oct 2026 (`run_provenance.json` `2026-10-02T03:43:44Z`, ahead of schedule)", "Done (6/6)"],
    ["Evaluation", "W6 (20–26 Oct 2026)", "T27–T30", "Compute end-to-end metrics, 474-class Macro-F1 (D2d/D2j), 95% cluster-bootstrap CIs (440 clusters), McNemar tests, Hit@k vs. Recall@k, and D2i failure axes.", "03 Oct 2026 (`canonical_metric_bundle_v2.json` `442b5933...`, ahead of schedule)", "Done (4/4)"],
    ["Report", "W7 (27 Oct–2 Nov 2026)", "T31–T33", "Author Methodology, Experiments & Results, Discussion, and 16-dimension comparator synthesis with 8 high-resolution figures and 14 canonical tables.", "19–30 Oct 2026 (Git `84b6e507...`, ahead of schedule)", "Done (3/3)"],
    ["QA & Submission", "W8 (3–9 Nov 2026)", "T34–T36", "Execute offline reproducibility QA (178/178 tests passed), finalize presentation kit, and publish `public_v4_candidate_20261003.zip` & Release `v1.0.0-rag2attck-study`.", "20–30 Oct 2026 (Release `ca8d3982...`, completed ahead of W8 window)", "Done (3/3; Total 35/35 In-Scope)"],
]

TABLE_14_RISKS = [
    ["Risk Category", "Severity", "Mitigation Control Implemented in RAG2ATT&CK"],
    ["Generic RAG-vs-No-RAG novelty overlap", "Medium", "Framed strictly as a controlled conceptual replication-and-extension study on Windows endpoint logs with exact attribution and failure decomposition; zero unsubstantiated 'first-ever' claims."],
    ["Label leakage from detector rules / metadata", "High", "Enforced `INFERENCE_ALLOWLIST` in `src/synthetic.py` retaining only `sample_id` and sanitized per-channel behavioral `endpoint_evidence` (e.g., `TargetUserName`, `SubjectUserName`, `SubjectLogonId`, `CommandLine`); purged all Sigma/Wazuh rule names, `rule.mitre.*`, and `Contoso` markers."],
    ["Corrupted external public telemetry (Mendeley v3)", "High", "Forensic Task 2 audit detected 15,713 cell discrepancies (`_source.id` truncation, `#NAME?` formulas); enforced fail-closed stop (`RECONCILIATION_DIVERGENT`) and bounded claims strictly to `synthetic-paired-v1` under Protocol D6."],
    ["Class support concentration & zero denominators", "Medium", "Frozen 474-class Macro-F1 universe (`D2d`) combined with explicit `NULL` zero-denominator semantics (`D2j`) and piecewise count formula across all boundary cases; reported support-based upper bound ($8/474 \\approx 1.69\\%$)."],
    ["API cost overrun & transient provider errors", "Medium", "Pre-dispatch worst-case reservation (`$0.53974560`/attempt), 25,600 attempt cap, deterministic exponential backoff (`max_retries=3`), settling at `$6.5758` (`$6.6284` total committed) under `$19.99` ceiling."],
    ["Upstream API model version mutability", "Low", "Fixed requested model alias (`gpt-5.6-luna`) and inference settings across conditions; logged timestamped response IDs (`run_provenance.json`) and disclosed `model_version: null` and `system_fingerprints: []` under Decision D3."],
    ["Prompt asymmetry across conditions", "Medium", "Used byte-identical `prompts/baseline_v1.txt` (`b751fde1...`) with a universal context handling clause across No-RAG and all RAG depths."],
    ["Post-publication irreproducibility / API cost barrier", "Low", "Published portable verification archive `public_v4_candidate_20261003.zip` (`1d5f9f4b...`) and `scripts.reproduce_canonical_study` under `OFFLINE_GUARD` (`$0.00` API cost, $< 10^{-12}$ numeric tolerance)."],
]

REFERENCES_LIST = [
    (
        "[1]",
        'The MITRE Corporation. "MITRE ATT&CK® Enterprise Matrix, Version 19.2." Published 05 August 2026. Available: https://github.com/mitre-attack/attack-stix-data/releases/tag/v19.2 (version history: https://attack.mitre.org/resources/versions/).',
    ),
    (
        "[2]",
        'OpenAI. "GPT-5.6 Luna Model." OpenAI API Documentation, accessed 02 October 2026. Available: https://developers.openai.com/api/docs/models/gpt-5.6-luna.',
    ),
    (
        "[3]",
        'OpenAI. "Reasoning Models." OpenAI API Documentation Guides, accessed 02 October 2026. Available: https://developers.openai.com/api/docs/guides/reasoning.',
    ),
    (
        "[4]",
        'Lewis, P.; Perez, E.; Piktus, A.; Petroni, F.; Karpukhin, V.; Goyal, N.; Küttler, H.; Lewis, M.; Yih, W.-t.; Rocktäschel, T.; Riedel, S.; Kiela, D. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." In: *Advances in Neural Information Processing Systems (NeurIPS 2020)*, vol. 33, pp. 9459–9474, 2020.',
    ),
    (
        "[5]",
        'Lekssays, A.; Shukla, U.; Sencar, H. T.; Parvez, M. R. "TechniqueRAG: Retrieval Augmented Generation for Adversarial Technique Annotation in Cyber Threat Intelligence Text." In: *Findings of the Association for Computational Linguistics: ACL 2025*, pp. 20913–20926, 2025. DOI: https://doi.org/10.18653/v1/2025.findings-acl.1076; arXiv: https://arxiv.org/abs/2505.11988.',
    ),
    (
        "[6]",
        'Morbiato, F.; Keller, M.; Nair, P.; Romano, L. "Hierarchical Retrieval Augmented Generation for Adversarial Technique Annotation in Cyber Threat Intelligence Text." *arXiv preprint* arXiv:2604.14166, 2026. Available: https://arxiv.org/abs/2604.14166.',
    ),
    (
        "[7]",
        'Yang, D.-R.; Hsu, F.-H. "LLM-Based Malicious Behavior Detection from Sysmon Event Logs: A Practical System Integrating Process Trees, RAG, and In-Context Analysis." In: *Security and Information Technologies with AI, Internet Computing and Big-Data Applications (SITAIBA 2025)*, Smart Innovation, Systems and Technologies, vol. 8767, pp. 235–251, Springer Cham, 2026. DOI: https://doi.org/10.1007/978-3-032-24063-7_18.',
    ),
    (
        "[8]",
        'Landauer, M.; Hotwagner, W.; Boenke, T.; Skopik, F.; Wurzenberger, M. "CAM-LDS: cyber attack manifestations for automatic interpretation of system logs and security alerts." *International Journal of Information Security*, vol. 25, art. 148, 2026. DOI: https://doi.org/10.1007/s10207-026-01318-x; arXiv: https://arxiv.org/abs/2603.04186.',
    ),
    (
        "[9]",
        'Okuma, M.; Watarai, K.; Okada, S.; Mitsunaga, T. "Automated Mapping Method for Sysmon Logs to ATT&CK Techniques by Leveraging Atomic Red Team." In: *2023 6th International Conference on Signal Processing and Information Security (ICSPIS 2023)*, pp. 104–109, IEEE, 2023. DOI: https://doi.org/10.1109/ICSPIS60075.2023.10343783.',
    ),
    (
        "[10]",
        'Adediran, G.; Awuson-David, K.; Ahmed, Y. "Retrieval-Augmented Large Language Model for AWS Cloud Threat Detection and Modelling: Cloudtrail Mitre ATT&CK Mapping." *Computers, Materials & Continua*, vol. 87, no. 2, art. 100, 2026. DOI: https://doi.org/10.32604/cmc.2026.077606.',
    ),
    (
        "[11]",
        'Lupinacci, M.; Arena, L.; Blefari, F.; Furfaro, A. "A Graph-Based Approach for Mapping Kernel-Level Telemetry to MITRE ATT&CK." *arXiv preprint* arXiv:2609.12841, 2026. Available: https://arxiv.org/abs/2609.12841.',
    ),
    (
        "[12]",
        'Gwak, J.-Y.; Strier, A.; Xi, Z.; Yan, G.; Shu, X.; Stoller, S. D.; Yang, P. "LADE: LLM-Assisted Advanced Persistent Threat Detection and Explanation." In: *Security and Privacy in Communication Networks (SecureComm 2026)*, Lecture Notes of the Institute for Computer Sciences, Social Informatics and Telecommunications Engineering, vol. 705, pp. 245–273, Springer Cham, 2026. DOI: https://doi.org/10.1007/978-3-032-32767-3_11; Available: https://www3.cs.stonybrook.edu/~stoller/papers/LADE-2026.pdf.',
    ),
    (
        "[13]",
        'Mozaffari, M.; Yazdinejad, A.; Dehghantanha, A. "Windows-APT 2025: A dataset for APT-inspired attack scenarios on windows systems." *Data in Brief*, vol. 65, art. 112569, 2026. DOI: https://doi.org/10.1016/j.dib.2026.112569; Mendeley Data v3: https://doi.org/10.17632/b8fmtzvpy8.3.',
    ),
]


def find_paragraph_by_exact_or_prefix(doc: docx.Document, target: str, start_idx: int = 148):
    """Locate a paragraph in the template section (P148 onwards) matching text."""
    for i in range(start_idx, len(doc.paragraphs)):
        p = doc.paragraphs[i]
        t = p.text.strip()
        if t == target.strip() or t.startswith(target.strip()):
            return i, p
    raise ValueError(f"Could not find paragraph matching {target!r} starting from P{start_idx}")


def populate_thesis_template(template_path: Path, out_paths: list[Path], pdf_out_path: Path):
    """Load the untouched backup template, apply all review fixes, and populate all sections."""
    CursorInserter._bm_counter = 500
    doc = docx.Document(str(template_path))

    # Configure footer page numbering (Page X of Y) and suppress footer on Page 1 (Cover Page)
    for section in doc.sections:
        section.different_first_page_header_footer = True
        first_footer = section.first_page_footer
        first_footer.is_linked_to_previous = False
        for pf in first_footer.paragraphs:
            pf.text = ""
        first_header = section.first_page_header
        first_header.is_linked_to_previous = False
        for ph in first_header.paragraphs:
            ph.text = ""

        footer = section.footer
        p_footer = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        p_footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_footer.text = ""
        p_footer.paragraph_format.space_before = Pt(0)
        p_footer.paragraph_format.space_after = Pt(0)
        r_left = p_footer.add_run("HOD402 — RAG2ATT&CK (SE196277)   |   Page ")
        r_left.font.name = FONT_FAMILY
        r_left.font.size = Pt(9.5)
        r_left.font.color.rgb = RGBColor(0x57, 0x60, 0x6A)
        p_footer._element.append(
            parse_xml(
                f'<w:fldSimple {nsdecls("w")} w:instr="PAGE">'
                f'<w:r><w:rPr><w:rFonts w:ascii="{FONT_FAMILY}" w:hAnsi="{FONT_FAMILY}"/><w:sz w:val="19"/><w:color w:val="57606A"/></w:rPr><w:t>1</w:t></w:r>'
                f"</w:fldSimple>"
            )
        )
        r_mid = p_footer.add_run(" of ")
        r_mid.font.name = FONT_FAMILY
        r_mid.font.size = Pt(9.5)
        r_mid.font.color.rgb = RGBColor(0x57, 0x60, 0x6A)
        p_footer._element.append(
            parse_xml(
                f'<w:fldSimple {nsdecls("w")} w:instr="NUMPAGES">'
                f'<w:r><w:rPr><w:rFonts w:ascii="{FONT_FAMILY}" w:hAnsi="{FONT_FAMILY}"/><w:sz w:val="19"/><w:color w:val="57606A"/></w:rPr><w:t>1</w:t></w:r>'
                f"</w:fldSimple>"
            )
        )

    # Fix numbering start values for Chapter 5 (abstractNumId=6 -> start=5) and Chapter 6 (abstractNumId=28 -> start=6)
    num_el = doc.part.numbering_part.element
    for aid, new_start in [("6", "5"), ("28", "6")]:
        for abs_num in num_el.findall(qn("w:abstractNum")):
            if abs_num.get(qn("w:abstractNumId")) == aid:
                for lvl in abs_num.findall(qn("w:lvl")):
                    if lvl.get(qn("w:ilvl")) == "0":
                        start_el = lvl.find(qn("w:start"))
                        if start_el is not None:
                            start_el.set(qn("w:val"), new_start)

    # Review Point 4: Fix grammatical headings & remove template instructional remnants while preserving XML styles
    # P216: Contribution of Research -> Research Contributions
    if doc.paragraphs[216].runs:
        doc.paragraphs[216].runs[0].text = "Research Contributions"
        for r in doc.paragraphs[216].runs[1:]:
            r.text = ""
    # P218: CHAPTER 3\nMETHODOLOGY -> CHAPTER 3 \nMETHODOLOGY
    if doc.paragraphs[218].runs and doc.paragraphs[218].runs[0].text == "CHAPTER 3":
        doc.paragraphs[218].runs[0].text = "CHAPTER 3 "
    # P220: Research Design trailing space
    if len(doc.paragraphs[220].runs) > 1 and doc.paragraphs[220].runs[1].text == " ":
        doc.paragraphs[220].runs[1].text = ""
    # P222: Sampling Data Analysis Techniques -> Sampling and Data Analysis Techniques
    if doc.paragraphs[222].runs:
        doc.paragraphs[222].runs[0].text = "Sampling and Data Analysis Techniques"
        for r in doc.paragraphs[222].runs[1:]:
            r.text = ""
    # P225: EXPERIMENTAL AND RESULTS -> EXPERIMENTS AND RESULTS
    for r in doc.paragraphs[225].runs:
        if "EXPERIMENTAL AND RESULTS" in r.text:
            r.text = r.text.replace("EXPERIMENTAL AND RESULTS", "EXPERIMENTS AND RESULTS")
    # P236: Restate the Research Problem or Objectives -> Research Objectives Revisited
    if doc.paragraphs[236].runs and doc.paragraphs[236].runs[0].text == " ":
        doc.paragraphs[236]._p.remove(doc.paragraphs[236].runs[0]._r)
    if doc.paragraphs[236].runs:
        doc.paragraphs[236].runs[0].text = "Research Objectives Revisited"
        for r in doc.paragraphs[236].runs[1:]:
            r.text = ""
    # P237: Summarize Key Findings -> Summary of Key Findings
    if doc.paragraphs[237].runs and doc.paragraphs[237].runs[0].text == " ":
        doc.paragraphs[237]._p.remove(doc.paragraphs[237].runs[0]._r)
    if doc.paragraphs[237].runs:
        doc.paragraphs[237].runs[0].text = "Summary of Key Findings"
        for r in doc.paragraphs[237].runs[1:]:
            r.text = ""
    # P249: APPENDICES (If any) -> APPENDICES
    if doc.paragraphs[249].runs:
        doc.paragraphs[249].runs[0].text = "APPENDICES"
        for r in doc.paragraphs[249].runs[1:]:
            r.text = ""

    # Enforce keep_with_next on all template headings & subheadings, and page_break_before on all Heading 1s
    for idx_h in range(158, len(doc.paragraphs)):
        p_h = doc.paragraphs[idx_h]
        st_name = p_h.style.name if p_h.style else ""
        if st_name in ("Heading 1", "List Paragraph"):
            p_h.paragraph_format.keep_with_next = True
        if st_name == "Heading 1":
            p_h.paragraph_format.page_break_before = True

    # Capture template instructional elements and standalone empty page-break paragraphs to remove cleanly
    body_el = doc.element.body
    cover_tbl0 = doc.tables[0]._tbl
    prefix_elements = []
    for child in list(body_el):
        if child is cover_tbl0:
            break
        prefix_elements.append(child)

    sample_table_3 = doc.tables[3]._tbl
    instructional_paragraph_indices = (
        [151, 152, 153, 154, 155, 156, 157]  # All trailing Cover Page empty paragraphs so Page 1 fits cleanly
        + [159, 160, 161]  # Abstract instructional text
        + [164, 165, 166]  # Acknowledgement instructional text + standalone page break
        + [167, 168, 169]  # TOC tips URL + standalone page break before LOF
        + list(range(171, 180))  # Sample List of Figures & sample Figure 1 + blogdaytinhoc URL
        + list(range(181, 190))  # Sample List of Tables & sample Table 1 caption + mytour URL
        + list(range(191, 203))  # Sample tab-separated Abbreviations list
        + [204, 211, 213, 217, 219, 224, 226, 233, 235, 238, 240, 243, 244]  # Chapter 1-6 instructional descriptions & standalone page-break paragraphs
        + [246, 247, 248]  # References instructional text & standalone page break
        + [250, 251]  # Appendices instructional text
    )
    instructional_paragraphs = [doc.paragraphs[i]._p for i in instructional_paragraph_indices]

    # ==========================================================================
    # 1. COVER PAGE (Table 0, Table 1, Nested Table in Table 1 [4,0], Table 2)
    # ==========================================================================
    t1 = doc.tables[1]
    p_title = t1.cell(2, 0).paragraphs[0]
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.text = ""
    r_t_lbl = p_title.add_run("Thesis Title:\n")
    r_t_lbl.font.name = FONT_FAMILY
    r_t_lbl.font.size = Pt(14)
    r_t_lbl.bold = True
    r_t_val = p_title.add_run(
        "Evaluating MITRE ATT&CK-Grounded RAG for Technique Attribution from Windows Endpoint Logs: A Replication-and-Extension Study"
    )
    r_t_val.font.name = FONT_FAMILY
    r_t_val.font.size = Pt(15.5)
    r_t_val.bold = True

    # Trim extra blank spacing inside Cover Page Table 1 cells so Table 2 (- Hanoi, October/2026 -) stays on Page 1
    for r_idx in (0, 1, 3):
        for p_c in t1.cell(r_idx, 0).paragraphs:
            p_c.paragraph_format.space_before = Pt(0)
            p_c.paragraph_format.space_after = Pt(0)

    nt = t1.cell(4, 0).tables[0]
    p_sname = nt.cell(0, 1).paragraphs[0]
    p_sname.text = ""
    r_sn1 = p_sname.add_run("Student’s name: ")
    r_sn1.font.name = FONT_FAMILY
    r_sn1.font.size = Pt(12)
    r_sn1.bold = True
    r_sn2 = p_sname.add_run("Hà Hoàng Bách")
    r_sn2.font.name = FONT_FAMILY
    r_sn2.font.size = Pt(12)
    r_sn2.bold = False

    # Review Point 4: Fix typo "Student’ ID:" -> "Student’s ID:"
    p_sid = nt.cell(0, 2).paragraphs[0]
    p_sid.text = ""
    r_id1 = p_sid.add_run("Student’s ID: ")
    r_id1.font.name = FONT_FAMILY
    r_id1.font.size = Pt(12)
    r_id1.bold = True
    r_id2 = p_sid.add_run("SE196277")
    r_id2.font.name = FONT_FAMILY
    r_id2.font.size = Pt(12)
    r_id2.bold = False

    p_sup = nt.cell(1, 1).paragraphs[0]
    p_sup.text = ""
    r_sp1 = p_sup.add_run("Supervisor’s Name: ")
    r_sp1.font.name = FONT_FAMILY
    r_sp1.font.size = Pt(12)
    r_sp1.bold = True
    r_sp2 = p_sup.add_run("Hồ Hải")
    r_sp2.font.name = FONT_FAMILY
    r_sp2.font.size = Pt(12)
    r_sp2.bold = False

    p_cpcode = nt.cell(2, 1).paragraphs[0]
    p_cpcode.text = ""
    r_cp = p_cpcode.add_run("HOD402 — RAG2ATTCK (Release v1.0.0-rag2attck-study)")
    r_cp.font.name = FONT_FAMILY
    r_cp.font.size = Pt(12)
    r_cp.bold = True

    # Table 2 Row 0: - Hanoi, October/2026 - and remove trailing empty Row 1
    t2 = doc.tables[2]
    if len(t2.rows) > 1:
        t2._tbl.remove(t2.rows[1]._tr)
    p_loc = t2.cell(0, 0).paragraphs[0]
    p_loc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_loc.paragraph_format.space_before = Pt(0)
    p_loc.paragraph_format.space_after = Pt(0)
    p_loc.text = ""
    r_loc = p_loc.add_run("- Hanoi, October/2026 -")
    r_loc.font.name = FONT_FAMILY
    r_loc.font.size = Pt(13)
    r_loc.bold = True

    # ==========================================================================
    # 2. ABSTRACT & KEYWORDS (P158..P162) — Review Points 1.1 & 1.5 Fixed
    # ==========================================================================
    _, p_abs_heading = find_paragraph_by_exact_or_prefix(doc, "ABSTRACT", start_idx=155)
    p_abs_heading.paragraph_format.page_break_before = True
    ins_abs = CursorInserter(doc, p_abs_heading._p)
    ins_abs.add_p(
        text=(
            "Attributing endpoint telemetry to standardized adversary behaviors in the MITRE Adversarial Tactics, Techniques, and Common Knowledge framework is a foundational task in security operations centers and cyber threat intelligence. While modern large language models possess broad parametric knowledge, direct zero-shot prompting without external grounding risks hallucinated technique identifiers, temporal obsolescence, and unverified decisions. Retrieval-Augmented Generation grounds model reasoning in curated external knowledge, yet prior evaluations remain fragmented across unstructured threat reports, cloud or Linux logs, unpinned knowledge bases, and conflated retrieval versus output cutoffs. "
            "This study conducts a controlled replication-and-extension evaluation of knowledge-grounded retrieval augmentation for exact technique and sub-technique attribution from Windows endpoint logs under a cryptographically frozen protocol. Our design enforces strict symmetry between an unaugmented baseline and retrieval-augmented conditions across candidate depths of one, three, five, and ten retrieved documents using a fixed reasoning model alias and a dense vector index over 474 active Windows techniques from Enterprise Matrix version 19.2. Across five conditions evaluated over 1,280 synthetic paired test views (6,400 logical inference requests; 6,401 physical attempts), attribution metrics on the 718 mapped, scorable views (excluding 311 ambiguous and 251 unmapped views) show that the unaugmented baseline achieves 77.99 percent end-to-end accuracy and 0.012608 macro-averaged F1 across 474 classes, whereas retrieval augmentation at depth ten achieves 79.53 percent accuracy (an observed difference of plus 1.532 percentage points, nominal 95 percent cluster-bootstrap confidence interval from minus 2.355 to plus 5.300 percentage points, unclustered exact McNemar probability value 0.4219) and 0.014024 macro-averaged F1 (a difference of plus 0.001415, nominal 95 percent cluster-bootstrap confidence interval from plus 0.001011 to plus 0.001792), showing no statistically significant accuracy difference alongside a positive confidence interval on sparse 474-class macro-averaged F1. "
            "Independent failure decomposition shows that 80.95 percent of classification errors at depth ten (119 of 147 errors) co-occur with retrieval misses (a 55.29 percent miss rate), where accuracy is 91.28 percent when retrieved versus 70.03 percent when absent, motivating retrieval-focused improvements."
        ),
        font_size=BODY_FONT_SIZE,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_before=6,
        space_after=6,
    )

    _, p_kw = find_paragraph_by_exact_or_prefix(doc, "Keywords:")
    p_kw.text = ""
    p_kw.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_kw.paragraph_format.space_before = Pt(4)
    p_kw.paragraph_format.space_after = Pt(6)
    p_kw.paragraph_format.line_spacing = 1.15
    r_kw_lbl = p_kw.add_run("Keywords: ")
    r_kw_lbl.font.name = FONT_FAMILY
    r_kw_lbl.font.size = BODY_FONT_SIZE
    r_kw_lbl.bold = True
    r_kw = p_kw.add_run(
        "MITRE ATT&CK Enterprise v19.2; Retrieval-Augmented Generation (RAG); Large Language Models (LLMs); Windows Endpoint Telemetry; Sysmon Event Logs; Threat Technique Attribution; Security Operations Center (SOC); Dense Vector Retrieval (FAISS); Replication-and-Extension Study; Reproducible Cybersecurity Evaluation."
    )
    r_kw.font.name = FONT_FAMILY
    r_kw.font.size = BODY_FONT_SIZE
    r_kw.bold = False

    # ==========================================================================
    # 3. ACKNOWLEDGEMENT (P163..P165)
    # ==========================================================================
    _, p_ack_heading = find_paragraph_by_exact_or_prefix(doc, "ACKNOWLEDGEMENT", start_idx=160)
    p_ack_heading.paragraph_format.page_break_before = True
    ins_ack = CursorInserter(doc, p_ack_heading._p)
    ins_ack.add_p(
        text=(
            "First and foremost, I would like to express my sincere gratitude to the Board of Rectors and the Faculty of Information Assurance at **FPT University** for establishing a rigorous academic environment and providing the foundational knowledge in network security, incident response, and security project management required to undertake this research thesis in course **HOD402**."
        ),
    )
    ins_ack.add_p(
        text=(
            "I extend my deepest appreciation to my Supervisor, **Mr. Hồ Hải**, for his dedicated guidance, critical methodological feedback, and unwavering insistence on scientific rigor throughout the eight-week research cycle. His emphasis on controlled experimental design, anti-label-leakage verification, and honest reporting of statistical uncertainty shaped the core architecture of the **RAG2ATT&CK** study."
        ),
    )
    p_ack_last = ins_ack.add_p(
        text=(
            "Finally, I would like to thank the members of the Capstone Project Evaluation Committee for their time, insightful review, and constructive assessment of this thesis, as well as my family and peers at FPT University for their continuous encouragement and support."
        ),
    )
    # Put a page break at the end of the last Acknowledgement paragraph so TOC (w:sdt) starts on Page 4
    p_ack_last.runs[-1]._r.append(parse_xml(f'<w:br {nsdecls("w")} w:type="page"/>'))

    # ==========================================================================
    # 4. LIST OF FIGURES (P170..P179)
    # ==========================================================================
    _, p_lof_heading = find_paragraph_by_exact_or_prefix(doc, "LIST OF FIGURES", start_idx=168)
    p_lof_heading.paragraph_format.page_break_before = True
    ins_lof = CursorInserter(doc, p_lof_heading._p)
    lof_entries = [
        ("Figure 1. Dual-View Attribution Architecture (CTI Log -> all-MiniLM-L6-v2 -> FAISS -> gpt-5.6-luna xhigh) — Chapter 3, Section 3.1", "_Ref_fig_1"),
        ("Figure 2. Attribution Accuracy vs. Candidate Depth k across Conditions (N=718 Scorable Views with 95% Bootstrap CI) — Chapter 4, Section 4.2", "_Ref_fig_2"),
        ("Figure 3. 474-Class Macro-F1 Performance across Retrieval Depths (8 Active Supported Classes vs. 466 Zero-Support Universe Classes) — Chapter 4, Section 4.2", "_Ref_fig_3"),
        ("Figure 4. Standalone Retrieval Hit@k vs. Multi-Label Macro Recall@k across Depths k=1, 3, 5, 10 on 718 Scorable TEST Views — Chapter 4, Section 4.2", "_Ref_fig_4"),
        ("Figure 5. Post-Retrieval Stratum Accuracy: P(Correct | Hit) vs. P(Correct | Miss) across Retrieval Depths — Chapter 4, Section 4.2", "_Ref_fig_5"),
        ("Figure 6. Request Inference Latency Scaling: Mean and Median Duration (ms) across Conditions (P95 Withheld per Protocol) — Chapter 4, Section 4.2", "_Ref_fig_6"),
        ("Figure 7. Conservative Ledger Spend vs. Token-Usage Cost (USD) and Aggregate Input Token Volume — Chapter 4, Section 4.2", "_Ref_fig_7"),
        ("Figure 8. Decoupled Independent Failure Decomposition and Co-occurrence Breakdown at Retrieval Depth k=10 — Chapter 4, Section 4.2", "_Ref_fig_8"),
    ]
    for entry_text, bm_name in lof_entries:
        ins_lof.add_toc_ref_item("•", entry_text, bm_name=bm_name, hanging_in=0.25)

    # ==========================================================================
    # 5. LIST OF TABLES (P180..P189) — Review Point 5.3 Sequential Table 1..14
    # ==========================================================================
    _, p_lot_heading = find_paragraph_by_exact_or_prefix(doc, "LIST OF TABLES", start_idx=175)
    p_lot_heading.paragraph_format.page_break_before = True
    ins_lot = CursorInserter(doc, p_lot_heading._p)
    lot_entries = [
        ("Table 1. Canonical Research Questions, Hypotheses, Experimental Variables, and Evaluation Metrics — Chapter 1, Section 1.3", "_Ref_tbl_1"),
        ("Table 2. Multi-Dimensional Comparator Matrix Grounded in Primary Evidence (Part 1: Comparators 1–4) — Chapter 2, Section 2.2", "_Ref_tbl_2"),
        ("Table 3. Multi-Dimensional Comparator Matrix Grounded in Primary Evidence (Part 2: Comparators 5–8 and RAG2ATT&CK) — Chapter 2, Section 2.2", "_Ref_tbl_3"),
        ("Table 4. Primary Attribution Performance, 474-Class Macro-F1 Bootstrap CIs, and Ground-Truth Complexity — Chapter 4, Section 4.2", "_Ref_tbl_4"),
        ("Table 5. Attribution Diagnostic Metrics Across Experimental Conditions — Chapter 4, Section 4.2", "_Ref_tbl_5"),
        ("Table 6. Representation Stratification: Single-Event vs. Contextual-Event Views — Chapter 4, Section 4.2", "_Ref_tbl_6"),
        ("Table 7. Paired Scorable Representation Concordance and Unclustered McNemar Discordance (N=278 complete pairs) — Chapter 4, Section 4.2", "_Ref_tbl_7"),
        ("Table 8. Decoupled Failure Decomposition Matrix Across Independent Diagnostic Axes (D2i) — Chapter 4, Section 4.2", "_Ref_tbl_8"),
        ("Table 9. Resource Consumption, Latency Scaling, Token-Usage Cost, and Conservative Ledger Spend — Chapter 4, Section 4.2", "_Ref_tbl_9"),
        ("Table 10. Whole-Study Financial Ledger and Budget Reconciliation — Chapter 4, Section 4.2", "_Ref_tbl_10"),
        ("Table 11. Cryptographic Reproducibility Manifest — Appendix A", "_Ref_tbl_11"),
        ("Table 12. Supplementary Execution Provenance (Canonical Run Mode) — Appendix A", "_Ref_tbl_12"),
        ("Table 13. Eight-Week Capstone Implementation Roadmap: Planned Window vs. Actual Execution Timestamps — Appendix B", "_Ref_tbl_13"),
        ("Table 14. Risk Register, Severity Assessment, and Reproducibility Mitigation Controls — Appendix B", "_Ref_tbl_14"),
    ]
    for entry_text, bm_name in lot_entries:
        ins_lot.add_toc_ref_item("•", entry_text, bm_name=bm_name, hanging_in=0.25)

    # ==========================================================================
    # 6. ABBREVIATIONS (P190..P202)
    # ==========================================================================
    _, p_abbr_heading = find_paragraph_by_exact_or_prefix(doc, "ABBREVIATIONS", start_idx=185)
    p_abbr_heading.paragraph_format.page_break_before = True
    ins_abbr = CursorInserter(doc, p_abbr_heading._p)
    abbr_rows = [
        ["Acronym", "Full Meaning & Technical Context in RAG2ATT&CK"],
        ["AI / ML / NLP", "Artificial Intelligence / Machine Learning / Natural Language Processing"],
        ["APT", "Advanced Persistent Threat"],
        ["ATT&CK", "Adversarial Tactics, Techniques, and Common Knowledge (MITRE Enterprise Matrix v19.2)"],
        ["BM25", "Best Matching 25 (Lexical bag-of-words retrieval ranking function)"],
        ["CI", "Confidence Interval (95% Cluster Bootstrap over 440 scenario clusters) / Continuous Integration"],
        ["CP / HOD402 / OJT", "Capstone Project / Course HOD402 / On-the-Job Training (FPT University)"],
        ["CTI", "Cyber Threat Intelligence"],
        ["DEV / TEST", "Development Split (30 pairs / 60 views) / Canonical Test Split (640 pairs / 1,280 views; 718 scorable)"],
        ["eBPF", "Extended Berkeley Packet Filter (Linux kernel telemetry comparator)"],
        ["EDR / SIEM", "Endpoint Detection and Response / Security Information and Event Management"],
        ["FAISS", "Facebook AI Similarity Search (`IndexFlatIP` exact inner-product vector index)"],
        ["FN / FP / TP", "False Negative / False Positive / True Positive"],
        ["FWER", "Family-Wise Error Rate"],
        ["GT", "Ground Truth (`single-GT` = 1 technique; `multi-GT` = multiple concurrent techniques)"],
        ["Hit@k / Recall@k", "Sample-Level Any-Hit Rate ($\\text{Hit@}k$, `ANY_GT_RETRIEVED`) vs. Fractional Multi-Label $\\text{Macro Recall@}k$"],
        ["HR / MAP / MRR / NDCG", "Hit Rate / Mean Average Precision / Mean Reciprocal Rank / Normalized Discounted Cumulative Gain"],
        ["IA / IDS", "Information Assurance / Intrusion Detection System"],
        ["JSON / XML", "JavaScript Object Notation / Extensible Markup Language"],
        ["KB", "Knowledge Base (474 active Windows ATT&CK techniques & sub-techniques)"],
        ["LADE", "LLM-Assisted Advanced Persistent Threat Detection and Explanation (Gwak et al., 2026/2027)"],
        ["LLM", "Large Language Model (Fixed OpenAI `gpt-5.6-luna` alias with `reasoning_effort=xhigh`)"],
        ["LOLBin", "Living-Off-The-Land Binary (e.g., `certutil.exe`, `wevtutil.exe`, `schtasks.exe`)"],
        ["MMR", "Maximal Marginal Relevance"],
        ["OMML / SDT", "Office Math Markup Language / Structured Document Tag (OpenXML)"],
        ["RAG", "Retrieval-Augmented Generation"],
        ["RQ", "Research Question (RQ1: Efficacy; RQ2: Retrieval & Failure Axes; RQ3: Depth/Cost/Latency)"],
        ["SHA-256", "Secure Hash Algorithm 256-bit cryptographic digest"],
        ["SOC", "Security Operations Center"],
        ["STIX", "Structured Threat Information Expression (JSON schema for MITRE ATT&CK v19.2)"],
        ["Sysmon", "Microsoft Windows System Monitor (Event IDs 1, 3, 7, 12, 13, etc.)"],
        ["TTP", "Tactics, Techniques, and Procedures"],
    ]
    ins_abbr.add_table(
        "Summary of Domain Abbreviations and Technical Acronyms in RAG2ATT&CK.",
        abbr_rows,
        table_id="table_abbr",
        custom_widths=[1.80, 4.70],
        caption_style="Normal",
        add_page_break_after=False,
    )

    # ==========================================================================
    # 7. CHAPTER 1: INTRODUCTION (P203..P210)
    # ==========================================================================
    _, p_1_1 = find_paragraph_by_exact_or_prefix(doc, "Background", start_idx=203)
    ins_1_1 = CursorInserter(doc, p_1_1._p)
    ins_1_1.add_callout(
        "Canonical Study Provenance & Scope Binding",
        "Bound to `canonical-metric-bundle-v2` (SHA-256: `442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34`), Terminal Run Seal `ae7a9ada86927a79e0c6916b44d3f0ba9e1f9756df55dd7b2fce712b35d48701` (`run_id=live-66b94b1676bf46a9`), Protocol `experiment-protocol-v1.1` (`d3bf3d31...`), and Official Release `v1.0.0-rag2attck-study` (`ca8d39824a72e80053371e208506bfdc6332dc5d`). All empirical claims are strictly bounded to the `synthetic-paired-v1` benchmark; generalization to production enterprise telemetry remains unproven.",
    )
    ins_1_1.add_p(
        text=(
            "Enterprise defense relies heavily on the ingestion, processing, and interpretation of host endpoint telemetry. System instrumentation tools—such as Microsoft Sysmon and native Windows Security Event Auditing—record granular operating system activity, including process creation (`Event ID 1` / `4688`), network connections (`Event ID 3`), image loading (`Event ID 7`), registry modifications (`Event IDs 12/13`), service installations (`Event ID 4697`), user account management (`Event ID 4720`), and event log clearing (`Event ID 1102`). Security Operations Center (SOC) analysts and incident response teams continuously triage these log streams to detect malicious behavior and perform *threat attribution*: mapping discrete host observables to standardized adversary Tactics, Techniques, and Procedures (TTPs) defined in the MITRE ATT&CK framework [1]."
        ),
    )
    ins_1_1.add_p(
        text=(
            "Accurate ATT&CK mapping enables automated playbooks, contextualized threat hunting, kill-chain reconstruction, and cross-organization cyber threat intelligence (CTI) sharing. However, manual attribution at the exact sub-technique level (`Txxxx.yyy`) is labor-intensive and cognitively demanding. An adversary executing a living-off-the-land binary (LOLBin) like `certutil.exe` might be staging tools from an external server (Ingress Tool Transfer: `T1105`) or decoding payloads locally (Deobfuscate/Decode Files or Information: `T1140`). Disambiguating these nuanced attacker goals requires deep domain knowledge, familiarity with command-line syntax, and comprehensive command of the evolving ATT&CK taxonomy."
        ),
    )
    ins_1_1.add_p(
        text=(
            "Originally initiated from the broad capstone theme *\"AI Assistant for Classifying and Mapping Attack Techniques According to the MITRE ATT&CK Framework from System Logs\"* (*Trợ lý AI phân loại và ánh xạ kỹ thuật tấn công theo khung MITRE ATT&CK từ log hệ thống*), systematic literature screening revealed that while foundation reasoning models [2, 3] and Retrieval-Augmented Generation (RAG) [4] have been widely applied to unstructured CTI report annotation [5, 6], controlled evaluations on endpoint telemetry remain scarce. Consequently, this thesis was formally refined into **RAG2ATT&CK**: a controlled conceptual replication-and-extension empirical study that isolates the exact effect of MITRE ATT&CK-grounded RAG [4] on Windows endpoint log technique attribution under a cryptographically frozen scientific protocol."
        ),
    )

    # 1.2. Problem Statement (P206) — Review Point 3 Fixed (TargetUserName/SubjectUserName instead of SamAccountName)
    _, p_1_2 = find_paragraph_by_exact_or_prefix(doc, "Problem Statement", start_idx=203)
    ins_1_2 = CursorInserter(doc, p_1_2._p)
    ins_1_2.add_p(
        text=(
            "Commercial foundation models with extended internal reasoning capabilities (such as OpenAI's `gpt-5.6-luna` [2, 3]) provide native structured output enforcement and multi-step reasoning over dense technical context. Nevertheless, relying solely on an unaugmented LLM's internal parametric memory (`No-RAG`) or deploying naive retrieval pipelines introduces four critical scientific and operational problems:"
        ),
    )
    ins_1_2.add_numbered_item(
        "1.",
        "**Parametric Hallucination, Invalid Identifiers, and Knowledge Obsolescence:** Without external grounding, LLMs may synthesize non-existent technique identifiers (such as `T1543.006`, which is absent from the Enterprise ATT&CK taxonomy) or confuse platform scopes by assigning non-Windows techniques (such as Cloud API: `T1059.009`, an active cloud technique in ATT&CK v19.2 inapplicable to Windows hosts). Furthermore, static model weights cannot reflect quarterly ATT&CK updates, revocations, or deprecations, and lack auditable citations back to official procedure descriptions.",
    )
    ins_1_2.add_numbered_item(
        "2.",
        "**Lexical and Representation Gap Between Raw Endpoint Telemetry and ATT&CK Prose:** Prior ATT&CK RAG systems (such as TechniqueRAG [5] and H-TechniqueRAG [6]) operate on human-written CTI reports that share rich natural-language vocabulary with MITRE ATT&CK descriptions. In contrast, Windows endpoint telemetry consists of structured, terse execution fields (`CommandLine`, `ParentImage`, `TargetObject`, `ServiceFileName`, and Windows Security Event XML attributes such as `TargetUserName`, `SubjectUserName`, and `SubjectLogonId`), creating a severe semantic representation gap for standard dense bi-encoder retrievers.",
    )
    ins_1_2.add_numbered_item(
        "3.",
        "**Methodological Fragmentation and Conflation of Retriever Depth ($k$):** Prior telemetry studies either focus on binary process-tree behavior detection without exact sub-technique IDs (Yang & Hsu [7]), omit RAG entirely during command-log interpretation (CAM-LDS [8]), provide bibliographic-only Sysmon mappings without verified retrieval controls (Okuma et al. [9]), evaluate non-Windows environments without ablating retriever depth (AWS CloudTrail RAG [10], Linux eBPF Trace2ATT&CK [11]), or conflate the length of the model's emitted candidate list (`Top-k` output cutoff) with the depth of the external retrieval engine ($k$) (LADE [12]).",
    )
    ins_1_2.add_numbered_item(
        "4.",
        "**Entangled Upstream Retrieval Misses vs. Downstream Generation Errors:** Existing end-to-end evaluations rarely decouple upstream retrieval misses ($Y_i \\cap R_{i,k} = \\emptyset$) from downstream LLM selection discrepancies ($Y_i \\cap R_{i,k} \\neq \\emptyset \\land \\hat{y}_i \\notin Y_i$), leaving security engineers unable to determine how classification errors co-occur across the vector index versus the reasoning model.",
    )

    # 1.3. Research Objectives (P207) — Review Points 1.1, 1.4, 5.3 Fixed (Table 1)
    _, p_1_3 = find_paragraph_by_exact_or_prefix(doc, "Research Objectives", start_idx=203)
    ins_1_3 = CursorInserter(doc, p_1_3._p)
    ins_1_3.add_p(
        text=(
            "The primary objective of this study is to execute a strictly controlled, reproducible empirical evaluation comparing unaugmented zero-shot reasoning (**No-RAG**) against MITRE ATT&CK-grounded **RAG** across systematic retrieval depths ($k \\in \\{1, 3, 5, 10\\}$) for exact Windows technique attribution. Specifically, the research is governed by three canonical Research Questions (**RQ1–RQ3**) and corresponding hypotheses (**H1–H3**):"
        ),
    )
    ins_1_3.add_bullet(
        "**RQ1 (Retrieval-Augmented Attribution Efficacy):** Does grounding a reasoning LLM (`gpt-5.6-luna`, `reasoning_effort=xhigh`) in retrieved MITRE ATT&CK v19.2 enterprise reference context improve exact technique and sub-technique attribution accuracy and 474-class Macro-F1 over a strictly matched No-RAG baseline under identical reasoning settings?"
    )
    ins_1_3.add_bullet(
        "**RQ2 (Retrieval Quality and Failure Axes):** When attribution errors occur under RAG, how do upstream retrieval misses ($Y_i \\cap R_{i,k} = \\emptyset$) and downstream model selection discrepancies ($Y_i \\cap R_{i,k} \\neq \\emptyset \\land \\hat{y}_i \\notin Y_i$) manifest across independent measurement axes with overlaps? Furthermore, how do single-event versus multi-event contextual representations correlate with standalone $\\text{Hit@}k$, multi-label $\\text{Macro Recall@}k$, and downstream accuracy?"
    )
    ins_1_3.add_bullet(
        "**RQ3 (Retrieval Depth, API Cost, and Latency Trade-Offs):** How does varying retrieval candidate depth ($k \\in \\{1, 3, 5, 10\\}$) affect attribution performance, context distractor susceptibility, wall-clock inference latency, token-usage cost, and conservative ledger spend under a hard USD 19.99 financial guard?"
    )
    ins_1_3.add_table(
        "Table 1: Canonical Research Questions, Hypotheses, Experimental Variables, and Evaluation Metrics.",
        TABLE_1_RQ,
        table_id="table_1",
        bm_name="_Ref_tbl_1",
        custom_widths=[0.42, 1.45, 1.08, 0.88, 0.85, 0.80, 1.02],
    )

    # 1.4. Significance of the Study (P208) — Review Point 1.3 Fixed (Fixed alias & inference settings)
    _, p_1_4 = find_paragraph_by_exact_or_prefix(doc, "Significance of the Study", start_idx=203)
    ins_1_4 = CursorInserter(doc, p_1_4._p)
    ins_1_4.add_p(
        text=(
            "To maintain strict scientific integrity, **RAG2ATT&CK does not claim global novelty** for applying RAG to MITRE ATT&CK [5, 6], analyzing Windows Sysmon logs with LLMs [7, 8, 9], comparing RAG against a No-RAG baseline [10, 11], or evaluating Top-$k$ trade-offs in isolation [6]. Instead, the significance of this thesis lies in its **controlled conceptual replication-and-extension design** that unites six rigorous experimental controls never simultaneously enforced in prior literature:"
        ),
    )
    ins_1_4.add_numbered_item("1.", "**Symmetric Controlled Contrast:** Comparing No-RAG and RAG using the identical requested model alias (`gpt-5.6-luna`), identical reasoning settings (`reasoning_effort=xhigh`, `max_output_tokens=8192`), and a byte-identical prompt template (`prompts/baseline_v1.txt`), isolating retrieved context as the sole treatment variable.")
    ins_1_4.add_numbered_item("2.", "**Pinned ATT&CK Enterprise Matrix v19.2:** Binding all retrieval and scoring operations to an immutable STIX snapshot of 474 active Windows techniques and sub-techniques, eliminating taxonomy drift.")
    ins_1_4.add_numbered_item("3.", "**Independent Failure Measurement Axes (Protocol D2i):** Decoupling upstream retrieval misses from downstream LLM selection discrepancies without forced mutually exclusive partitioning, while distinguishing sample-level $\\text{Hit@}k$ from fractional multi-label $\\text{Macro Recall@}k$.")
    ins_1_4.add_numbered_item("4.", "**Systematic Retriever Depth Ablation ($k \\in \\{1, 3, 5, 10\\}$):** Strictly separating external retriever depth $k$ from single-ID output prediction (`{\"technique_id\": \"...\"}`).")
    ins_1_4.add_numbered_item("5.", "**Paired Single-Event vs. Contextual-Event Evaluation:** Testing how multi-event telemetry windows correlate with dense retrieval ranks and downstream attribution across 640 paired TEST scenarios (278 complete scorable positive pairs).")
    ins_1_4.add_numbered_item("6.", "**Zero-Cost Offline Reproducibility (`OFFLINE_GUARD`):** Providing a cryptographically sealed verification archive (`public_v4_candidate_20261003.zip`) that enables any independent auditor to replay all 6,400 predictions, bootstrap confidence intervals, and financial ledgers offline at USD 0.00 API cost.")

    # 1.5. Scope and Limitations (P209)
    _, p_1_5 = find_paragraph_by_exact_or_prefix(doc, "Scope and Limitations", start_idx=203)
    ins_1_5 = CursorInserter(doc, p_1_5._p)
    ins_1_5.add_p(
        text=(
            "The scope of this thesis is strictly governed by Scientific Protocol `experiment-protocol-v1.1` (`config/experiment_protocol_v1.json`, SHA-256 `a402b04a...`) and the Scope Alignment Addendum (Section 15 of the Research Plan):"
        ),
    )
    ins_1_5.add_bullet("**Target Taxonomy & Positive Technique Scope:** The retrieval corpus and Macro-F1 evaluation universe encompass all **474 active Windows techniques and sub-techniques** (176 root, 298 sub-techniques) in MITRE ATT&CK Enterprise v19.2. Positive ground-truth support in the benchmark is concentrated across **8 high-frequency Windows techniques**: `T1059.001` (PowerShell), `T1059.003` (Windows Command Shell), `T1053.005` (Scheduled Task), `T1543.003` (Windows Service), `T1136.001` (Local Account), `T1547.001` (Registry Run Keys / Startup Folder), `T1685.005` (Clear Windows Event Logs), and `T1105` (Ingress Tool Transfer).")
    ins_1_5.add_bullet("**Benchmark Dataset Scope (`synthetic-paired-v1`):** The dataset comprises **670 scenario pairs** (**1,340 views** across 1,434 unique events), split into **640 TEST pairs (1,280 views)** across 52 template families and **30 DEV pairs (60 views)** across 12 template families with zero family overlap. Across the 1,280 TEST views, authoritative ground-truth joining yields **718 scorable mapped-positive views** (278 single-event, 440 contextual-event; 678 single-GT, 40 multi-GT across 440 scenario clusters), while 311 ambiguous views and 251 unmapped negative views are excluded from headline accuracy per Protocol Decisions D2c and D2b.")
    ins_1_5.add_bullet("**Explicit Non-Goals:** This study does not train or fine-tune model weights, does not build multi-agent workflows, does not deploy production SIEM/Wazuh/EDR infrastructure, and does not construct knowledge graphs.")
    ins_1_5.add_callout(
        "CRITICAL DISCIPLINARY CLAIM BOUNDARY & Forensic Telemetry Blocker (Task 2 / T15)",
        "All experimental evaluations and conclusions in this thesis are strictly bounded to the `synthetic-paired-v1` benchmark and do NOT evaluate real-world enterprise telemetry. While the initial research plan contemplated evaluating public Windows-APT telemetry (Mendeley v3, Mozaffari et al., 2026 [13]), an internal forensic audit conducted during Task 2 (`reports/final_repair_validation.md`) uncovered **15,713 unresolved cell discrepancies** between individual scenario CSVs and the combined dataset (14,930 cells in `_source.id` and 509 cells in binary event data suffering numeric precision truncation, `#NAME?` formula corruption in `param3`, and divergent timestamps). This triggered a formal fail-closed stop (`RECONCILIATION_DIVERGENT`). Under Protocol Decision D6 (`NOT_REQUIRED_FOR_SYNTHETIC_BENCHMARK`), Task T15 is formally recorded as `Deferred / Out-of-Scope` (`DATA_UNAVAILABLE`), and generalization to real production telemetry remains unproven.",
        border_color="CF222E",
        bg_color="FFEBE9",
    )

    # 1.6. Thesis Structure (P210)
    _, p_1_6 = find_paragraph_by_exact_or_prefix(doc, "Thesis Structure", start_idx=203)
    ins_1_6 = CursorInserter(doc, p_1_6._p)
    ins_1_6.add_p(
        text="The remainder of this Capstone Project Thesis Document is organized into six chapters, followed by References and Appendices, strictly adhering to the FPT University Information Assurance Research Thesis structure:"
    )
    ins_1_6.add_bullet("**Chapter 1 (Introduction):** Establishes the operational background of Windows endpoint threat attribution, states the research problem, formulates Research Questions RQ1–RQ3 (Table 1), defines the study's significance, and declares the strict synthetic scope boundary.")
    ins_1_6.add_bullet("**Chapter 2 (Literature Review):** Presents a source-bounded audit of eight core comparator studies (6/8 full-text verified, 2/8 metadata-only), synthesizes the 16-dimension comparator matrix (Tables 2 & 3), and defines the research gap and contributions.")
    ins_1_6.add_bullet("**Chapter 3 (Methodology):** Details the dual-view system architecture (Figure 1), Frozen Scientific Protocol v1.1 (D1–D7), `gpt-5.6-luna` inference configuration and provenance policy, symmetric prompt template, FAISS `IndexFlatIP` retrieval engine, `synthetic-paired-v1` data engineering, `INFERENCE_ALLOWLIST` anti-leakage controls, and formal mathematical evaluation definitions ($\\text{Hit@}k$ vs. $\\text{Recall@}k$, piecewise D2j Macro-F1, cluster bootstrap vs. unclustered McNemar).")
    ins_1_6.add_bullet("**Chapter 4 (Experiments and Results):** Reports the complete empirical results from the 6,400-request canonical campaign (Tables 4–10, Figures 2–8), analyzes RQ1–RQ3 (including both Accuracy and Macro-F1 CIs, TEST-only vs. combined TEST+DEV retrieval cohorts, and a verbatim multi-view worked example), compares findings with prior literature, and outlines SOC engineering implications.")
    ins_1_6.add_bullet("**Chapter 5 (Discussion):** Revisits the research objectives, synthesizes key empirical takeaways, examines synthetic data boundaries, operational latency/cost trade-offs, runtime infrastructure resilience, and evaluates Threats to Validity across Internal, Statistical, External, and Construct dimensions.")
    ins_1_6.add_bullet("**Chapter 6 (Conclusion and Future Work):** Summarizes the thesis conclusions across RQ1–RQ3, certifies open-science reproducibility, and proposes concrete future research hypotheses in hybrid lexical-dense retrieval, event pre-filtering, and verified real-world telemetry benchmarking.")

    # ==========================================================================
    # 8. CHAPTER 2: LITERATURE REVIEW (P212..P216) — Review Points 1.2, 1.4, 1.5, 3, 5.3 Fixed
    # ==========================================================================
    _, p_2_1 = find_paragraph_by_exact_or_prefix(doc, "Review of Previous Studies", start_idx=212)
    ins_2_1 = CursorInserter(doc, p_2_1._p)
    ins_2_1.add_p(
        text=(
            "To situate RAG2ATT&CK within contemporary cybersecurity and natural language processing scholarship, we conducted a rigorous, source-bounded literature audit of eight primary comparator studies alongside foundational works on Retrieval-Augmented Generation [4], the MITRE ATT&CK framework [1], and Windows APT datasets [13]. In strict adherence to scholarly truthfulness (`reports/T33_related_work.md`, PR #8 commit `6783f209`, and `reports/evidence/t33_lade_claim_verification_record.json`), we explicitly disclose the verification tier of each comparator:"
        ),
    )
    ins_2_1.add_bullet(
        "**Full-Text Content Audited (6/8 Comparators):** Lekssays et al. (*TechniqueRAG*, ACL 2025) [5], Morbiato et al. (*H-TechniqueRAG*, 2026) [6], Landauer et al. (*CAM-LDS*, IJIS 2026) [8], Adediran et al. (*CloudTrail RAG*, CMC 2026) [10], Lupinacci et al. (*Trace2ATT&CK*, 2026) [11], and Gwak et al. (*LADE*, SecureComm 2026/2027, 28-page author manuscript PDF verified against SHA-256 `6e8384569254bc4cf82dd4d0191746907ff40fa76016275946651cf47d6f4985`) [12]."
    )
    ins_2_1.add_bullet(
        "**Partial / Metadata-Only / Access-Blocked (2/8 Comparators):** Yang & Hsu (SITAIBA/Springer 2026) [7] is verified solely from the publisher abstract and bibliographic metadata due to subscription paywall restrictions; Okuma et al. (IEEE ICSPIS 2023) [9] is verified solely from the IEEE bibliographic record. All claims concerning these two works are strictly bounded to verified metadata (`UNVERIFIED`)."
    )
    ins_2_1.add_subheading("Stream 1: Retrieval-Augmented Generation for Unstructured CTI Text Annotation")
    ins_2_1.add_p(
        text=(
            "**TechniqueRAG (Lekssays et al., 2025) [5]** introduced a retrieval-and-reranking pipeline for annotating unstructured Cyber Threat Intelligence (CTI) text reports with exact MITRE ATT&CK techniques and sub-techniques (`Txxxx.yyy`). The system retrieves a candidate pool of $K=40$ annotated text-label exemplars from TRAM and MITRE procedure corpora using BM25, reranks them via DeepSeek-v3 to select a fixed $k=3$ exemplars, and feeds them to a fine-tuned Ministral-8B generator. While TechniqueRAG analyzes retriever versus generator errors, it operates exclusively on natural-language CTI prose rather than host logs and does not report standalone retriever $\\text{Hit@}k$ across varying depths. "
            "**H-TechniqueRAG (Morbiato et al., 2026) [6]** extended CTI annotation using a hierarchical dense RAG architecture (FAISS IVF) with Llama-3-8B-Instruct over 1,200 CTI-RCM, 2,800 MITRE, and 450 TRAM samples. It routes queries from tactics to techniques, evaluating sensitivity to tactic count $M$ (peaking at $M=3$ with per-tactic quota $K_A=15$) against a zero-shot Llama 3 baseline, and highlights context distraction when excessive candidates are injected. However, H-TechniqueRAG evaluates human-authored CTI prose rather than structured endpoint telemetry and does not perform a flat retriever depth sweep $k \\in \\{1, 3, 5, 10\\}$."
        ),
    )
    ins_2_1.add_subheading("Stream 2: Windows Sysmon and Host Command Telemetry Mapping to MITRE ATT&CK")
    ins_2_1.add_p(
        text=(
            "**Okuma et al. (2023) [9]** established an early foundation for automated mapping of Windows Sysmon event logs to ATT&CK techniques using Atomic Red Team executions; however, as only the IEEE bibliographic record was accessible during our audit, its internal mapping mechanism remains marked `UNVERIFIED`. "
            "**Yang & Hsu (2026) [7]** represent the closest input-level comparator on Windows: their system integrates Windows Sysmon process trees, semantic matching RAG, and in-context analysis across Mistral-7B, phi-2, and TinyLlama-1.1B with a matched No-RAG baseline. Crucially, however, based on verified abstract metadata, Yang & Hsu focus on binary malicious behavior detection and natural-language explanation (reporting Precision, F1, and False Positive Rate) rather than exact 474-class ATT&CK technique/sub-technique ID attribution. "
            "**LADE (Gwak et al., 2026/2027) [12]** evaluates chronological host command and script traces for APT detection and ranked ATT&CK technique mapping (`Top-3` and `Top-10` output cutoffs) across `gpt-oss-120B`, `Llama-3.3-70B`, `Mistral-Small-3.2-24B`, and `Gemini-2.5-Pro`. Full-text verification of the 28-page manuscript (`LADE-2026.pdf`, pp. 13–15) confirms that LADE evaluates two benchmarks: the **AVIATOR dataset** (35 attack and 32 benign sequences) and a **Caldera-derived dataset** comprising two sets of 33 APT sequences for 2:1 and 10:1 benign-to-APT ratio settings (each set of 33 APT sequences consists of 20 adversary-profile sequences and 13 MITRE emulation-plan sequences—specifically 5 lateral-movement and 8 multi-stage attack sequences—paired with 33 benign sequences). To handle long traces (Section 4.1, pp. 7–8), LADE segments traces at **70% of each model's context window** (all Caldera sequences fit in a single window; on AVIATOR, segmentation is triggered for 12 sequences on Mistral-Small-3.2-24B, 10 sequences each on gpt-oss-120B and Llama-3.3-70B under 128k windows [$\\approx 89,600$ token limit], and 6 sequences on Gemini-2.5-Pro under a 1M window). Across 5 voting runs (p. 15), 76.3% of sequences achieve 5–0 unanimity, 13.8% achieve 4–1 consensus, and 10% split 3–2. Importantly, LADE uses rubric prompting with static ATT&CK text and performs **no RAG retrieval ablation**."
        ),
    )
    ins_2_1.add_subheading("Stream 3: RAG-Assisted Telemetry Attribution in Cloud and Linux Environments")
    ins_2_1.add_p(
        text=(
            "**Adediran et al. (2026) [10]** provide the closest experimental-design comparator for controlled No-RAG versus RAG contrast on security telemetry, evaluating Gemini 2.5 Pro across 200 AWS CloudTrail JSON events (122 malicious, 78 benign) using a two-step query-expansion RAG pipeline on Vertex AI. While they demonstrate that RAG improves accuracy, precision, recall, and F1 over unaugmented Gemini 2.5 Pro, their study operates on cloud API logs rather than Windows endpoint telemetry, omits numeric retrieval depth $k$, does not report standalone retriever $\\text{Hit@}k$ or $\\text{Recall@}k$, and contains an unresolved internal reporting discrepancy in its published text (stating in Section 2 and the conclusion that retrieval-generation gaps account for 60% of errors, while the Section 6.4.1 heading reports 26%). "
            "**Trace2ATT&CK (Lupinacci et al., 2026) [11]** maps 347 Linux Atomic Red Team kernel executions (represented as eBPF provenance graphs) to ATT&CK techniques using Chroma dense retrieval (800-word ATT&CK chunks with Maximal Marginal Relevance) across six models (`foundation-sec-8b`, `qwen3.5-9b`, `gpt-oss`, `gemma4-31b-it`, `deepseek-r1-qwen32b`, `llama3.3-70b`), comparing against a prompting baseline. However, Trace2ATT&CK fixes both retriever depth and output cutoff at 5 chunks/candidates, preventing separation of standalone retriever recall from downstream generation accuracy."
        ),
    )
    ins_2_1.add_subheading("Stream 4: Zero-Shot Multi-Source Log Interpretation and Anti-Leakage Methodology")
    ins_2_1.add_p(
        text=(
            "**CAM-LDS (Landauer et al., 2026) [8]** evaluates zero-shot LLM log interpretation across 7 multi-step cyber attack scenarios (198 log steps across 18 Linux `auditd`/`syslog` and IDS sources) using frontier models (`GPT-5.5`, `GPT-5.2`, `Llama 4`, `Qwen 3`, `Ministral` per §5.1). CAM-LDS introduces rigorous anti-label-leakage sanitization—stripping explicit ATT&CK labels and detector rule names before prompting—and evaluates output candidate ranking (`P@k`, `Recall@k`, `MRR`) while collapsing sub-techniques to parent techniques (`Txxxx`, §5.2.2). However, CAM-LDS deliberately excludes RAG."
        ),
    )

    # 2.2. Summary of the Literature Review (P215) — Tables 2 & 3
    _, p_2_2 = find_paragraph_by_exact_or_prefix(doc, "Summary of the Literature Review", start_idx=212)
    ins_2_2 = CursorInserter(doc, p_2_2._p)
    ins_2_2.add_p(
        text=(
            "Table 2 and Table 3 synthesize our 16-dimension comparative evaluation across all eight comparator works and RAG2ATT&CK. To ensure full legibility within the 6.50-inch printable page width, Table 2 presents Comparators 1–4 and Table 3 presents Comparators 5–8 alongside RAG2ATT&CK."
        ),
    )
    ins_2_2.add_table(
        "Table 2: Multi-Dimensional Comparator Matrix Grounded in Primary Evidence (Part 1: Comparators 1–4).",
        TABLE_2_COMP_A,
        table_id="table_2",
        bm_name="_Ref_tbl_2",
        custom_widths=[1.30, 1.30, 1.30, 1.30, 1.30],
    )
    ins_2_2.add_table(
        "Table 3: Multi-Dimensional Comparator Matrix Grounded in Primary Evidence (Part 2: Comparators 5–8 and RAG2ATT&CK).",
        TABLE_3_COMP_B,
        table_id="table_3",
        bm_name="_Ref_tbl_3",
        custom_widths=[1.25, 1.05, 1.05, 1.05, 1.05, 1.05],
        footnote_text=(
            "*Note on Adediran et al. [10]: The published primary text contains an unresolved internal discrepancy without authorial resolution, stating in Section 2 and the conclusion that retrieval-generation gaps account for 60% of errors, while Section 6.4.1 heading reports 26%. We refrain from imputing derived fractions to the authors."
        ),
    )
    ins_2_2.add_p(
        text=(
            "**Research Gap Synthesis:** Although prior studies have investigated LLM-based ATT&CK mapping [8, 12], RAG-assisted Sysmon or security-log analysis [7], ATT&CK-grounded RAG in cloud [10] and Linux kernel telemetry [11], and retrieval/reranking for CTI text annotation [5, 6], **controlled evaluations of MITRE ATT&CK-grounded RAG for exact technique and sub-technique attribution (`Txxxx.yyy`) from Windows endpoint telemetry remain limited**. Crucially, no single prior work combines Windows endpoint telemetry, a strictly symmetric same-LLM No-RAG versus RAG contrast, systematic retriever depth ablation ($k \\in \\{1, 3, 5, 10\\}$) decoupled from single-ID output prediction, and independent measurement of upstream retrieval misses versus downstream LLM selection discrepancies."
        ),
    )

    # 2.3. Research Contributions (P216) — Review Points 1.2, 1.4, 1.5, 3 Fixed
    _, p_2_3 = find_paragraph_by_exact_or_prefix(doc, "Research Contributions", start_idx=212)
    ins_2_3 = CursorInserter(doc, p_2_3._p)
    ins_2_3.add_p(
        text=(
            "Positioned as a **conceptual replication-and-extension empirical study**, this thesis makes four concrete scientific and engineering contributions:"
        ),
    )
    ins_2_3.add_numbered_item("1.", "**Controlled Empirical Replication on Windows Endpoint Telemetry:** We replicate the core treatment contrast of Adediran et al. [10] (`No-RAG` vs. `ATT&CK-Grounded RAG`) while transferring the domain from AWS CloudTrail to Windows Sysmon and Security Event telemetry [7, 9], holding the requested `gpt-5.6-luna` alias (`reasoning_effort=xhigh`, `max_output_tokens=8192`), output schema, and `prompts/baseline_v1.txt` strictly constant across 6,400 dispatches.")
    ins_2_3.add_numbered_item("2.", "**Diagnostic Extension Decoupling Retrieval vs. Generation Error Axes:** Extending the retrieval-quality analysis of TechniqueRAG [5] and H-TechniqueRAG [6] to terse endpoint logs, we report both standalone sample-level hit rate ($\\text{Hit@}1 = 3.76\\%$, $\\text{Hit@}10 = 44.71\\%$) and fractional multi-label recall ($\\text{Macro Recall@}1 = 2.95\\%$, $\\text{Macro Recall@}10 = 42.80\\%$) on the 718 scorable TEST views, alongside post-retrieval stratum accuracy ($91.28\\%$ when at least one ground-truth technique is retrieved vs. $70.03\\%$ when absent), showing that $80.95\\%$ ($119/147$) of classification errors at $k=10$ co-occur with retrieval misses.")
    ins_2_3.add_numbered_item("3.", "**Observational Characterization of Per-Technique Retrieval Misses and Multi-Event Rank Shifts:** Across the 718 scorable TEST cohort (with auxiliary combined TEST+DEV diagnostics from Task T20 explicitly delineated), we document: (a) a $0.00\\%$ $\\text{Hit@}10$ rate on `T1136.001` (`0/95` TEST views—comprising `70` views containing Security `EventID=4720` [`10` single-event `{4720}` views and `60` contextual views across EventID set combinations `{4688, 4720}` (`38`), `{1, 4720}` (`12`), and `{13, 4720}` (`10`)] where sanitized `EventID=4720` records retain the 6 allowlisted fields `TimeCreated`, `Computer`, `EventID`, `TargetUserName`, `SubjectUserName`, `SubjectLogonId`, plus `25` single-event process-creation views [`13` `EventID=4688` and `12` Sysmon `EventID=1`]; `0/99` in combined TEST+DEV) alongside a $16.67\\%$ $\\text{Hit@}10$ rate on `T1105` (`18/108` on TEST; `15.79%`, `18/114` on TEST+DEV); and (b) multi-event retrieval rank shifts under the Top-10-censored rank comparison (`comparison_rank = rank if found else 11`), where contextual views exhibit a worse anchor-technique rank in **$21.58\\%$ (`60/278`)** of complete scorable TEST pairs, a better rank in **$7.55\\%$ (`21/278`)**, and a tied rank in **$70.86\\%$ (`197/278`: `58` tied at a finite Top-10 rank and `139` absent from Top-10 in both views)** (`21.96%`, `65/296` worse vs. `7.77%`, `23/296` better and `70.27%`, `208/296` tied [`61` finite + `147` absent-both] in the combined TEST+DEV T20 cohort). These patterns are consistent with hypotheses involving lexical mismatch, competing retrieved techniques, and context dilution; the present observational diagnostics do not isolate these mechanisms causally.")
    ins_2_3.add_numbered_item("4.", "**Cryptographically Sealed Benchmark and Forensic Data Governance:** Following our Task 2 forensic discovery of 15,713 cell discrepancies in public Windows-APT CSV exports [13], we deliver the byte-audited `synthetic-paired-v1` benchmark (`INFERENCE_ALLOWLIST` leakage-scrubbed) and an offline reproduction suite (`public_v4_candidate_20261003.zip`) verified across 178/178 automated audit gates.")

    # ==========================================================================
    # 9. CHAPTER 3: METHODOLOGY (P218..P223) — Review Points 1.3, 1.4, 2.1, 2.2, 2.4, 3 Fixed
    # ==========================================================================
    _, p_3_1 = find_paragraph_by_exact_or_prefix(doc, "Research Design", start_idx=218)
    ins_3_1 = CursorInserter(doc, p_3_1._p)
    ins_3_1.add_p(
        text=(
            "Our experimental methodology is structured as a controlled, five-condition comparative evaluation governed by the cryptographically frozen protocol `experiment-protocol-v1.1` (Canonical Decisions Digest: `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c`; Protocol Config File SHA-256: `a402b04ab463172f9d4079bff27b089ca8a21ffd0805d097af6cb1f3c7b5a8fb`), approved under reference `RAG2ATTCK-PROTOCOL-V1.1-FROZEN`. Figure 1 illustrates the dual-view attribution architecture comparing the unaugmented `No-RAG` baseline against the `RAG` pipeline."
        ),
    )
    ins_3_1.add_figure(
        "fig1_system_architecture.png",
        "Figure 1: Dual-View Attribution Architecture (CTI Log -> all-MiniLM-L6-v2 -> FAISS -> gpt-5.6-luna xhigh).",
        fig_id="fig_1",
    )
    ins_3_1.add_subheading("1. Frozen Scientific Protocol Policies (D1–D7 and D2a–D2j)")
    ins_3_1.add_bullet("**D1 (Raw Response Policy: `RECORD_ONLY`):** The raw textual completion emitted by the LLM is captured inline (`raw_response: str`) within prediction records for full auditability, with fail-closed secret sanitization.")
    ins_3_1.add_bullet("**D2a (Multi-Label Ground Truth Semantics: `ANY_MATCH`):** For samples with multi-label ground truth ($Y_i$), a single predicted technique $\\hat{y}_i$ is scored as correct if $\\hat{y}_i \\in Y_i$.")
    ins_3_1.add_bullet("**D2b & D2c (Empty and Ambiguous Ground Truth: `EXCLUDE`):** Negative/unmapped samples (`label_status == \"unmapped\"`, $N=251$) and ambiguous samples (`label_status == \"ambiguous\"`, $N=311$) are excluded from headline accuracy and Macro-F1, but retained in diagnostic and financial accounting.")
    ins_3_1.add_bullet("**D2d (Macro-F1 Universe: `FROZEN_BENCHMARK_UNIVERSE`):** Macro-averaging is computed over the entire fixed 474-technique active Windows universe ($|\\mathcal{C}|=474$), ensuring constant denominators across all conditions.")
    ins_3_1.add_bullet("**D2e & D2f (Invalid ID & Provider/Parser Failure Accounting: `INCLUDE_IN_DENOMINATOR`):** Hallucinated/non-existent ATT&CK IDs, provider timeouts, HTTP errors, and JSON parse failures are retained in all headline accuracy denominators and scored as incorrect (Fail-Closed).")
    ins_3_1.add_bullet("**D2g (Retired ATT&CK IDs: `ALLOW_HISTORICAL`):** Predictions matching deprecated or revoked STIX IDs are tracked distinctly without silent remapping.")
    ins_3_1.add_bullet("**D2h (Retrieval Success Definition: `ANY_GT_RETRIEVED`):** Sample-level retrieval hit ($\\text{Hit@}k$) is satisfied if $Y_i \\cap R_{i,k} \\neq \\emptyset$, whereas fractional multi-label coverage is tracked separately via $\\text{Macro Recall@}k$.")
    ins_3_1.add_bullet("**D2i (Failure Decomposition: `INDEPENDENT_AXES`):** Errors are analyzed along five independent diagnostic axes without forced artificial precedence.")
    ins_3_1.add_bullet("**D2j (Zero Denominator Convention: `NULL`):** Undefined per-class metric fractions evaluate strictly to `null` in JSON exports while contributing $0.0$ to the 474-class macro-average numerator.")
    ins_3_1.add_bullet("**D3–D7 (Execution & Governance Controls):** Timestamped model response ID binding (`D3: ALLOW_LATEST_WITH_TIMESTAMP_BINDING`), strictly sequential execution `concurrency = 1` (`D4`), hard worst-case attempt budget reservation (`D5`), independence from blocked external telemetry (`D6`), and full 1,280-view `PAIRED_TEST` execution (`D7`).")

    ins_3_1.add_subheading("2. Language Model Configuration, Provenance Policy, and Symmetric Prompting")
    ins_3_1.add_p(
        text=(
            "The language model configuration is frozen in `config/model.json` (SHA-256: `312c34ce...`): OpenAI `gpt-5.6-luna` invoked via the OpenAI Responses API (`client.responses.create`) with identical reasoning settings (`reasoning_effort=\"xhigh\"` and `max_output_tokens=8192`, a unified ceiling covering internal reasoning and visible output tokens; note that fixed reasoning settings do not constrain the model to expend identical actual reasoning tokens per query). In accordance with Protocol Decision D3 (`ALLOW_LATEST_WITH_TIMESTAMP_BINDING`) and `artifacts/results/outputs/run_provenance.json` (SHA-256: `90918c9e...`), the requested model alias and inference configuration were fixed across all conditions and timestamped response IDs (`has_response_ids: true`, `has_timestamps: true`) were retained for every dispatch; however, the recorded provenance does not identify an immutable backend model snapshot or system fingerprint (`model_version: null`, `system_fingerprints: []`). Sampling parameters (`temperature`, `top_p`, `seed`) are left unconfigured at uniform provider defaults across all conditions, with deterministic exponential backoff retry resilience (`max_retries=3`, initial delay 1.0s, factor 2.0, max delay 30.0s, socket timeout 120s)."
        ),
    )
    ins_3_1.add_p(
        text=(
            "Crucially, native JSON Schema enforcement (`strict: true`) targets the Pydantic `TechniquePrediction` schema (`{\"technique_id\": \"...\"}`) while deliberately omitting regex pattern constraints at the API schema layer. This architectural separation enables a **two-layer post-hoc taxonomic validation pipeline**: (1) *Layer 1 (Canonical Syntax Check)* validates strings against `^T\\d{4}(?:\\.\\d{3})?$`, classifying malformed strings (e.g., `\"T1059.1\"`) as `INVALID_ID` rather than `MALFORMED_RESPONSE`; (2) *Layer 2 (Registry Membership Check)* validates syntax-compliant IDs against the pinned ATT&CK v19.2 registry. Both `no_rag` and all `rag_k*` conditions share the byte-identical prompt template `prompts/baseline_v1.txt` (SHA-256: `b751fde1ee33b03ec0bdc07cbba10267002d2086cf22b91a74bdfd123856f206`):"
        ),
    )
    ins_3_1.add_code_block(
        "You are an expert cyber threat intelligence and SOC analyst.\n"
        "Analyze the following endpoint evidence and determine the single most specific and accurate MITRE ATT&CK Technique or Sub-technique ID.\n\n"
        "If reference context is provided below, use it as supporting information for the attribution. If no reference context is provided, perform the attribution using the endpoint evidence alone.\n\n"
        "ENDPOINT EVIDENCE:\n"
        "{ENDPOINT_EVIDENCE}\n\n"
        "---\n"
        "REFERENCE CONTEXT:\n"
        "{RETRIEVED_CONTEXT}\n"
        "---\n\n"
        'Respond with a single JSON object containing only the "technique_id" field. Do not include markdown formatting, code fences, or explanatory text.'
    )

    ins_3_1.add_subheading("3. Dense Retrieval Subsystem, Prefix Consistency, and Financial Guard")
    ins_3_1.add_p(
        text=(
            "Frozen in `config/retrieval.json` (SHA-256: `b33a9391...`), the dense retriever encodes both ATT&CK corpus documents and sanitized telemetry queries into 384-dimensional unit L2-normalized vectors ($\\|v\\|_2 = 1.0$) using `sentence-transformers/all-MiniLM-L6-v2` (pinned to Hugging Face commit `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`) indexed in a FAISS `IndexFlatIP` structure. Under unit L2 normalization, inner product equals cosine similarity:"
        ),
    )
    ins_3_1.add_equation(r"\langle \hat{q}, \hat{d}_i \rangle = \frac{q \cdot d_i}{\|q\|_2 \|d_i\|_2} = \cos(q, d_i)")
    ins_3_1.add_p(
        text=(
            "To guarantee deterministic tie-breaking and strict prefix consistency across retrieval depths $k \\in \\{1, 3, 5, 10\\}$, the retriever scores all $N=474$ documents, sorts via compound key $\\text{sort\\_key} = (-\\text{score}, \\text{technique\\_id})$, and slices the top $k$, satisfying the **Prefix Consistency Invariant**:"
        ),
    )
    ins_3_1.add_equation(r"\forall k_1 < k_2 \in \{1, 3, 5, 10\}: \quad \text{results}(k_1) \equiv \text{results}(k_2)[:k_1]")
    ins_3_1.add_p(
        text=(
            "Under Protocol Decision D5 and `config/pricing_v1.json` (short-context $\\le 272\\text{k}$ tokens: input `$0.20/M`, cache-read `$0.02/M`, cache-write `$0.25/M`, output `$1.20/M`), the runner places a worst-case reservation of **USD 0.53974560** before each attempt under a hard cap of $\\text{Cap} = 1,280 \\times 5 \\times 4 = 25,600$ attempts and an authorized study budget ceiling of **USD 19.99000000**."
        ),
    )

    # 3.2. Data Collection Methods (P221) — Review Point 3 Fixed (Exact INFERENCE_ALLOWLIST per channel)
    _, p_3_2 = find_paragraph_by_exact_or_prefix(doc, "Data Collection Methods", start_idx=218)
    ins_3_2 = CursorInserter(doc, p_3_2._p)
    ins_3_2.add_p(
        text=(
            "Data collection and corpus engineering in RAG2ATT&CK encompass three cryptographically audited pipelines: (1) MITRE ATT&CK v19.2 Windows knowledge base extraction, (2) forensic auditing of external public telemetry, and (3) generation and leakage-scrubbing of the `synthetic-paired-v1` benchmark."
        ),
    )
    ins_3_2.add_bullet(
        "**MITRE ATT&CK Enterprise Matrix v19.2 Corpus Census:** Starting from the official raw STIX bundle `enterprise-attack-19.2.json` (published 05 August 2026; SHA-256: `dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4`), we parse exactly **858** `attack-pattern` objects. Removing **161 unique inactive** objects (**149 revoked** with `revoked: true` and **12 deprecated** with `x_mitre_deprecated: true`, zero overlap: $149 + 12 = 161$) yields **697 active enterprise techniques**. Filtering for `\"Windows\" in x_mitre_platforms` yields the canonical active Windows corpus of **474 techniques and sub-techniques** (**176 root techniques** [37.1%] and **298 sub-techniques** [62.9%]), verified to have 0 orphan sub-techniques and serialized in `attack/corpus/enterprise-windows-v19.2.jsonl` (SHA-256: `b2193411...`)."
    )
    ins_3_2.add_bullet(
        "**Synthetic Paired Benchmark (`synthetic-paired-v1`):** Following the Task 2 forensic rejection of Mendeley v3 CSVs (15,713 cell discrepancies), we engineered `synthetic-paired-v1` (`data/ground_truth/synthetic/dataset_manifest.json`, SHA-256: `4576b793...`), comprising **670 scenario pairs** (**1,340 evaluation views** across 1,434 unique events). The **TEST split** contains **640 scenario pairs (1,280 views = 640 single-event + 640 contextual-event)** across 52 template families; the **DEV split** contains **30 scenario pairs (60 views)** across 12 template families, with strict family disjointness ($\\text{Family}_{\\text{TEST}} \\cap \\text{Family}_{\\text{DEV}} = \\emptyset$). In each pair, the *single-event view* presents the isolated anchor event, while the *contextual-event view* embeds the anchor event within a sequence of 2–3 correlated host events."
    )
    ins_3_2.add_bullet(
        "**Strict Field Whitelisting and Anti-Leakage Controls (`INFERENCE_ALLOWLIST` and `CANONICAL_TELEMETRY_SCHEMA` in `src/synthetic.py`):** All inference payloads (`data/ground_truth/synthetic/inference.jsonl`, SHA-256: `90d5f59e...`) are projected through `INFERENCE_ALLOWLIST = {\"sample_id\", \"endpoint_evidence\"}`, where each event dictionary inside the JSON-serialized `endpoint_evidence` list retains only the sanitized per-channel behavioral fields defined in `CANONICAL_TELEMETRY_SCHEMA` (note that provider/channel names do not appear as keys inside `endpoint_evidence`): `UtcTime`, `Computer`, `EventID`, `Image`, `CommandLine`, `ParentImage`, `ParentCommandLine`, `User`, `ProcessId`, `ParentProcessId`, `ProcessGuid`, `ParentProcessGuid`, `LogonGuid`, `LogonId`, `Hashes` (Sysmon ProcessCreate `EventID 1`); `UtcTime`, `Computer`, `EventID`, `Image`, `User`, `SourceIp`, `SourcePort`, `DestinationIp`, `DestinationPort`, `Protocol`, `ProcessId`, `ProcessGuid` (Sysmon NetworkConnect `EventID 3`); `UtcTime`, `Computer`, `EventID`, `Image`, `TargetFilename`, `ProcessId`, `ProcessGuid`, `User` (Sysmon FileCreate `EventID 11`); `UtcTime`, `Computer`, `EventID`, `Image`, `EventType`, `TargetObject`, `Details`, `ProcessId`, `ProcessGuid`, `User` (Sysmon Registry `EventID 13`); `TimeCreated`, `Computer`, `EventID`, `NewProcessName`, `CommandLine`, `ParentProcessName`, `SubjectUserName`, `TargetUserName`, `NewProcessId`, `ProcessId`, `SubjectLogonId` (Security ProcessCreate `EventID 4688`); `TimeCreated`, `Computer`, `EventID`, `ServiceName`, `ServiceFileName`, `ServiceType`, `ServiceStartType`, `ServiceAccount`, `SubjectUserName`, `SubjectDomainName`, `SubjectLogonId` (Security ServiceInstall `EventID 4697`); `TimeCreated`, `Computer`, `EventID`, `TaskName`, `TaskContent`, `SubjectUserName`, `SubjectLogonId` (Security ScheduledTask `EventID 4698`); the 6 allowlisted fields `TimeCreated`, `Computer`, `EventID`, `TargetUserName`, `SubjectUserName`, `SubjectLogonId` (Security AccountCreated `EventID 4720`, i.e., 3 metadata fields + 3 account-identifier fields); and the 5 allowlisted fields `TimeCreated`, `Computer`, `EventID`, `SubjectUserName`, `SubjectLogonId` (Security AuditLogCleared `EventID 1102`). Notice that Active Directory attribute names such as `SamAccountName` and `UserPrincipalName` have zero occurrences in `inference.jsonl`. All Sigma/Wazuh rule titles, `rule.mitre.*` tags, scenario identifiers, and synthetic lexical markers (such as `Contoso`) are completely purged and verified by `tests/test_benchmark_inputs.py` and `tests/test_synthetic_freeze.py`."
    )

    # 3.3. Sampling and Data Analysis Techniques (P222) — Review Points 1.4, 2.1, 2.2, 2.4 Fixed
    _, p_3_3 = find_paragraph_by_exact_or_prefix(doc, "Sampling and Data Analysis Techniques", start_idx=218)
    ins_3_3 = CursorInserter(doc, p_3_3._p)
    ins_3_3.add_p(
        text=(
            "**Authoritative Join and Scorable Cohort Census:** Joining the 1,280 TEST views (`split_manifest.json` $\\to$ `views.jsonl`) against `ground_truth.jsonl` yields **718 mapped positive scorable views** (comprising **678 single-GT views** and **40 multi-GT views**; stratified by representation into **278 Single-Event Views** and **440 Contextual-Event Views**, $278 + 440 = 718$). Across the 640 TEST scenario pairs, **278 complete scorable pairs** have valid positive ground truth on *both* single and contextual views ($278 \\times 2 = 556$ views), **162 pairs** have valid ground truth on *only* the contextual view ($162 \\times 1 = 162$ views; single view unmapped/ambiguous), and **200 pairs** have valid ground truth on *neither* view ($556 + 162 = 718$ scorable views across $278 + 162 = 440$ valid pair clusters). The remaining **311 ambiguous views** (261 single, 50 contextual) and **251 unmapped negative views** (101 single, 150 contextual) are excluded from headline accuracy per Protocol Decisions D2c and D2b. Ground-truth support across the 718 scorable TEST views is concentrated across the **8 benchmark techniques** totaling **768 annotations**: `T1053.005` (85), `T1059.001` (107), `T1059.003` (107), `T1105` (108), `T1136.001` (95), `T1543.003` (108), `T1547.001` (98), and `T1685.005` (60)."
        ),
    )
    ins_3_3.add_p(
        text="**Formal Mathematical Evaluation Metrics:** Under `ANY_MATCH` semantics (D2a), for sample $i$ with ground-truth set $Y_i \\subseteq \\mathcal{C}$ ($|\\mathcal{C}| = 474$) and model prediction $\\hat{y}_i$, the correctness indicator, Headline End-to-End Accuracy ($\\text{Acc}_{\\text{e2e}}$, D2f), and Valid Output Accuracy ($\\text{Acc}_{\\text{valid}}$) are defined as:"
    )
    ins_3_3.add_equation(r"I_{\text{correct}}(i) = 1 \quad \text{if } \hat{y}_i \in Y_i, \quad 0 \quad \text{otherwise}")
    ins_3_3.add_equation(r"\text{Acc}_{\text{e2e}} = \frac{1}{N_{\text{scorable}}} \sum_{i=1}^{N_{\text{scorable}}} I_{\text{correct}}(i), \qquad \text{Acc}_{\text{valid}} = \frac{1}{N_{\text{valid}}} \sum_{i \in \text{Valid}} I_{\text{correct}}(i)")
    ins_3_3.add_p(
        text=(
            "**Standalone Retrieval Metrics ($\\text{Hit@}k$ vs. Sample-Averaged Multi-Label $\\text{Macro Recall@}k$):** Because the scorable TEST cohort includes 40 multi-label (`mapped_multi`) views ($|Y_i| > 1$), sample-level binary hit rate ($\\text{Hit@}k$ per Decision D2h `ANY_GT_RETRIEVED`) and sample-averaged multi-label fractional recall (termed `macro_recall` / $\\text{Macro Recall@}k$ in project artifacts) are mathematically distinct and are reported separately. Given ground-truth label set $Y_i$ and top-$k$ retrieved candidate set $R_{i,k}$:"
        ),
    )
    ins_3_3.add_equation(r"\text{Hit@}k = \frac{1}{N} \sum_{i=1}^{N} \mathbf{1}\{Y_i \cap R_{i,k} \neq \emptyset\}, \qquad \text{Macro Recall@}k = \frac{1}{N} \sum_{i=1}^{N} \frac{|Y_i \cap R_{i,k}|}{|Y_i|}")
    ins_3_3.add_p(
        text=(
            "For example, if a view has two ground-truth techniques ($|Y_i|=2$) and the retriever places exactly one of them in $R_{i,k}$, that view contributes $1.0$ to $\\text{Hit@}k$ but $0.5$ to sample-averaged $\\text{Macro Recall@}k$."
        ),
    )
    ins_3_3.add_p(
        text=(
            "**474-Class Macro-F1 and Piecewise D2j `NULL` Semantics:** For each class $c \\in \\mathcal{C}$, `compute_condition_metrics` in `src/evaluation/experiment_metrics.py` and the canonical bundle analysis pipeline `scripts/analysis/evaluate_rqs.py` track $TP_c, FP_c, FN_c$, support $\\text{support}_c = TP_c + FN_c$, and predictions $\\text{pred}_c = TP_c + FP_c$. Per Decision D2j, undefined per-class ratios export as JSON `null` (`None` in Python) across three boundary cases: **Case A (Unobserved: $\\text{support}_c=0 \\land \\text{pred}_c=0$)** exports `precision=null, recall=null, f1=null`; **Case B (Unpredicted: $\\text{support}_c>0 \\land \\text{pred}_c=0$)** exports `precision=null, recall=0.0, f1=0.0`; **Case C (Hallucinated False Positive: $\\text{support}_c=0 \\land \\text{pred}_c>0$)** exports `precision=0.0, recall=null, f1=0.0`; and **Case D ($TP_c=0$ with $\\text{support}_c>0 \\land \\text{pred}_c>0$)** yields $P_c=0.0, R_c=0.0, F1_c=0.0$. Rather than dividing by $P_c + R_c$ when either quantity is `null` or zero, the effective per-class score $F1_c^*$ accumulated in the 474-class macro-average is defined directly in terms of counts:"
        ),
    )
    ins_3_3.add_equation(r"F1_c^* = \frac{2 \cdot TP_c}{2 \cdot TP_c + FP_c + FN_c} \quad \text{if } TP_c > 0, \quad 0 \quad \text{if } TP_c = 0, \qquad \text{Macro-F1} = \frac{1}{474} \sum_{c \in \mathcal{C}} F1_c^*")
    ins_3_3.add_p(
        text=(
            "**Statistical Inference & Independent Failure Axes (D2i):** Uncertainty bounds on both accuracy differences $\\Delta\\text{Acc} = \\text{Acc}(\\text{RAG}) - \\text{Acc}(\\text{No-RAG})$ and Macro-F1 differences $\\Delta\\text{Macro-F1} = \\text{Macro-F1}(\\text{RAG}) - \\text{Macro-F1}(\\text{No-RAG})$ are estimated as nominal, unadjusted 95% confidence intervals (`NO_MULTIPLE_COMPARISON_CORRECTION_PRE_SPECIFIED_PRIMARY_CONTRASTS`) via **1,000 cluster-bootstrap resamples** (`seed=42`) over the **440 scenario pair clusters** (`cluster_unit: pair_id`, preserving within-pair dependence between single and contextual views of the same scenario while treating between-pair independence across template-derived synthetic pairs as a modeling assumption). Alongside cluster-bootstrap CIs, we report **exact two-sided binomial McNemar tests** over discordant view pairs $(b, c)$ at $N=718$ (and $N=278$ for complete representation pairs); we explicitly note that exact McNemar treats view-level discordant pairs as independent trials without cluster adjustment, so cluster-bootstrap CIs serve as the primary cluster-aware inference reference. Failure analysis tracks five non-mutually-exclusive axes (`retrieval_miss`, `provider_failure`, `parse_failure`, `invalid_attack_id`, `valid_but_wrong_classification`) and compares post-retrieval subsets $P(\\text{Correct}\\mid Y_i \\cap R_{i,k} \\neq \\emptyset)$ and $P(\\text{Correct}\\mid Y_i \\cap R_{i,k} = \\emptyset)$."
        ),
    )

    # 3.4. Limitations of the Methodology (P223)
    _, p_3_4 = find_paragraph_by_exact_or_prefix(doc, "Limitations of the Methodology", start_idx=218)
    ins_3_4 = CursorInserter(doc, p_3_4._p)
    ins_3_4.add_p(
        text=(
            "Four methodological limitations and epistemic boundaries are formally enforced in this study:"
        ),
    )
    ins_3_4.add_numbered_item("1.", "**Synthetic Benchmark Regularities:** While `synthetic-paired-v1` guarantees verified ground truth and zero label leakage, template-derived command lines and 2–3 event contextual windows cannot capture the full background noise, obfuscation, or scale of production enterprise SOC streams.")
    ins_3_4.add_numbered_item("2.", "**Sparse Class Support Across the 474-Class Ontology (Support-Based vs. With-Hallucination Ceiling):** Because positive ground truth in TEST is concentrated in 8 active techniques while 466 classes have zero support ($F1_c^* = 0$), unweighted 474-class Macro-F1 has a support-based upper bound of $8 / 474 \\approx 0.01688$ ($1.69\\%$), and false-positive predictions landing on any of the 466 zero-support classes (Case C) further penalize the active classes' recall without ever increasing the 8-class numerator sum. We preserve the 474-class denominator without post-hoc subset rescaling to honor Protocol D2d.")
    ins_3_4.add_numbered_item("3.", "**Epistemic Boundaries of Failure Decomposition and Post-Retrieval Stratification:** Under Protocol D2i, co-occurrence of classification errors with `retrieval_miss` ($Y_i \\cap R_{i,k} = \\emptyset$) is an observational diagnostic association, not an interventional proof that replacing the retriever alone would eliminate all co-occurring errors. Likewise, the difference between $P(\\text{Correct}\\mid Y_i \\cap R_{i,k} \\neq \\emptyset)$ ($91.28\\%$ at $k=10$) and $P(\\text{Correct}\\mid Y_i \\cap R_{i,k} = \\emptyset)$ ($70.03\\%$) compares two post-retrieval sample strata partitioned by retriever outcome (which correlates with intrinsic log lexical clarity) rather than a randomized intervention on identical samples.")
    ins_3_4.add_numbered_item("4.", "**Observational Nature of Representation Contrasts:** Comparisons between Single-Event ($N=278$) and Contextual-Event ($N=440$) cohorts—and across the 40 label-divergent multi-stage pairs within the 278 complete pairs—represent observational associations confounded by multi-stage scenario label expansion rather than isolated causal effects.")

    # ==========================================================================
    # 10. CHAPTER 4: EXPERIMENTS AND RESULTS (P225..P232) — All Review Points Fixed
    # ==========================================================================
    _, p_4_1 = find_paragraph_by_exact_or_prefix(doc, "Introduction", start_idx=225)
    ins_4_1 = CursorInserter(doc, p_4_1._p)
    ins_4_1.add_p(
        text=(
            "This chapter presents the complete empirical results obtained from the canonical live experimental campaign (`experiment_id=\"synthetic-paired-test-1\"`, `run_id=\"live-66b94b1676bf46a9\"`) executed under `experiment-protocol-v1.1` at execution commit `80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315` and bound to `canonical_metric_bundle_v2.json` (SHA-256: `442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34`) and `canonical_run_seal_v1.json` (SHA-256: `ae7a9ada86927a79e0c6916b44d3f0ba9e1f9756df55dd7b2fce712b35d48701`). Across the 5 experimental conditions (`no_rag`, `rag_k1`, `rag_k3`, `rag_k5`, `rag_k10`), all 1,280 TEST views were dispatched sequentially (`concurrency = 1`), producing **6,400 terminal execution records** across **6,401 physical API attempts** (6,387 VALID responses and 13 INCOMPLETE responses; 99.80% VALID fraction). Within the **718 scorable mapped-positive TEST views** ($5 \\times 718 = 3,590$ dispatches), the provider failure rate, JSON parse failure rate, and invalid ATT&CK ID rate were identically **0.00% (0/3,590)**."
        ),
    )

    # 4.2. Presentation of Data (P228) — Sequential Tables 4..10 & Figures 2..8
    _, p_4_2 = find_paragraph_by_exact_or_prefix(doc, "Presentation of Data", start_idx=225)
    ins_4_2 = CursorInserter(doc, p_4_2._p)
    ins_4_2.add_p(
        text="We present the canonical empirical tables and publication figures organized sequentially across Research Questions RQ1 (Tables 4, 5, 6, 7; Figures 2, 3), RQ2 (Table 8; Figures 4, 5), and RQ3 & Integrated Failure Synthesis (Tables 9, 10; Figures 6, 7, 8)."
    )
    ins_4_2.add_table(
        "Table 4: Primary Attribution Performance, 474-Class Macro-F1 Bootstrap CIs, and Ground-Truth Complexity Across Conditions.",
        TABLE_4_PRIMARY,
        table_id="table_4",
        bm_name="_Ref_tbl_4",
        custom_widths=[0.62, 0.45, 0.52, 0.92, 0.88, 0.78, 0.98, 0.68, 0.67],
        footnote_text=(
            "*Note on Table 4: 95% confidence intervals for both $\\Delta\\text{Acc}$ and $\\Delta\\text{Macro-F1}$ relative to `no_rag` are computed via 1,000 cluster-bootstrap resamples over the 440 TEST scenario clusters (`seed=42`, `canonical_metric_bundle_v2.json`). While $\\Delta\\text{Acc}$ CIs span zero across all $k$, $\\Delta\\text{Macro-F1}$ CIs exclude zero for $k \\in \\{3, 5, 10\\}$."
        ),
    )
    ins_4_2.add_figure(
        "fig2_accuracy_vs_k.png",
        "Figure 2: Attribution Accuracy vs. Candidate Depth k across Conditions (N=718 Scorable Views with 95% Bootstrap CI).",
        fig_id="fig_2",
    )
    ins_4_2.add_figure(
        "fig3_macro_f1_vs_k.png",
        "Figure 3: 474-Class Macro-F1 Performance across Retrieval Depths (8 Active Supported Classes vs. 466 Zero-Support Universe Classes).",
        fig_id="fig_3",
    )
    ins_4_2.add_table(
        "Table 5: Attribution Diagnostic Metrics Across Experimental Conditions.",
        TABLE_5_DIAG,
        table_id="table_5",
        bm_name="_Ref_tbl_5",
    )
    ins_4_2.add_table(
        "Table 6: Representation Stratification: Single-Event vs. Contextual-Event Views.",
        TABLE_6_REPR,
        table_id="table_6",
        bm_name="_Ref_tbl_6",
    )
    ins_4_2.add_table(
        "Table 7: Paired Scorable Representation Concordance and Unclustered McNemar Discordance (N=278 complete pairs).",
        TABLE_7_PAIRED,
        table_id="table_7",
        bm_name="_Ref_tbl_7",
    )
    ins_4_2.add_table(
        "Table 8: Decoupled Failure Decomposition Matrix Across Independent Diagnostic Axes (D2i).",
        TABLE_8_FAILURE,
        table_id="table_8",
        bm_name="_Ref_tbl_8",
    )
    ins_4_2.add_figure(
        "fig4_retrieval_hit_rate.png",
        "Figure 4: Standalone Retrieval Hit@k vs. Multi-Label Macro Recall@k across Depths k=1, 3, 5, 10 on 718 Scorable TEST Views.",
        fig_id="fig_4",
    )
    ins_4_2.add_figure(
        "fig5_conditional_accuracy.png",
        "Figure 5: Post-Retrieval Stratum Accuracy: P(Correct | Hit) vs. P(Correct | Miss) across Retrieval Depths.",
        fig_id="fig_5",
    )
    ins_4_2.add_table(
        "Table 9: Resource Consumption, Latency Scaling, Token-Usage Cost, and Conservative Ledger Spend.",
        TABLE_9_COST,
        table_id="table_9",
        bm_name="_Ref_tbl_9",
        custom_widths=[0.62, 0.72, 0.72, 0.65, 0.60, 0.60, 0.85, 0.92, 0.82],
        footnote_text=(
            "*Note on Table 9 (`rag_k1` Cost Reconciliation & Scope): All resource and cost figures in Table 9 cover the full 1,280 logical TEST requests per condition (6,400 logical requests / 6,401 physical attempts total) and represent tariff-derived accounted costs under the API budget guard (`config/pricing_v1.json`; external commercial invoice verification is absent). For `rag_k1`, pre-credit token-usage estimated cost is $\\text{USD } 0.75784210$ ($\\approx \\text{USD } 0.7578$), less $\\text{USD } 0.00035420$ observed cache credit = $\\text{USD } 0.75748790$ ($\\approx \\text{USD } 0.7575$ net usage cost). Conservative ledger spend is $\\text{USD } 0.75748790 + \\text{USD } 0.53974560 = \\text{USD } 1.29723350$ ($\\approx \\text{USD } 1.2972$, or $\\text{USD } 0.001013$/query) because 1 transient attempt on `view_d870d574` lacked a usage receipt and retained its full pre-dispatch worst-case hold of $\\text{USD } 0.53974560$ per Protocol Decision D5."
        ),
    )
    ins_4_2.add_figure(
        "fig6_latency_vs_k.png",
        "Figure 6: Request Inference Latency Scaling: Mean and Median Duration (ms) across Conditions (P95 Withheld per Protocol).",
        fig_id="fig_6",
    )
    ins_4_2.add_figure(
        "fig7_cost_and_tokens_vs_k.png",
        "Figure 7: Conservative Ledger Spend vs. Token-Usage Cost (USD) and Aggregate Input Token Volume.",
        fig_id="fig_7",
    )
    ins_4_2.add_figure(
        "fig8_failure_decomposition.png",
        "Figure 8: Decoupled Independent Failure Decomposition and Co-occurrence Breakdown at Retrieval Depth k=10.",
        fig_id="fig_8",
    )
    ins_4_2.add_table(
        "Table 10: Whole-Study Financial Ledger and Budget Reconciliation.",
        TABLE_10_LEDGER,
        table_id="table_10",
        bm_name="_Ref_tbl_10",
        custom_widths=[2.20, 2.10, 1.10, 1.10],
    )

    # 4.3. Analysis of Results (P229) — Review Points 1.1, 1.4, 1.6, 2.4 Fixed
    _, p_4_3 = find_paragraph_by_exact_or_prefix(doc, "Analysis of Results", start_idx=225)
    ins_4_3 = CursorInserter(doc, p_4_3._p)
    ins_4_3.add_subheading("1. Analysis of RQ1: End-to-End Attribution Efficacy — Accuracy vs. 474-Class Macro-F1")
    ins_4_3.add_p(
        text=(
            "Across the 718 scorable mapped-positive TEST views (Table 4), retrieval depth $k=10$ (`rag_k10`) achieved the highest observed point estimate for headline end-to-end accuracy at **79.53% (571/718 correct)** compared to the unaugmented baseline (`no_rag`: **77.99%, 560/718 correct**), representing an observed difference of $\\Delta\\text{Acc} = +1.532\\text{ percentage points}$ (+11 net views), while 474-class Macro-F1 increased from **0.012608 (1.26%)** to **0.014024 (1.40%)**. Intermediate retrieval depths yielded **77.02% (553/718, $\\Delta\\text{Acc} = -0.975\\text{ pp}$, Macro-F1 $0.012668$)** at $k=1$, **78.55% (564/718, $\\Delta\\text{Acc} = +0.557\\text{ pp}$, Macro-F1 $0.013643$)** at $k=3$, and **78.83% (566/718, $\\Delta\\text{Acc} = +0.836\\text{ pp}$, Macro-F1 $0.013891$)** at $k=5$. On the 40 multi-GT views, all four RAG conditions achieved **100.00% (40/40)** accuracy compared to **87.50% (35/40)** under `no_rag`."
        ),
    )
    ins_4_3.add_p(
        text=(
            "Critically, answering RQ1 completely requires reporting the distinct statistical inference outcomes for **Accuracy** versus **474-class Macro-F1** recorded in `canonical_metric_bundle_v2.json`:"
        ),
    )
    ins_4_3.add_bullet(
        "**End-to-End Accuracy Difference (Not Statistically Significant):** The 95% cluster-bootstrap confidence intervals (1,000 resamples over 440 scenario clusters, `seed=42`) for $\\Delta\\text{Acc}$ relative to `no_rag` contain zero across all four RAG depths: $\\Delta\\text{Acc}_{k1} = [-3.186\\text{ pp}, +1.124\\text{ pp}]$, $\\Delta\\text{Acc}_{k3} = [-2.786\\text{ pp}, +3.934\\text{ pp}]$, $\\Delta\\text{Acc}_{k5} = [-2.934\\text{ pp}, +4.603\\text{ pp}]$, and $\\Delta\\text{Acc}_{k10} = [-2.355\\text{ pp}, +5.300\\text{ pp}]$. For `rag_k10` versus `no_rag`, the unclustered view-level discordant counts are: both correct = 488, `no_rag` only = 72, `rag_k10` only = 83, and both incorrect = 75, yielding an exact two-sided McNemar $p = 0.4219$ ($p = 0.435$ for $k=1$, $p = 0.777$ for $k=3$, $p = 0.677$ for $k=5$)."
    )
    ins_4_3.add_bullet(
        "**474-Class Macro-F1 Difference (Positive Cluster-Bootstrap CIs at $k \\in \\{3, 5, 10\\}$ and 8-Class F1 Decomposition):** At $k=10$, the 474-class Macro-F1 difference over `no_rag` was **$+0.001415$** ($+0.1415\\text{ pp}$ on a $0$–$100\\%$ scale, a $+11.23\\%$ relative gain), with a nominal 95% cluster-bootstrap confidence interval of **$[+0.001011, +0.001792]$** that excludes zero. Positive 95% cluster-bootstrap CIs excluding zero were likewise observed at $k=3$ ($\\Delta\\text{Macro-F1} = +0.001034$, 95% CI $[+0.000632, +0.001424]$) and $k=5$ ($\\Delta\\text{Macro-F1} = +0.001282$, 95% CI $[+0.000860, +0.001679]$), whereas $k=1$ spanned zero ($+0.000060$, 95% CI $[-0.000242, +0.000363]$). Per-class decomposition (`per_technique_metrics.json`) explains the difference between the observed point-estimate changes in Accuracy and Macro-F1 (while statistical uncertainty is assessed separately using the nominal, unadjusted pair-cluster bootstrap confidence intervals): in view-weighted Accuracy ($1/718$ per view), the $83$ newly corrected views ($b=83$) are largely offset by $72$ regressions ($c=72$, net $+11$ views). In class-weighted Macro-F1 ($1/474$ per class), however, `T1685.005` ($N=60$) jumps from $F1 = 0.0000$ ($\\text{TP}=0$ in `no_rag`) to $F1 = 0.9916$ ($\\text{TP}=59$, $\\Delta F1 = +0.9916$). Specifically, among the 60 TEST views whose ground-truth sets contain `T1685.005`, `no_rag` predicts retired `T1070.001` in 55 views and predicts `T1543.003` in 5 multi-GT views labeled with both `T1543.003` and `T1685.005` (`view_339041eb`, `view_6c60a0e0`, `view_72d3654e`, `view_d3e487ef`, `view_e96ca934`); those 5 predictions are scored as correct under `ANY_MATCH` accuracy but contribute false negatives ($\\text{FN}$) for `T1685.005` in per-class F1, so $\\text{TP}=0$ for `T1685.005` does not mean 60 incorrect view-level predictions. Accompanied by gains on `T1059.001` ($0.7186 \\to 0.7653$, $\\Delta F1 = +0.0467$) and `T1059.003` ($0.7108 \\to 0.7558$, $\\Delta F1 = +0.0450$) while `T1547.001` remains at $1.0000$ ($\\Delta F1 = 0.0000$), these positive class gains ($+1.0833$ combined) outweigh the moderate F1 decreases across the four larger classes—`T1053.005` ($0.9444 \\to 0.8606$, $-0.0838$), `T1543.003` ($0.9763 \\to 0.8866$, $-0.0897$), `T1136.001` ($0.7742 \\to 0.6620$, $-0.1122$), and `T1105` ($0.8520 \\to 0.7254$, $-0.1266$; combined $-0.4124$)—raising the 8-class F1 sum from $5.9764$ (mean $0.7470$ over 8 supported classes; $0.012608$ over 474 classes) to $6.6473$ (mean $0.8309$ over 8 classes; $0.014024$ over 474 classes, net $+0.6709 / 474 = +0.001415$)."
    )
    ins_4_3.add_p(
        text=(
            "In the paired representation analysis across the **278 complete scorable pairs** (Table 7), Contextual views outperformed Single views under `no_rag` ($92.45\\%$ vs. $87.05\\%$, $\\Delta = +5.40\\text{ pp}$, unclustered exact McNemar $p_{\\text{exact}} = 0.0315$) and `rag_k1` ($92.45\\%$ vs. $85.61\\%$, $\\Delta = +6.83\\text{ pp}$, $p_{\\text{exact}} = 0.0026$), converging to $+0.00\\text{ pp}$ ($83.81\\%$ vs. $83.81\\%$, $p_{\\text{exact}} = 1.0000$) at $k=10$. Forensic stratification reveals that of the 278 complete pairs, 238 have identical ground-truth sets while 40 multi-stage pairs have expanded ground-truth sets on the contextual view: 12 of the 15 net contextual wins in `no_rag` (80%) and all 19 of the 19 net contextual wins in `rag_k1` (100%) occurred within the 40 mismatched-GT pairs, indicating that apparent contextual differences co-occur with multi-stage label expansion rather than isolating a purely causal effect of context window length."
        ),
    )

    ins_4_3.add_subheading("2. Analysis of RQ2: Standalone Hit@k vs. Macro Recall@k and Post-Retrieval Failure Axes")
    ins_4_3.add_p(
        text=(
            "Across the 718 scorable TEST views (`retrieval_metrics.json` and `retrieval_conditional_metrics.json`), standalone dense retrieval (`all-MiniLM-L6-v2` + FAISS `IndexFlatIP`) achieved sample-level **$\\text{Hit@}k$ (`ANY_GT_RETRIEVED`)** of **$\\text{Hit@}1 = 3.76\\%$ (`27/718` hits, `691` misses)**, **$\\text{Hit@}3 = 16.43\\%$ (`118/718` hits, `600` misses)**, **$\\text{Hit@}5 = 24.09\\%$ (`173/718` hits, `545` misses)**, and **$\\text{Hit@}10 = 44.71\\%$ (`321/718` hits, `397` misses = $55.29\\%$ miss rate)**. Because 40 scorable TEST views carry multiple ground-truth labels (`mapped_multi`), sample-averaged **multi-label $\\text{Macro Recall@}k$** is systematically lower than $\\text{Hit@}k$: **$\\text{Macro Recall@}1 = 2.95\\%$**, **$\\text{Macro Recall@}3 = 15.48\\%$**, **$\\text{Macro Recall@}5 = 22.96\\%$**, and **$\\text{Macro Recall@}10 = 42.80\\%$** (specifically, on the **40 TEST multi-label views**, $\\text{Hit@}10 = 75.00\\%$ [`30/40`] whereas sample-averaged $\\text{Macro Recall@}10 = 40.83\\%$ [sum of fractional recalls $= 49/3 \\approx 16.3333$ divided by $40$], and on the **678 TEST single-label views**, $\\text{Hit@}10 = \\text{Macro Recall@}10 = 42.92\\%$ [`291/678`]; in the exploratory **TEST+DEV combined cohort** [$N=756$: `712` single-GT + `44` multi-GT], the **44 multi-label views** achieve $\\text{Hit@}10 = 72.73\\%$ [`32/44`] vs. $\\text{Macro Recall@}10 = 39.02\\%$ [sum of fractional recalls $= 103/6$ divided by $44$], and the **712 single-label views** achieve $43.40\\%$ [`309/712`]). Comparing post-retrieval sample strata at $k=10$ (Table 8, Figure 5) shows:"
        ),
    )
    ins_4_3.add_bullet("**Retrieved Stratum ($Y_i \\cap R_{i,10} \\neq \\emptyset$, $N=321$):** Downstream attribution accuracy in this subset is **$P(\\text{Correct}\\mid Y_i \\cap R_{i,10} \\neq \\emptyset) = 91.28\\%$ (`293/321`)**, with 28 downstream selection discrepancies.")
    ins_4_3.add_bullet("**Missed Stratum ($Y_i \\cap R_{i,10} = \\emptyset$, $N=397$):** Downstream attribution accuracy in this subset is **$P(\\text{Correct}\\mid Y_i \\cap R_{i,10} = \\emptyset) = 70.03\\%$ (`278/397`)**, with **119 misclassifications** (an observed between-stratum difference of $21.25\\text{ pp}$).")
    ins_4_3.add_bullet("**Error Co-occurrence Locus:** At $k=10$, **119 of 147 classification errors (80.95%)** co-occurred with retrieval misses. This strong observational association motivates retrieval-focused ablations without claiming direct interventional causality.")

    ins_4_3.add_subheading("3. Analysis of RQ3: Token Volume vs. Cost Scaling, Latency, and Ledger Reconciliation")
    ins_4_3.add_p(
        text=(
            "As retrieval depth increases from `no_rag` to `rag_k10` (Table 9, Figures 6–7), we explicitly separate **input token volume scaling** from **monetary cost scaling**:"
        ),
    )
    ins_4_3.add_bullet(
        "**Input & Output Token Scaling:** Aggregate input tokens across the 1,280 TEST views scale **7.58-fold** from **863,139** (`674.3` tokens/req in `no_rag`) to **6,546,274** (`5,114.3` tokens/req in `rag_k10`), while mean output tokens (including internal reasoning) scale **2.04-fold** from **163.6** (`209,466` total) to **333.9** (`427,346` total) tokens/req."
    )
    ins_4_3.add_bullet(
        "**Token-Usage Cost vs. Conservative Ledger Spend (`rag_k1` vs. `rag_k3` Reconciliation):** Across all 1,280 logical TEST requests per condition (tariff-derived accounted costs under `config/pricing_v1.json`), both token-usage estimated cost and conservative ledger spend scale **4.60-fold** from **USD 0.4671** (`$0.46714395`, `$0.000365`/query) in `no_rag` to **USD 2.1494** (`$2.14938370`, `$0.001679`/query) in `rag_k10` (with `rag_k3` at **USD 1.1789** [`$1.17888000`] and `rag_k5` at **USD 1.4831** [`$1.48311775`]). Notably, in Table 9, `rag_k1` exhibits a higher conservative ledger spend (**USD 1.29723350** $\\approx$ **USD 1.30**) than `rag_k3` (**USD 1.17888000** $\\approx$ **USD 1.18**) despite consuming 42.6% fewer input tokens (`1,595,554` vs. `2,780,640`). Audit of `budget_ledger.json` and `request_journal.jsonl` (lines `48476–48485`) explains this exact reconciliation: across the 6,400 logical requests, there were **6,401 physical API attempts**, with the single extra attempt occurring on `(\"view_d870d574\", \"rag_k1\")` (`rag_k1_predictions.jsonl` line `1078`). Because the failed initial attempt on `view_d870d574` did not return a provider usage receipt, the financial guard (Protocol D5) conservatively retained its full worst-case pre-dispatch reservation hold of **USD 0.53974560** alongside the net token-usage cost of **USD 0.75748790** (pre-credit `token_usage_estimated_cost_usd` $\\text{USD } 0.75784210$ less $\\text{USD } 0.00035420$ observed cache credit), summing to $\\text{USD } 0.75748790 + \\text{USD } 0.53974560 = \\text{USD } 1.29723350$. All 13 `INCOMPLETE` responses reaching the 8,192 output token limit occurred exclusively in non-scorable views (11 unmapped, 2 ambiguous). Total canonical conservative ledger spend was **USD 6.57575890** (**USD 6.62839900** total committed spend including the **USD 0.05264010** pilot hold), leaving **USD 13.36160100** (66.84%) in uncommitted budget beneath the **USD 19.99** ceiling."
    )

    # 4.4. Interpretation of Results (P230) — Review Points 1.2, 1.5, 3, 5.4 (Worked Example) Fixed
    _, p_4_4 = find_paragraph_by_exact_or_prefix(doc, "Interpretation of Results", start_idx=225)
    ins_4_4 = CursorInserter(doc, p_4_4._p)
    ins_4_4.add_p(
        text="Four core observational patterns and a concrete multi-view worked example illuminate the empirical results observed in Chapter 4 (noting that these patterns are consistent with hypotheses involving lexical mismatch, competing retrieved techniques, and context dilution, while the present observational diagnostics do not isolate these mechanisms causally):"
    )
    ins_4_4.add_numbered_item("1.", "**Candidate Pool Size and $k=1$ Distractor Co-occurrence (`77.02%` vs. `77.99%` No-RAG):** Because `Hit@1` is only 3.76% (27/718), in **96.24% (691/718)** of scorable views at `rag_k1`, the single injected document does not match the ground-truth technique. Presenting a single non-matching ATT&CK document coincides with an observed $-0.975\\text{ pp}$ accuracy dip relative to `no_rag`, whereas expanding the candidate pool to $k \\ge 3$ (`Hit@3 = 16.43%`, `Hit@10 = 44.71%`) coincides with higher observed accuracy (`78.55%` $\\to$ `79.53%`), consistent with the hypothesis that broader candidate sets mitigate single-document distraction.")
    ins_4_4.add_numbered_item("2.", "**Reconciling the 21.25 pp Between-Stratum Difference with the +1.532 pp Marginal Difference:** First, `gpt-5.6-luna` (`xhigh`) already exhibits high baseline accuracy on Windows attack commands (`77.99%` No-RAG baseline, and `70.03%` in the missed stratum at $k=10$). Second, because the dense bi-encoder misses the ground truth in **55.29% (397/718)** of views at $k=10$, retrieved ground-truth definitions are present in less than half of the benchmark, which is consistent with the modest marginal end-to-end difference.")
    ins_4_4.add_numbered_item("3.", "**Per-Technique Retrieval Breakdown — Scorable TEST ($N=718$) vs. Combined TEST+DEV ($N=756$, T20):** To prevent any conflation between the 718 scorable TEST cohort and the 756-view combined TEST+DEV diagnostic cohort reported in `reports/T20_retrieval_diagnostics.md` (718 TEST + 38 scorable DEV views), we report both cohorts side-by-side: on the **718 scorable TEST cohort** (with combined TEST+DEV T20 rates in parentheses), `T1685.005` achieves **98.33% Hit@10 (`59/60` TEST; `98.39%`, `61/62` TEST+DEV)**, `T1547.001` achieves **92.86% (`91/98` TEST; `92.45%`, `98/106` TEST+DEV)**, `T1059.001` achieves **68.22% (`73/107` TEST; `68.14%`, `77/113` TEST+DEV)**, `T1053.005` achieves **47.06% (`40/85` TEST; `45.16%`, `42/93` TEST+DEV)**, and `T1543.003` achieves **31.48% (`34/108` TEST; `30.70%`, `35/114` TEST+DEV)**. Conversely, `T1105` (*Ingress Tool Transfer*) achieves **16.67% Hit@10 (`18/108` TEST; `15.79%`, `18/114` TEST+DEV)** (where competing LOLBin techniques such as `T1218.012` *Verclsid* rank #1 in 42.1% of T20 `T1105` views), `T1059.003` achieves **14.02% (`15/107` TEST; `17.12%`, `19/111` TEST+DEV)**, and `T1136.001` (*Create Account: Local Account*) exhibits **0.00% Hit@10 (`0/95` TEST; `0/99` TEST+DEV)**. Specifically, across the **95 TEST views** with ground truth `T1136.001`, **70 views** contain Security `EventID=4720` across unordered EventID set combinations (`10` single-event `{4720}` views, `38` contextual `{4688, 4720}` views [comprising both temporal orderings], `12` contextual `{1, 4720}` views, and `10` contextual `{13, 4720}` views, where `EventID=4720` records contain the 6 allowlisted schema fields `TimeCreated`, `Computer`, `EventID`, `TargetUserName`, `SubjectUserName`, and `SubjectLogonId`), while **25 single-event views** contain process-creation telemetry without `EventID=4720` (`13` Security `EventID=4688` views and `12` Sysmon `EventID=1` views, such as `New-LocalUser` in `view_02aac5b1`). These low retrieval rates are consistent with hypotheses of lexical mismatch and competing LOLBin descriptions, without isolating a single mechanism causally.")
    ins_4_4.add_numbered_item("4.", "**Multi-Event Retrieval Rank Shifts — Scorable TEST Pairs ($N=278$) vs. Combined TEST+DEV Pairs ($N=296$, T20):** Under the Top-10-censored rank comparison rule (`comparison_rank = rank if found else 11` for each pair's anchor technique), on the **278 complete scorable TEST pairs**, multi-event contextual views exhibit a **worse (larger) anchor-technique `comparison_rank` in 21.58% of pairs (`60/278`)**, a **better (smaller) rank in 7.55% (`21/278`)**, and a **tied `comparison_rank` in 70.86% (`197/278`, comprising `58` pairs tied at a finite Top-10 rank `1..10` and `139` pairs absent from Top-10 [`rank = 11`] in both views)**. In the exploratory combined TEST+DEV diagnostic cohort (**296 anchor pairs** in `reports/T20_retrieval_diagnostics.md`, comprising 278 TEST + 18 DEV pairs), contextual views exhibit a worse rank in **21.96% (`65/296`)**, a better rank in **7.77% (`23/296`)**, and a tied `comparison_rank` in **70.27% (`208/296`, comprising `61` finite-rank ties and `147` absent-in-both ties)**. This asymmetry is consistent with a context-dilution hypothesis when multi-event windows are pooled into a single 384-d `all-MiniLM-L6-v2` vector, though observational rank comparisons do not isolate background-event dilution causally.")

    ins_4_4.add_subheading("5. Concrete End-to-End Worked Examples From Canonical Artifacts (`view_0265275a`, `view_02aac5b1` & `view_0f68fd96`)")
    ins_4_4.add_p(
        text=(
            "To illustrate the exact mechanics of dense retrieval, taxonomy evolution recovery, distractor co-occurrence, and `T1136.001` retrieval misses on verbatim benchmark records from `data/ground_truth/synthetic/inference.jsonl` (where every displayed `endpoint_evidence` JSON array below is programmatically serialized via `json.dumps(json.loads(record[\"endpoint_evidence\"]), indent=2)` directly from `inference.jsonl` with zero added or omitted keys), `artifacts/retrieval/retrieval_diagnostics.jsonl`, and `artifacts/results/predictions/`, consider three scorable TEST views:"
        ),
    )
    import json
    inf_path = Path(r"C:\Users\hahoa\.codex\artifacts\rag2attck\finalization_repo_20261003\data\ground_truth\synthetic\inference.jsonl")
    inf_records = {}
    for _line in inf_path.read_text(encoding="utf-8").splitlines():
        if _line.strip():
            _obj = json.loads(_line)
            if _obj.get("sample_id") in {"view_0265275a", "view_02aac5b1", "view_0f68fd96"}:
                _ev = json.loads(_obj["endpoint_evidence"])
                _dumped = json.dumps(_ev, ensure_ascii=False, indent=2)
                assert json.loads(_dumped) == _ev
                inf_records[_obj["sample_id"]] = _dumped

    ins_4_4.add_code_block(
        "# Case 1: Treatment-Win Discordant View via RAG at k >= 3 (sample_id='view_0265275a', contextual, GT=['T1685.005'])\n"
        "# Exact endpoint_evidence JSON array from data/ground_truth/synthetic/inference.jsonl:\n"
        + inf_records["view_0265275a"] + "\n"
        "# FAISS Top-5 Retrieved Ranks: #1 T1547.004 (0.4031), #2 T1546.009 (0.4001), #3 T1685.005 (0.4000, active v19.2 ID),\n"
        "#   #4 T1685.001 (0.3977), #5 T1218.010 (0.3620)\n"
        "# Model Predictions across Conditions (1 of b=83 treatment-win discordant views at k=10):\n"
        "#   no_rag -> 'T1070.001' (Incorrect: retired pre-v19.2 ID) | rag_k1 -> 'T1070.001' (Incorrect: Rank #1 is T1547.004)\n"
        "#   rag_k3 -> 'T1685.005' (CORRECT: T1685.005 enters at Rank #3) | rag_k5 -> 'T1685.005' | rag_k10 -> 'T1685.005'"
    )
    ins_4_4.add_code_block(
        "# Case 2: Baseline-Win Regression on Single-Event Process Creation (sample_id='view_02aac5b1', single, GT=['T1136.001'])\n"
        "# Exact endpoint_evidence JSON array from data/ground_truth/synthetic/inference.jsonl (all 15 keys verbatim):\n"
        + inf_records["view_02aac5b1"] + "\n"
        "# FAISS Top-5 Retrieved Ranks: #1 T1547.004 (0.4334), #2 T1003.002 (0.3863), #3 T1059.001 (0.3711, PowerShell),\n"
        "#   #4 T1216.001 (0.3651), #5 T1556.008 (0.3645)  --> GT 'T1136.001' ABSENT from Top-10 (0/95 TEST views)\n"
        "# Model Predictions across Conditions (1 of c=72 baseline-win discordant regressions at k=10):\n"
        "#   no_rag -> 'T1136.001' (CORRECT) | rag_k1 -> 'T1136.001' (CORRECT)\n"
        "#   rag_k3 -> 'T1059.001' (Incorrect: changes to T1059.001 at k>=3 as Rank #3 PowerShell enters context under miss;\n"
        "#              consistent with context distraction without isolating single cause) | rag_k5, rag_k10 -> 'T1059.001'"
    )
    ins_4_4.add_code_block(
        "# Case 3: EventID 4720 Account-Creation View (sample_id='view_0f68fd96', single, GT=['T1136.001'])\n"
        "# Exact endpoint_evidence JSON array from data/ground_truth/synthetic/inference.jsonl (all 6 keys verbatim):\n"
        + inf_records["view_0f68fd96"] + "\n"
        "# FAISS Top-5 Retrieved Ranks: #1 T1685.005 (0.1624), #2 T1685.001 (0.1438), #3 T1217 (0.1412), #4 T1087.001 (0.1326),\n"
        "#   #5 T1124 (0.1298)  --> GT 'T1136.001' ABSENT from Top-10; all conditions predict 'T1136.001' (CORRECT despite miss)"
    )

    # 4.5. Comparison with Literature (P231) — Review Point 1.5 Fixed (Non-causal comparative framing)
    _, p_4_5 = find_paragraph_by_exact_or_prefix(doc, "Comparison with Literature", start_idx=225)
    ins_4_5 = CursorInserter(doc, p_4_5._p)
    ins_4_5.add_p(
        text=(
            "Comparing RAG2ATT&CK's empirical findings against the eight audited comparators highlights why domain-specific evaluation controls are essential:"
        ),
    )
    ins_4_5.add_bullet("**Contrast with CloudTrail RAG (Adediran et al., 2026) [10]:** Whereas Adediran et al. reported large end-to-end RAG gains on 200 AWS CloudTrail events using Gemini 2.5 Pro and a two-step query-expansion pipeline on Vertex AI, our single-step dense retrieval on raw Windows logs with `gpt-5.6-luna` yields a modest, statistically non-significant $+1.532\\text{ pp}$ accuracy difference alongside a $+0.001415$ Macro-F1 difference. Because the two studies differ across telemetry domain, model family, and retrieval pipeline architecture, this contrast suggests the hypothesis—rather than proving causally in isolation—that single-step dense retrieval over raw Windows OS fields faces a steeper lexical-semantic representation gap than query-expanded cloud API logs.")
    ins_4_5.add_bullet("**Alignment with CTI Distractor Findings (TechniqueRAG [5] & H-TechniqueRAG [6]):** Our observation that `rag_k1` dips slightly below `no_rag` ($-0.975\\text{ pp}$) when the top-1 miss rate is 96.24%, while accuracy in the retrieved stratum reaches 91.28%, is consistent with the distractor-sensitivity patterns reported by Morbiato et al. [6] on unstructured CTI prose.")
    ins_4_5.add_bullet("**Advancement over Fixed-Cutoff Telemetry Studies (Trace2ATT&CK [11], CAM-LDS [8], LADE [12]):** Unlike Trace2ATT&CK [11] (which fixes both retriever depth and output cutoff at 5 on Linux eBPF graphs) and CAM-LDS [8] / LADE [12] (which vary output cutoff `Top-k` without RAG), RAG2ATT&CK's decoupled ablation across $k \\in \\{1, 3, 5, 10\\}$ separately characterizes input token growth (7.58x at $k=10$), ledger cost scaling (4.60x at $k=10$), sample-level $\\text{Hit@}k$ (44.71% at $k=10$), and multi-label $\\text{Macro Recall@}k$ (42.80% at $k=10$).")

    # 4.6. Implications of the Results (P232) — Review Points 1.5, 1.6, 3 Fixed
    _, p_4_6 = find_paragraph_by_exact_or_prefix(doc, "Implications of the Results", start_idx=225)
    ins_4_6 = CursorInserter(doc, p_4_6._p)
    ins_4_6.add_p(
        text=(
            "For SOC architects and cybersecurity AI practitioners, our diagnostic findings motivate three testable engineering hypotheses for production RAG design:"
        ),
    )
    ins_4_6.add_numbered_item("1.", "**Prioritize Retrieval Engineering Before Scaling Context Windows:** Because 80.95% (`119/147`) of errors at $k=10$ co-occur with retrieval misses—while accuracy in the retrieved stratum reaches 91.28%—expanding context depth from $k=0$ to $k=10$ increases input token volume by **7.58x** and monetary cost by **4.60x** while leaving 55.29% of queries without ground-truth context. Improving upstream candidate recall is therefore the highest-leverage intervention to test next.")
    ins_4_6.add_numbered_item("2.", "**Test Hybrid Lexical-Dense Retrieval and Schema Translation for Windows Event IDs:** Off-the-shelf general-purpose bi-encoders (`all-MiniLM-L6-v2`) achieved `0.00% Hit@10` (`0/95` TEST views) on `T1136.001` across both the 70 views containing Security `EventID=4720` (`TimeCreated`, `Computer`, `EventID`, `TargetUserName`, `SubjectUserName`, `SubjectLogonId`) and the 25 single-event process-creation views (`13` `EventID=4688` + `12` `EventID=1`). Consistent with a lexical-mismatch hypothesis, this motivates testing hybrid sparse-dense retrieval (BM25 + dense embeddings with cross-encoder reranking) and schema-aware query expansion mapping Event IDs to canonical ATT&CK concepts.")
    ins_4_6.add_numbered_item("3.", "**Evaluate Event Salience Pre-Filtering to Address Multi-Event Rank Shifts:** Because multi-event contextual views exhibited worse anchor retrieval ranks nearly 3x more often than better ranks (`21.58%` [`60/278`] worse vs. `7.55%` [`21/278`] better on TEST; `21.96%` [`65/296`] vs. `7.77%` [`23/296`] on TEST+DEV), consistent with a context-dilution hypothesis, SOC pipelines should evaluate per-event scoring or salience pre-filtering prior to vector encoding.")

    # ==========================================================================
    # 11. CHAPTER 5: DISCUSSION (P234..P237) — Review Points 1.1, 1.3, 4 Fixed
    # ==========================================================================
    _, p_5_1 = find_paragraph_by_exact_or_prefix(doc, "Research Objectives Revisited", start_idx=234)
    ins_5_1 = CursorInserter(doc, p_5_1._p)
    ins_5_1.add_p(
        text=(
            "This study set out to resolve a critical empirical question in AI-assisted Security Operations: *When every confounding variable—requested language model alias (`gpt-5.6-luna`), reasoning settings (`reasoning_effort=xhigh`, `max_output_tokens=8192`), prompt wording (`prompts/baseline_v1.txt`), and knowledge base snapshot (MITRE ATT&CK Enterprise v19.2, 474 active Windows techniques)—is held strictly constant, does grounding the model in retrieved ATT&CK reference documents significantly improve exact technique and sub-technique attribution from Windows endpoint logs over unaugmented zero-shot reasoning (RQ1), how do upstream retrieval misses versus downstream selection discrepancies co-occur with end-to-end errors (RQ2), and what are the operational trade-offs across retrieval depths $k \\in \\{1, 3, 5, 10\\}$ (RQ3)?*"
        ),
    )
    ins_5_1.add_p(
        text=(
            "By executing 6,400 controlled inference requests across the leakage-scrubbed `synthetic-paired-v1` benchmark under Frozen Protocol v1.1 (`D1–D7`), this thesis answered all three Research Questions with full statistical and cryptographic auditability, demonstrating that scientific value in empirical cybersecurity research rests on rigorous hypothesis testing and failure decomposition rather than claiming an artificial 'win' for RAG."
        ),
    )

    # 5.2. Summary of Key Findings (P237) — Review Points 1.1, 1.3, 1.4, 1.6 Fixed
    _, p_5_2 = find_paragraph_by_exact_or_prefix(doc, "Summary of Key Findings", start_idx=234)
    ins_5_2 = CursorInserter(doc, p_5_2._p)
    ins_5_2.add_subheading("1. Synthesis of Empirical Findings Across RQ1–RQ3")
    ins_5_2.add_bullet("**RQ1 (Metric-Specific Statistical Findings Under Strong Parametric Baseline):** `rag_k10` achieved the highest point accuracy (`79.53%`, 474-class Macro-F1 `0.014024`) over `no_rag` (`77.99%`, Macro-F1 `0.012608`), while `rag_k1` dipped slightly in accuracy to `77.02%` ($-0.975\\text{ pp}$). At $k=10$, the accuracy difference ($+1.532\\text{ pp}$, 95% cluster-bootstrap CI $[-2.355\\text{ pp}, +5.300\\text{ pp}]$, unclustered exact McNemar $p = 0.4219$) was not statistically significant, whereas the 474-class Macro-F1 difference was $+0.001415$ with a 95% cluster-bootstrap CI of $[+0.001011, +0.001792]$ (and likewise excluded zero at $k=3$ and $k=5$).")
    ins_5_2.add_bullet("**RQ2 (Upstream Retrieval Miss Co-occurrence & Hit@k vs. Recall@k):** On the 718 scorable TEST views, standalone dense retrieval achieved $\\text{Hit@}10 = 44.71\\%$ (`321/718`) and multi-label $\\text{Macro Recall@}10 = 42.80\\%$, missing all ground-truth techniques in **55.29% (397/718)** of views. Accuracy in the retrieved stratum was **91.28% (293/321)** versus **70.03% (278/397)** in the missed stratum, with **80.95% (119/147)** of `rag_k10` classification errors co-occurring with retrieval misses.")
    ins_5_2.add_bullet("**RQ3 (Token Volume, Cost Reconciliation, and Operational Reliability):** Input token volume grew **7.58x** from `no_rag` to `rag_k10`, while tariff-derived token-usage and ledger cost across all 1,280 logical requests/condition grew **4.60x** from `$0.4671` (`$0.000365`/query) to `$2.1494` (`$0.001679`/query; with `rag_k3` at `$1.1789` and `rag_k5` at `$1.4831`); `rag_k1` recorded `$0.7578` pre-credit usage cost (`$0.7575` net of `$0.00035420` cache credit) and `$1.2972` in conservative ledger spend due to one retained `$0.5397` worst-case hold on `view_d870d574`. Median latency remained stable (`2.30s` to `2.87s`; earlier DEV pilot mean latency of `8.13s` across 20 calibration requests is distinguished as an exploratory artifact). Total study conservative ledger spend was **USD 6.5758** (**USD 6.6284** total committed) within the **USD 19.99** ceiling, with 0% provider or parse failures in the 718 scorable cohort.")

    ins_5_2.add_subheading("2. Synthetic Data Boundaries, Ground-Truth Governance, and Runtime Infrastructure Disclosure")
    ins_5_2.add_p(
        text=(
            "**Synthetic Data Boundaries & Public Telemetry Governance:** While `synthetic-paired-v1` isolates retrieval mechanics cleanly, synthetic templates lack the extreme background noise, custom administrative scripts, and adversarial obfuscation of live enterprise networks. Furthermore, our Task 2 forensic discovery of 15,713 cell discrepancies in the Mendeley v3 Windows-APT dataset [13] underscores a broader lesson for cybersecurity machine learning: public telemetry benchmarks must never be ingested without cell-level reconciliation and cryptographic provenance verification."
        ),
    )
    ins_5_2.add_p(
        text=(
            "**Runtime Launcher & Infrastructure Resilience Disclosure:** To ensure full engineering transparency, we disclose all runtime harnesses used during execution: (1) the authenticated live execution launcher verified against SHA-256 `05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa`; (2) a Windows atomic file-locking resilience wrapper (`12` retries with deterministic exponential backoff `delay = 0.05 * (1.5 ** attempt)`) mitigating transient `WindowsError 5 / 32` exceptions during sequential ledger writes; (3) the `scripts/run_offline_tests.py` socket-monkeypatch `OFFLINE_GUARD` verifying zero external network egress during replay; and (4) the sequential runner `src/experiment/runner.py` (`concurrency = 1`)."
        ),
    )

    ins_5_2.add_subheading("3. Threats to Validity")
    ins_5_2.add_bullet("**Internal Validity, Bitwise Determinism & Model Provenance (Decision D3):** Mitigated via strict field whitelisting (`INFERENCE_ALLOWLIST`), byte-identical prompts, and deterministic FAISS tie-breaking. Bitwise determinism holds 100% for dataset regeneration, FAISS indexing, and discrete evaluation counts; across repeated 1,000-resample bootstrap runs (`seed=42`), all integer counts are invariant, arithmetic invariants hold within $< 10^{-12}$, and the 4 Macro-CI endpoints exhibit floating-point variation $< 6 \\times 10^{-18}$. Regarding API provenance (`run_provenance.json`), the requested model alias (`gpt-5.6-luna`) and inference configuration were fixed across conditions and timestamped response IDs (`has_response_ids: true`, `has_timestamps: true`) were retained; however, an immutable backend model version (`model_version: null`) and system fingerprints (`system_fingerprints: []`) were not provided by the upstream API under policy `ALLOW_LATEST_WITH_TIMESTAMP_BINDING`.")
    ins_5_2.add_bullet("**Statistical Validity, Cluster Dependence & Multiple Comparisons:** Exact McNemar tests at $N=718$ (and $N=278$) treat view-level discordant pairs as independent binary trials without cluster adjustment and are reported unadjusted for multiple comparisons across $k \\in \\{1, 3, 5, 10\\}$. Accordingly, nominal 95% cluster-bootstrap CIs over the 440 scenario clusters (`cluster_unit: pair_id`, `NO_MULTIPLE_COMPARISON_CORRECTION_PRE_SPECIFIED_PRIMARY_CONTRASTS`, treating between-pair independence across template-derived synthetic pairs as a modeling assumption) serve as the primary cluster-aware statistical reference for both Accuracy and 474-class Macro-F1.")
    ins_5_2.add_bullet("**External Validity & Sparse Class Census:** Positive ground truth in TEST covers 8 active Windows techniques (768 annotations across 718 views), leaving 466 classes in the 474-technique universe with zero support. Generalization to the remaining 466 techniques, other LLM families, or production SOC telemetry cannot be claimed without empirical validation.")
    ins_5_2.add_bullet("**Construct Validity & Scenario Label Shift:** Multi-label `ANY_MATCH` scoring (D2a) is supplemented by separate single-GT ($N=678$) and multi-GT ($N=40$) accuracy reporting, as well as separate sample-level $\\text{Hit@}k$ and fractional $\\text{Macro Recall@}k$ metrics. Moreover, as shown in Section 4.3, the 40 label-divergent multi-stage pairs confound direct attribution of single-vs-contextual differences to context windowing alone.")

    # ==========================================================================
    # 12. CHAPTER 6: CONCLUSION AND FUTURE WORK (P239..P242) — All Review Points Fixed
    # ==========================================================================
    _, p_6_1 = find_paragraph_by_exact_or_prefix(doc, "Conclusion", start_idx=239)
    ins_6_1 = CursorInserter(doc, p_6_1._p)
    ins_6_1.add_p(
        text=(
            "This Capstone Project Thesis presented **RAG2ATT&CK**, a controlled replication-and-extension empirical study evaluating MITRE ATT&CK-grounded Retrieval-Augmented Generation for exact technique and sub-technique attribution from Windows endpoint telemetry under Scientific Protocol v1.1. Across 6,400 canonical live dispatches (`718` scorable TEST views) using the fixed `gpt-5.6-luna` model alias (`reasoning_effort=xhigh`), `all-MiniLM-L6-v2`, and a FAISS `IndexFlatIP` index over 474 active Windows techniques from MITRE ATT&CK Enterprise v19.2, our study establishes three primary conclusions:"
        ),
    )
    ins_6_1.add_numbered_item("1.", "**Attribution Efficacy Across Accuracy and 474-Class Macro-F1 (RQ1):** At $k=10$, RAG achieved the highest point accuracy (`79.53%` vs. `77.99%` for unaugmented `no_rag`, $\\Delta\\text{Acc} = +1.532\\text{ pp}$, 95% cluster-bootstrap CI $[-2.355\\text{ pp}, +5.300\\text{ pp}]$, unclustered exact McNemar $p = 0.4219$), indicating that the accuracy difference was not statistically significant. Concurrently, the 474-class Macro-F1 difference at $k=10$ was $+0.001415$ (`0.014024` vs. `0.012608`), with a 95% cluster-bootstrap CI of $[+0.001011, +0.001792]$ (and positive CIs excluding zero at $k=3$ and $k=5$), interpreted under our multiple-comparison disclosure and the sparse 8-of-474 class-support ceiling.")
    ins_6_1.add_numbered_item("2.", "**Retrieval Miss Co-occurrence as the Dominant Bottleneck (RQ2):** On the 718 scorable TEST views, standalone dense retrieval achieved sample-level $\\text{Hit@}10 = 44.71\\%$ (`321/718`) and multi-label $\\text{Macro Recall@}10 = 42.80\\%$, failing to retrieve any ground-truth technique in **55.29% (397/718)** of views (including a **0.00% Hit@10** blind spot on `T1136.001` across all 95 TEST views). Accuracy in the retrieved stratum reached **91.28% (293/321)** versus **70.03% (278/397)** in the missed stratum, with **80.95% (119/147)** of `rag_k10` classification errors co-occurring with retrieval misses.")
    ins_6_1.add_numbered_item("3.", "**Representation Confounding, Cost Accountability, and Zero-Cost Reproducibility (RQ3):** Multi-event contextual views exhibited worse anchor retrieval ranks in **21.58% (`60/278`)** of complete scorable TEST pairs versus **7.55% (`21/278`)** improved (**21.96%, `65/296`** vs. **7.77%, `23/296`** in the combined TEST+DEV T20 cohort), while 80%–100% of net end-to-end contextual wins in `no_rag` and `rag_k1` occurred in 40 multi-stage label-divergent pairs. Operationally, input tokens scaled 7.58x and cost scaled 4.60x at $k=10$, with the full campaign completing at a conservative ledger spend of **USD 6.5758** (**USD 6.6284** total committed) under the **USD 19.99** guard, permanently archived in GitHub Release `v1.0.0-rag2attck-study` (`ca8d39824a72e80053371e208506bfdc6332dc5d`) for offline reproduction at USD 0.00 API cost.")

    # 6.2. Future Work (P242) — Review Points 1.5, 3 Fixed
    _, p_6_2 = find_paragraph_by_exact_or_prefix(doc, "Future Work", start_idx=239)
    ins_6_2 = CursorInserter(doc, p_6_2._p)
    ins_6_2.add_p(
        text="Building directly upon the observational diagnostics and bottlenecks identified in this thesis, we formulate four concrete hypotheses for future experimental validation:"
    )
    ins_6_2.add_numbered_item("1.", "**Hybrid Lexical-Dense Retrieval and Schema-Aware Query Expansion:** Evaluate whether combining sparse lexical matching (BM25 over Windows Event IDs, registry paths, and LOLBin command flags) with dense embeddings via Reciprocal Rank Fusion (RRF) and cross-encoder reranking—augmented by a schema translation layer mapping Windows Security Event ID `4720` attributes (`TimeCreated`, `Computer`, `EventID`, `TargetUserName`, `SubjectUserName`, `SubjectLogonId`) and local-account CLI patterns to canonical ATT&CK concepts (`T1136.001`)—improves recall on zero-hit techniques.")
    ins_6_2.add_numbered_item("2.", "**Automated Event Pre-Filtering to Test the Context-Dilution Hypothesis:** Test experimentally whether an upstream event salience filter or per-event max-pooling aggregator before vector encoding improves multi-event retrieval ranks compared to single-vector window pooling.")
    ins_6_2.add_numbered_item("3.", "**Verified Real-World Windows Enterprise Telemetry Benchmarking (Task T15 Follow-Up):** Construct and cryptographically seal a real-world Windows intrusion telemetry benchmark collected directly from live Caldera / Atomic Red Team range executions with raw EVTX/JSON provenance hashes, overcoming the 15,713 CSV export discrepancies discovered in Mendeley v3 [13].")
    ins_6_2.add_numbered_item("4.", "**Expanded Taxonomic Coverage and Multi-Model Cost-Tiered Routing:** Expand positive benchmark support from 8 techniques to 50+ Windows techniques across the 474-technique matrix, and evaluate a tiered SOC routing architecture pairing fast open-weight models (`Llama-3.3-70B`, `Qwen-3`) on high-confidence hits with frontier reasoning models (`gpt-5.6-luna`) reserved for ambiguous escalations.")

    # ==========================================================================
    # 13. REFERENCES (P245..P247)
    # ==========================================================================
    _, p_ref_heading = find_paragraph_by_exact_or_prefix(doc, "REFERENCES", start_idx=244)
    ins_ref = CursorInserter(doc, p_ref_heading._p)
    for ref_num, ref_text in REFERENCES_LIST:
        ins_ref.add_numbered_item(ref_num, ref_text, hanging_in=0.38)

    # ==========================================================================
    # 14. APPENDICES (P249..P250) — Review Points 1.7 & 5.3 Fixed (Tables 11..14)
    # ==========================================================================
    _, p_app_heading = find_paragraph_by_exact_or_prefix(doc, "APPENDICES", start_idx=248)
    ins_app = CursorInserter(doc, p_app_heading._p)
    ins_app.add_subheading("Appendix A: Cryptographic Reproducibility Manifest and Certified Execution Lineage")
    ins_app.add_p(
        text=(
            "In adherence to open-science principles, all code, configurations, corpora, and execution artifacts of the RAG2ATT&CK study (`https://github.com/habachcp6/RAG2ATTCK`, Release `v1.0.0-rag2attck-study`) are bound to immutable SHA-256 digests in Table 11 and Table 12."
        ),
    )
    ins_app.add_table(
        "Table 11: Cryptographic Reproducibility Manifest.",
        TABLE_11_MANIFEST,
        table_id="table_11",
        bm_name="_Ref_tbl_11",
        custom_widths=[1.60, 1.80, 0.90, 2.20],
    )
    ins_app.add_table(
        "Table 12: Supplementary Execution Provenance (Canonical Run Mode).",
        TABLE_12_PROVENANCE,
        table_id="table_12",
        bm_name="_Ref_tbl_12",
        custom_widths=[1.60, 1.80, 0.90, 2.20],
    )
    ins_app.add_p(
        text="Independent auditors can reproduce all headline metrics, 1,000-resample cluster-bootstrap CIs, exact McNemar tests, and financial reconciliations offline at USD 0.00 API cost from `public_v4_candidate_20261003.zip` (SHA-256: `1d5f9f4bb2d50bbb885746fe4d26f34ca5af1cacdbcad7e0005c2af8ea1086c1`) using:"
    )
    ins_app.add_code_block(
        "python scripts/run_offline_tests.py -m scripts.reproduce_canonical_study \\\n"
        "  --bundle-dir <package-root> \\\n"
        "  --repository-root <checkout> \\\n"
        "  --output-dir <new-output-dir> \\\n"
        "  --all"
    )

    ins_app.add_subheading("Appendix B: Eight-Week Capstone Implementation Roadmap (Planned vs. Actual Execution) and Risk Register")
    ins_app.add_p(
        text=(
            "Synchronized with the official Google Drive Project Tracker (`RAG_ATTCK_Project_Tracker_Updated`, 35/35 in-scope tasks completed, 1 task `T15` deferred out-of-scope per Protocol v1.1 Decision D6) and Research Plan (`RAG_ATTCK_Research_Plan_Updated`, Section 15 Scope Alignment Addendum), Table 13 explicitly distinguishes the **8-week syllabus planned schedule windows** (`W1–W8`, `15 Sep–9 Nov 2026`) from the **actual execution timestamps** (`run_provenance.json` `2026-10-02T03:43:44Z`, evaluation bundle freeze `03 Oct 2026`, and documentation/release freeze `19–30 Oct 2026`, completed ahead of the planned `W5–W8` windows). Table 14 documents the project risk register and implemented reproducibility controls."
        ),
    )
    ins_app.add_table(
        "Table 13: Eight-Week Capstone Implementation Roadmap: Planned Window vs. Actual Execution Timestamps.",
        TABLE_13_ROADMAP,
        table_id="table_13",
        bm_name="_Ref_tbl_13",
        custom_widths=[0.88, 0.92, 0.52, 1.98, 1.42, 0.78],
    )
    ins_app.add_table(
        "Table 14: Risk Register, Severity Assessment, and Reproducibility Mitigation Controls.",
        TABLE_14_RISKS,
        table_id="table_14",
        bm_name="_Ref_tbl_14",
        custom_widths=[1.50, 0.80, 4.20],
    )

    # Remove template instructional prefix, sample Figure 1 / Table 1, and instructional prompts
    sdt_toc_list = body_el.xpath("./w:sdt")
    if sdt_toc_list:
        sdt_c = sdt_toc_list[0].find(qn("w:sdtContent"))
        if sdt_c is not None:
            for ch in list(sdt_c):
                ch_txt = "".join(ch.xpath(".//w:t/text()")).strip()
                if "List all major sections and sub-sections" in ch_txt:
                    sdt_c.remove(ch)

    for el in prefix_elements:
        if el.getparent() is not None:
            el.getparent().remove(el)
    if sample_table_3.getparent() is not None:
        sample_table_3.getparent().remove(sample_table_3)
    for p_el in instructional_paragraphs:
        if p_el.getparent() is not None:
            p_el.getparent().remove(p_el)

    # Mark TOC fields dirty and set w:updateFields in settings.xml so Word updates fields on open
    for fld in doc.element.xpath("//w:fldSimple"):
        fld.set(qn("w:dirty"), "true")

    settings_el = doc.settings.element
    if not settings_el.xpath("./w:updateFields"):
        upd = OxmlElement("w:updateFields")
        upd.set(qn("w:val"), "true")
        settings_el.append(upd)

    initial_out = SCRATCH_DIR / "_initial_populated_v2.docx"
    initial_out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(initial_out))
    print(f"Saved initial populated thesis document to: {initial_out} ({initial_out.stat().st_size:,} bytes)")

    update_docx_fields_and_export_pdf_via_word_com(initial_out, out_paths, pdf_out_path)


def update_docx_fields_and_export_pdf_via_word_com(initial_out: Path, out_paths: list[Path], pdf_out_path: Path):
    """Use an isolated Microsoft Word COM instance to repaginate, update TOC/LOF/LOT/PAGEREF twice, and export PDF."""
    import win32com.client

    scratch_work = SCRATCH_DIR / "_com_work_thesis_v2.docx"
    shutil.copy2(initial_out, scratch_work)
    scratch_resolved = scratch_work.resolve()

    # Set clean Core Properties before opening in Word COM so exported PDF & final DOCX both carry clean metadata
    pre_doc = docx.Document(str(scratch_resolved))
    cp = pre_doc.core_properties
    cp.author = "Hà Hoàng Bách (SE196277)"
    cp.last_modified_by = "Hà Hoàng Bách"
    cp.title = (
        "Evaluating MITRE ATT&CK-Grounded RAG for Technique Attribution "
        "from Windows Endpoint Logs: A Replication-and-Extension Study"
    )
    cp.subject = "HOD402 — RAG2ATT&CK Capstone Research Thesis (Supervisor: Hồ Hải)"
    cp.keywords = (
        "MITRE ATT&CK v19.2; Retrieval-Augmented Generation (RAG); "
        "Large Language Models (LLMs); Windows Endpoint Telemetry; Sysmon Logs; "
        "Threat Attribution; SOC; FAISS Dense Retrieval; "
        "Replication-and-Extension Study; Reproducible Evaluation"
    )
    cp.comments = "FPT University Information Assurance Capstone Project Thesis (HOD402) — Release v1.0.0-rag2attck-study"
    pre_doc.save(str(scratch_resolved))

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0

    wdoc = word.Documents.Open(
        str(scratch_resolved),
        ConfirmConversions=False,
        ReadOnly=False,
        AddToRecentFiles=False,
        Visible=False,
        OpenAndRepair=False,
        NoEncodingDialog=True,
    )
    try:
        # Two-pass repagination & field update so TOC length shifts never desync page numbers
        for _pass in range(2):
            wdoc.Repaginate()
            for toc_idx in range(1, wdoc.TablesOfContents.Count + 1):
                try:
                    wdoc.TablesOfContents(toc_idx).Update()
                except Exception:
                    pass
            wdoc.Repaginate()
            wdoc.Fields.Update()
            for sec_idx in range(1, wdoc.Sections.Count + 1):
                sec = wdoc.Sections(sec_idx)
                for hf_idx in range(1, 4):
                    try:
                        sec.Footers(hf_idx).Range.Fields.Update()
                        sec.Headers(hf_idx).Range.Fields.Update()
                    except Exception:
                        pass
        wdoc.Repaginate()
        wdoc.Save()
        if pdf_out_path:
            pdf_out_path.parent.mkdir(parents=True, exist_ok=True)
            # wdExportFormatPDF = 17
            wdoc.ExportAsFixedFormat(
                OutputFileName=str(pdf_out_path.resolve()),
                ExportFormat=17,
                OpenAfterExport=False,
                OptimizeFor=0,
                CreateBookmarks=1,
            )
            print(f"Exported verification PDF to: {pdf_out_path} ({pdf_out_path.stat().st_size:,} bytes)")
    finally:
        wdoc.Close(SaveChanges=0)
        word.Quit()

    for dst in out_paths:
        dst_res = dst.resolve()
        dst_res.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(scratch_resolved, dst_res)
        print(f"Updated fields & synced thesis document: {dst_res} ({dst_res.stat().st_size:,} bytes)")


def verify_filled_thesis_docx(docx_path: Path, pdf_path: Path = None):
    """Comprehensive multi-layer QA audit of the revised Thesis Document across all review items."""
    doc = docx.Document(str(docx_path))
    full_text = "\n".join(p.text for p in doc.paragraphs)
    table_texts = []
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                table_texts.append("".join(c._element.xpath(".//w:t/text()")))
    all_table_str = "\n".join(table_texts)

    errors = []

    # 1. Check revised headings (Review Point 4)
    required_headings = [
        "ABSTRACT",
        "Keywords",
        "ACKNOWLEDGEMENT",
        "LIST OF FIGURES",
        "LIST OF TABLES",
        "ABBREVIATIONS",
        "CHAPTER 1",
        "Background",
        "Problem Statement",
        "Research Objectives",
        "Significance of the Study",
        "Scope and Limitations",
        "Thesis Structure",
        "CHAPTER 2",
        "Review of Previous Studies",
        "Summary of the Literature Review",
        "Research Contributions",
        "CHAPTER 3",
        "Research Design",
        "Data Collection Methods",
        "Sampling and Data Analysis Techniques",
        "Limitations of the Methodology",
        "CHAPTER 4",
        "EXPERIMENTS AND RESULTS",
        "Introduction",
        "Presentation of Data",
        "Analysis of Results",
        "Interpretation of Results",
        "Comparison with Literature",
        "Implications of the Results",
        "CHAPTER 5",
        "Research Objectives Revisited",
        "Summary of Key Findings",
        "CHAPTER 6",
        "Conclusion",
        "Future Work",
        "REFERENCES",
        "APPENDICES",
    ]
    for req in required_headings:
        if req not in full_text:
            errors.append(f"Missing required revised heading: {req!r}")

    # 2. Verify forbidden legacy headings/placeholders are gone
    forbidden_strings = [
        "APPENDICES (If any)",
        "Restate the Research Problem or Objectives",
        "Summarize Key Findings",
        "Contribution of Research",
        "Sampling Data Analysis Techniques",
        "EXPERIMENTAL AND RESULTS",
        "Student’ ID:",
        "Table 0:",
        "Table 1a:",
        "Table 1b:",
        "Table 2a:",
        "Table 2b:",
        "Table 3b:",
        "Table 5b:",
        "Table 6b:",
    ]
    sdt_text = "".join(doc.element.body.xpath(".//w:sdt//w:t/text()"))
    for bad_s in forbidden_strings:
        if bad_s in full_text or bad_s in all_table_str or bad_s in sdt_text:
            errors.append(f"Forbidden legacy string still present: {bad_s!r}")

    # 3. Verify all key review additions (Review Points 1.1..1.7, 2.1..2.5, 3, 5.3, 5.4)
    required_review_fixes = [
        "Student’s ID:",
        "+0.001415",
        "+0.001011",
        "+0.001792",
        "98.33%",
        "59/60",
        "92.86%",
        "91/98",
        "16.67%",
        "18/108",
        "21.58%",
        "60/278",
        "7.55%",
        "21/278",
        "ALLOW_LATEST_WITH_TIMESTAMP_BINDING",
        "model_version: null",
        "42.80%",
        "2.95%",
        "15.48%",
        "22.96%",
        "0.75748790",
        "0.53974560",
        "73.50%, 80.17%",
        "75.00%, 81.74%",
        "75.07%, 82.35%",
        "2026-05-03T13:35:02Z",
        "2026-05-03T13:35:05Z",
        "2026-02-19T08:55:54Z",
        "view_0265275a",
        "view_02aac5b1",
        "TargetUserName",
        "SubjectUserName",
        "SubjectLogonId",
    ]
    combined_doc_str = full_text + "\n" + all_table_str
    for rf in required_review_fixes:
        if rf not in combined_doc_str:
            errors.append(f"Missing required review fix fact: {rf!r}")

    # 4. Verify zero raw LaTeX leakage outside code blocks
    tex_pattern = re.compile(r"\\[a-zA-Z]+|\$\$")
    for idx, p in enumerate(doc.paragraphs):
        is_code = any(r.font.name == "Consolas" for r in p.runs)
        if not is_code:
            m = tex_pattern.findall(p.text)
            if m:
                errors.append(f"Paragraph {idx} has raw LaTeX tokens {m}: {p.text[:100]!r}")

    for t_i, t in enumerate(doc.tables):
        for r_i, r in enumerate(t.rows):
            for c_i, c in enumerate(r.cells):
                c_txt = "".join(c._element.xpath(".//w:t/text()"))
                m = tex_pattern.findall(c_txt)
                if m:
                    errors.append(f"Table {t_i} [{r_i},{c_i}] has raw LaTeX tokens {m}: {c_txt[:80]!r}")

    # 5. Verify bookmarks for Figures 1..8 and Tables 1..14
    expected_bms = [f"_Ref_fig_{i}" for i in range(1, 9)] + [f"_Ref_tbl_{i}" for i in range(1, 15)]
    for bm_name in expected_bms:
        if not doc.element.xpath(f'//w:bookmarkStart[@w:name="{bm_name}"]'):
            errors.append(f"Missing bookmark {bm_name} in document")

    if errors:
        raise AssertionError("VERIFICATION FAILED:\n" + "\n".join(errors))

    print(
        f"=== DOCX QA VERIFICATION PASSED 100% ===\n"
        f"  File: {docx_path} ({docx_path.stat().st_size:,} bytes)\n"
        f"  Total Paragraphs: {len(doc.paragraphs)} | Total Tables: {len(doc.tables)}"
    )


if __name__ == "__main__":
    single_final = Path(r"C:\Users\hahoa\Downloads\HOD402_CP_StudentsGuideForm_RAG2ATTCK_HoanChinh.docx")
    pdf_final = Path(r"C:\Users\hahoa\Downloads\HOD402_CP_StudentsGuideForm_RAG2ATTCK_HoanChinh.pdf")
    output_targets = [single_final]
    populate_thesis_template(BACKUP_PATH, output_targets, pdf_final)
    for target in output_targets:
        verify_filled_thesis_docx(target, pdf_final)
