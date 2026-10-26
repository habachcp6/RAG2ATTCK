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

    OPERATORS = {
        "min", "max", "cos", "sin", "tan", "log", "ln", "exp",
        "det", "lim", "dim", "ker", "arg", "sup", "inf",
    }

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
        r"\div": "÷",
        r"\cdot": "·",
        r"\dots": "…",
        r"\cdots": "⋯",
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
        r"\alpha": "α",
        r"\beta": "β",
        r"\gamma": "γ",
        r"\theta": "θ",
        r"\lambda": "λ",
        r"\mu": "μ",
        r"\sigma": "σ",
        r"\tau": "τ",
        r"\phi": "φ",
        r"\chi": "χ",
        r"\psi": "ψ",
        r"\omega": "ω",
        r"\Gamma": "Γ",
        r"\Theta": "Θ",
        r"\Lambda": "Λ",
        r"\Sigma": "Σ",
        r"\Phi": "Φ",
        r"\Psi": "Ψ",
        r"\Omega": "Ω",
        r"\top": "⊤",
        r"\bot": "⊥",
        r"\prime": "′",
    }

    @classmethod
    def _escape(cls, text: str) -> str:
        return html.escape(text, quote=True)

    @classmethod
    def _extract_sub_sup(cls, s: str, idx: int) -> tuple[str | None, str | None, int]:
        """Check if s[idx:] has attached _ or ^ and extract sub_text, sup_text, new_idx."""
        n = len(s)
        sub_text = None
        sup_text = None
        while idx < n and s[idx].isspace():
            idx += 1
        if idx < n and s[idx] in ("_", "^"):
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
        return sub_text, sup_text, idx

    @classmethod
    def _wrap_sub_sup(cls, base_xml: str, sub_text: str | None, sup_text: str | None) -> str:
        """Wrap base_xml with OMML sub, sup, or subSup if present."""
        if sub_text is not None and sup_text is not None:
            sub_xml = cls._parse_tokens(sub_text)
            sup_xml = cls._parse_tokens(sup_text)
            return f"<m:sSubSup><m:e>{base_xml}</m:e><m:sub>{sub_xml}</m:sub><m:sup>{sup_xml}</m:sup></m:sSubSup>"
        elif sub_text is not None:
            sub_xml = cls._parse_tokens(sub_text)
            return f"<m:sSub><m:e>{base_xml}</m:e><m:sub>{sub_xml}</m:sub></m:sSub>"
        elif sup_text is not None:
            sup_xml = cls._parse_tokens(sup_text)
            return f"<m:sSup><m:e>{base_xml}</m:e><m:sup>{sup_xml}</m:sup></m:sSup>"
        return base_xml

    @classmethod
    def convert_to_omml(cls, latex: str, is_display: bool = False) -> str:
        """Main entry point: returns <m:oMath> or <m:oMathPara> XML string."""
        s = latex.strip()
        if s.startswith("$$") and s.endswith("$$"):
            s = s[2:-2].strip()
        elif s.startswith("$") and s.endswith("$"):
            s = s[1:-1].strip()

        if r"\langle" in s and r"\rangle" in s:
            s = s.replace(r"\langle", "⟨").replace(r"\rangle", "⟩")

        inner_xml = cls._parse_tokens(s)
        ns = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'

        if is_display:
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

            if ch.isspace():
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
                        base_frac = f"<m:f><m:num>{num_xml}</m:num><m:den>{den_xml}</m:den></m:f>"
                        sub_text, sup_text, idx = cls._extract_sub_sup(s, end_idx)
                        xml_parts.append(cls._wrap_sub_sup(base_frac, sub_text, sup_text))
                        i = idx
                        continue

            # Summation: \sum_{lower}^{upper} or \sum_{lower} or \sum
            if s[i:].startswith(r"\sum"):
                idx = i + 4
                sub_text, sup_text, idx = cls._extract_sub_sup(s, idx)
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

            # Math Operators: \min, \max, \cos, \sin, etc.
            op_match = re.match(r"^\\([a-zA-Z]+)", s[i:])
            if op_match and op_match.group(1) in cls.OPERATORS:
                op_name = op_match.group(1)
                idx = i + len(op_match.group(0))
                sub_text, sup_text, idx = cls._extract_sub_sup(s, idx)
                base_xml = f"<m:r><m:rPr><m:nor/></m:rPr><m:t>{op_name}</m:t></m:r>"
                xml_parts.append(cls._wrap_sub_sup(base_xml, sub_text, sup_text))
                i = idx
                continue

            # Text wrapper: \text{...}, \mathrm{...}, \mathbf{...}, \mathit{...}, \mathbb{...}, \mathcal{...}
            tag_match = re.match(r"^\\(text|mathrm|mathbf|mathit|mathbb|mathcal)\{", s[i:])
            if tag_match:
                tag_name = tag_match.group(1)
                brace_start = i + len(tag_match.group(0)) - 1
                inner, next_idx = extract_braced(s, brace_start)
                if tag_name in ("text", "mathrm"):
                    clean_inner = inner.replace(r"\_", "_").replace(r"\%", "%")
                    base_xml = f"<m:r><m:rPr><m:nor/></m:rPr><m:t>{cls._escape(clean_inner)}</m:t></m:r>"
                elif tag_name == "mathbf":
                    base_xml = f"<m:r><m:rPr><m:b/></m:rPr><m:t>{cls._escape(inner)}</m:t></m:r>"
                elif tag_name == "mathbb":
                    rep = {"I": "𝕀", "R": "ℝ", "N": "ℕ", "C": "ℂ"}.get(inner, inner)
                    base_xml = f"<m:r><m:t>{cls._escape(rep)}</m:t></m:r>"
                elif tag_name == "mathcal":
                    rep = {"C": "𝓒", "L": "𝓛", "N": "𝓝"}.get(inner, inner)
                    base_xml = f"<m:r><m:t>{cls._escape(rep)}</m:t></m:r>"
                else:
                    base_xml = f"<m:r><m:t>{cls._escape(inner)}</m:t></m:r>"

                sub_text, sup_text, idx = cls._extract_sub_sup(s, next_idx)
                xml_parts.append(cls._wrap_sub_sup(base_xml, sub_text, sup_text))
                i = idx
                continue

            # Accents: \hat{...}
            if s[i:].startswith(r"\hat{"):
                inner, next_idx = extract_braced(s, i + 4)
                e_xml = cls._parse_tokens(inner)
                acc_xml = f'<m:acc><m:accPr><m:chr m:val="̂"/></m:accPr><m:e>{e_xml}</m:e></m:acc>'
                sub_text, sup_text, idx = cls._extract_sub_sup(s, next_idx)
                xml_parts.append(cls._wrap_sub_sup(acc_xml, sub_text, sup_text))
                i = idx
                continue

            # Norm: \| ... \|
            if s[i:].startswith(r"\|"):
                end_norm = s.find(r"\|", i + 2)
                if end_norm != -1:
                    inner = s[i+2:end_norm]
                    inner_xml = cls._parse_tokens(inner)
                    base_xml = f'<m:d><m:dPr><m:begChr m:val="‖"/><m:endChr m:val="‖"/></m:dPr><m:e>{inner_xml}</m:e></m:d>'
                    idx = end_norm + 2
                    sub_text, sup_text, idx = cls._extract_sub_sup(s, idx)
                    xml_parts.append(cls._wrap_sub_sup(base_xml, sub_text, sup_text))
                    i = idx
                    continue

            # Known LaTeX symbol commands: \Delta, \times, etc.
            matched_sym = False
            for cmd, sym in cls.SYMBOL_MAP.items():
                if s[i:].startswith(cmd):
                    after_ch_idx = i + len(cmd)
                    if after_ch_idx < n and cmd[-1].isalpha() and s[after_ch_idx].isalpha():
                        continue
                    base_xml = f"<m:r><m:t>{cls._escape(sym)}</m:t></m:r>"
                    sub_text, sup_text, idx = cls._extract_sub_sup(s, after_ch_idx)
                    xml_parts.append(cls._wrap_sub_sup(base_xml, sub_text, sup_text))
                    i = idx
                    matched_sym = True
                    break
            if matched_sym:
                continue

            # Braced group: {...}
            if s[i] == "{":
                inner, next_idx = extract_braced(s, i)
                inner_xml = cls._parse_tokens(inner)
                sub_text, sup_text, idx = cls._extract_sub_sup(s, next_idx)
                xml_parts.append(cls._wrap_sub_sup(inner_xml, sub_text, sup_text))
                i = idx
                continue

            # Unattached Subscripts or Superscripts: attach to previous XML element if present
            if s[i] in ("_", "^") and xml_parts:
                last_xml = xml_parts.pop()
                sub_text, sup_text, idx = cls._extract_sub_sup(s, i)
                xml_parts.append(cls._wrap_sub_sup(last_xml, sub_text, sup_text))
                i = idx
                continue

            # Identifiers or single tokens with Subscripts and Superscripts
            base_match = re.match(r"^([a-zA-Z0-9]+|[\(\)\[\]\+\-\=\<\>\,\.\:\;])", s[i:])
            if base_match:
                base_str = base_match.group(1)
                idx = i + len(base_str)
                sub_text, sup_text, idx = cls._extract_sub_sup(s, idx)
                base_xml = f"<m:r><m:t>{cls._escape(base_str)}</m:t></m:r>"
                xml_parts.append(cls._wrap_sub_sup(base_xml, sub_text, sup_text))
                i = idx
                continue

            # Fallback for any other character
            xml_parts.append(f"<m:r><m:t>{cls._escape(s[i])}</m:t></m:r>")
            i += 1

        return "".join(xml_parts)
