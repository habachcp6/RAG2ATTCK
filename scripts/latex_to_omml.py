"""LaTeX to OMML (Office OpenXML Math) Converter for Word (.docx).

Converts LaTeX mathematical expressions to native Word OMML (<m:oMath>, <m:f>, <m:sSub>, etc.).
"""

from __future__ import annotations

import re
import html
from xml.etree import ElementTree as ET


def extract_braced(s: str, start_brace_idx: int) -> tuple[str, int]:
    """Extract content inside matching braces {...} starting at start_brace_idx."""
    depth = 0
    content = []
    i = start_brace_idx
    while i < len(s):
        ch = s[i]
        if ch == "{":
            depth += 1
            if depth > 1:
                content.append(ch)
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return "".join(content), i + 1
            else:
                content.append(ch)
        else:
            if depth >= 1:
                content.append(ch)
        i += 1
    return "".join(content), len(s)


class LatexToOmml:
    """Converts LaTeX formulas to OpenXML Math (<m:oMath>)."""

    SYMBOL_MAP = {
        r"\Delta": "Δ",
        r"\to": "→",
        r"\in": "∈",
        r"\notin": "∉",
        r"\subseteq": "⊆",
        r"\subset": "⊂",
        r"\cap": "∩",
        r"\cup": "∪",
        r"\emptyset": "∅",
        r"\neq": "≠",
        r"\ne": "≠",
        r"\le": "≤",
        r"\leq": "≤",
        r"\ge": "≥",
        r"\geq": "≥",
        r"\approx": "≈",
        r"\sim": "~",
        r"\times": "×",
        r"\cdot": "·",
        r"\forall": "∀",
        r"\exists": "∃",
        r"\equiv": "≡",
        r"\land": "∧",
        r"\lor": "∨",
        r"\quad": "  ",
        r"\qquad": "    ",
        r"\,": " ",
        r"\;": " ",
        r"\:": " ",
        r"\!": "",
        r"\left(": "(",
        r"\right)": ")",
        r"\left[": "[",
        r"\right]": "]",
        r"\left\{": "{",
        r"\right\}": "}",
        r"\{": "{",
        r"\}": "}",
        r"\_": "_",
        r"\%": "%",
        r"\mid": "|",
        r"\pm": "±",
        r"\infty": "∞",
    }

    @classmethod
    def _escape(cls, text: str) -> str:
        return html.escape(text, quote=True)

    @classmethod
    def convert_to_omml(cls, latex: str, is_display: bool = False) -> str:
        """Main entry point: returns <m:oMath> or <m:oMathPara> XML string."""
        s = latex.strip()
        if s.startswith("$$") and s.endswith("$$"):
            s = s[2:-2].strip()
        elif s.startswith("$") and s.endswith("$"):
            s = s[1:-1].strip()

        # Handle simple \langle ... \rangle wrapper
        if r"\langle" in s and r"\rangle" in s:
            s = s.replace(r"\langle", "⟨").replace(r"\rangle", "⟩")

        inner_xml = cls._parse_tokens(s)
        ns = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'

        if is_display:
            # Wrap in <m:oMathPara> or single <m:oMath>
            # Inside a Word paragraph, <m:oMath> styled paragraph is the most robust
            return f'<m:oMath {ns}>{inner_xml}</m:oMath>'
        else:
            return f'<m:oMath {ns}>{inner_xml}</m:oMath>'

    @classmethod
    def _parse_tokens(cls, s: str) -> str:
        """Parse LaTeX string into sequence of OMML XML elements."""
        xml_parts = []
        i = 0
        n = len(s)

        while i < n:
            ch = s[i]

            # Whitespace
            if ch.isspace():
                # Add tiny spacing or ignore
                i += 1
                continue

            # Fraction: \frac{num}{den}
            if s[i:].startswith(r"\frac"):
                idx = i + 5
                while idx < n and s[idx].isspace():
                    idx += 1
                if idx < n and s[idx] == "{":
                    num_text, next_idx = extract_braced(s, idx)
                    while next_idx < n and s[next_idx].isspace():
                        next_idx += 1
                    if next_idx < n and s[next_idx] == "{":
                        den_text, end_idx = extract_braced(s, next_idx)
                        num_xml = cls._parse_tokens(num_text)
                        den_xml = cls._parse_tokens(den_text)
                        xml_parts.append(
                            f"<m:f><m:num>{num_xml}</m:num><m:den>{den_xml}</m:den></m:f>"
                        )
                        i = end_idx
                        continue

            # Summation: \sum_{lower}^{upper} or \sum_{lower} or \sum
            if s[i:].startswith(r"\sum"):
                idx = i + 4
                while idx < n and s[idx].isspace():
                    idx += 1
                sub_text = None
                sup_text = None

                # Check for sub or sup
                for _ in range(2):
                    if idx < n and s[idx] == "_":
                        idx += 1
                        if idx < n and s[idx] == "{":
                            sub_text, idx = extract_braced(s, idx)
                        elif idx < n:
                            sub_text = s[idx]
                            idx += 1
                        while idx < n and s[idx].isspace():
                            idx += 1
                    elif idx < n and s[idx] == "^":
                        idx += 1
                        if idx < n and s[idx] == "{":
                            sup_text, idx = extract_braced(s, idx)
                        elif idx < n:
                            sup_text = s[idx]
                            idx += 1
                        while idx < n and s[idx].isspace():
                            idx += 1

                sub_hide = "0" if sub_text is not None else "1"
                sup_hide = "0" if sup_text is not None else "1"
                sub_xml = cls._parse_tokens(sub_text) if sub_text else ""
                sup_xml = cls._parse_tokens(sup_text) if sup_text else ""

                xml_parts.append(
                    f"<m:nary>"
                    f"<m:naryPr>"
                    f'<m:chr m:val="∑"/>'
                    f'<m:limLoc m:val="undOvr"/>'
                    f'<m:subHide m:val="{sub_hide}"/>'
                    f'<m:supHide m:val="{sup_hide}"/>'
                    f"</m:naryPr>"
                    f"<m:sub>{sub_xml}</m:sub>"
                    f"<m:sup>{sup_xml}</m:sup>"
                    f"<m:e/>"
                    f"</m:nary>"
                )
                i = idx
                continue

            # Text wrapper: \text{...}, \mathrm{...}, \mathbf{...}, \mathit{...}, \mathbb{...}, \mathcal{...}
            tag_match = re.match(r"^\\(text|mathrm|mathbf|mathit|mathbb|mathcal)\{", s[i:])
            if tag_match:
                tag_name = tag_match.group(1)
                brace_start = i + len(tag_match.group(0)) - 1
                inner, next_idx = extract_braced(s, brace_start)
                if tag_name in ("text", "mathrm"):
                    # Normal upright text
                    # replace escaped underscores or symbols
                    clean_inner = inner.replace(r"\_", "_").replace(r"\%", "%")
                    xml_parts.append(
                        f"<m:r><m:rPr><m:nor/></m:rPr><m:t>{cls._escape(clean_inner)}</m:t></m:r>"
                    )
                elif tag_name == "mathbf":
                    xml_parts.append(
                        f"<m:r><m:rPr><m:b/></m:rPr><m:t>{cls._escape(inner)}</m:t></m:r>"
                    )
                elif tag_name == "mathbb":
                    # E.g. \mathbb{I} -> 𝕀 or I
                    rep = {"I": "𝕀", "R": "ℝ", "N": "ℕ", "C": "ℂ"}.get(inner, inner)
                    xml_parts.append(f"<m:r><m:t>{cls._escape(rep)}</m:t></m:r>")
                elif tag_name == "mathcal":
                    # E.g. \mathcal{C} -> 𝓒 or C
                    rep = {"C": "𝓒", "L": "𝓛", "N": "𝓝"}.get(inner, inner)
                    xml_parts.append(f"<m:r><m:t>{cls._escape(rep)}</m:t></m:r>")
                else:
                    xml_parts.append(f"<m:r><m:t>{cls._escape(inner)}</m:t></m:r>")
                i = next_idx
                continue

            # Accents: \hat{...}
            if s[i:].startswith(r"\hat{"):
                inner, next_idx = extract_braced(s, i + 4)
                # In OMML accent: <m:acc><m:accPr><m:chr m:val="̂"/></m:accPr><m:e>...</m:e></m:acc>
                e_xml = cls._parse_tokens(inner)
                # Check if followed by subscript/superscript
                after_idx = next_idx
                has_sub = False
                has_sup = False
                sub_text = None
                sup_text = None
                while after_idx < n and s[after_idx].isspace():
                    after_idx += 1
                if after_idx < n and s[after_idx] == "_":
                    has_sub = True
                    after_idx += 1
                    if after_idx < n and s[after_idx] == "{":
                        sub_text, after_idx = extract_braced(s, after_idx)
                    elif after_idx < n:
                        sub_text = s[after_idx]
                        after_idx += 1
                acc_xml = f'<m:acc><m:accPr><m:chr m:val="̂"/></m:accPr><m:e>{e_xml}</m:e></m:acc>'
                if has_sub:
                    sub_xml = cls._parse_tokens(sub_text)
                    xml_parts.append(f"<m:sSub><m:e>{acc_xml}</m:e><m:sub>{sub_xml}</m:sub></m:sSub>")
                    i = after_idx
                    continue
                else:
                    xml_parts.append(acc_xml)
                    i = next_idx
                    continue

            # Norm: \| ... \|
            if s[i:].startswith(r"\|"):
                # find matching \|
                end_norm = s.find(r"\|", i + 2)
                if end_norm != -1:
                    inner = s[i+2:end_norm]
                    inner_xml = cls._parse_tokens(inner)
                    xml_parts.append(
                        f'<m:d><m:dPr><m:begChr m:val="‖"/><m:endChr m:val="‖"/></m:dPr><m:e>{inner_xml}</m:e></m:d>'
                    )
                    i = end_norm + 2
                    continue

            # Known LaTeX symbol commands
            matched_sym = False
            for cmd, sym in cls.SYMBOL_MAP.items():
                if s[i:].startswith(cmd):
                    # Check boundary so e.g. \sum doesn't match something else
                    after_ch_idx = i + len(cmd)
                    if after_ch_idx < n and cmd[-1].isalpha() and s[after_ch_idx].isalpha():
                        continue
                    xml_parts.append(f"<m:r><m:t>{cls._escape(sym)}</m:t></m:r>")
                    i = after_ch_idx
                    matched_sym = True
                    break
            if matched_sym:
                continue

            # Identifiers or operators with Subscripts and Superscripts
            # Pattern: base followed by _ or ^
            base_match = re.match(r"^([a-zA-Z0-9]+|[\(\)\[\]\{\}\+\-\=\<\>\,\.\:\;])", s[i:])
            if base_match:
                base_str = base_match.group(1)
                idx = i + len(base_str)
                # Check for sub/sup
                sub_text = None
                sup_text = None
                if idx < n and s[idx] in ("_", "^"):
                    # Parse attached sub and sup
                    for _ in range(2):
                        if idx < n and s[idx] == "_":
                            idx += 1
                            if idx < n and s[idx] == "{":
                                sub_text, idx = extract_braced(s, idx)
                            elif idx < n:
                                sub_text = s[idx]
                                idx += 1
                        elif idx < n and s[idx] == "^":
                            idx += 1
                            if idx < n and s[idx] == "{":
                                sup_text, idx = extract_braced(s, idx)
                            elif idx < n:
                                sup_text = s[idx]
                                idx += 1

                base_xml = f"<m:r><m:t>{cls._escape(base_str)}</m:t></m:r>"
                if sub_text is not None and sup_text is not None:
                    sub_xml = cls._parse_tokens(sub_text)
                    sup_xml = cls._parse_tokens(sup_text)
                    xml_parts.append(
                        f"<m:sSubSup><m:e>{base_xml}</m:e><m:sub>{sub_xml}</m:sub><m:sup>{sup_xml}</m:sup></m:sSubSup>"
                    )
                    i = idx
                    continue
                elif sub_text is not None:
                    sub_xml = cls._parse_tokens(sub_text)
                    xml_parts.append(
                        f"<m:sSub><m:e>{base_xml}</m:e><m:sub>{sub_xml}</m:sub></m:sSub>"
                    )
                    i = idx
                    continue
                elif sup_text is not None:
                    sup_xml = cls._parse_tokens(sup_text)
                    xml_parts.append(
                        f"<m:sSup><m:e>{base_xml}</m:e><m:sup>{sup_xml}</m:sup></m:sSup>"
                    )
                    i = idx
                    continue
                else:
                    xml_parts.append(base_xml)
                    i = idx
                    continue

            # Fallback for any other character
            xml_parts.append(f"<m:r><m:t>{cls._escape(s[i])}</m:t></m:r>")
            i += 1

        return "".join(xml_parts)
