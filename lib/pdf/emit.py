"""Markdown and companion prompts file generation."""

import logging
import os
import re
from collections import Counter

from .. import format_front_matter
from .cleanup import normalize_whitespace
from .types import Line, Span, Section, SectionKind, Confidence, BULLET_CHARS, COMPOUND_PREFIXES
from .tablemodel import SEP, flatten, marker

_log = logging.getLogger(__name__)


def _render_span(span: Span, skip_bold: bool = False) -> str:
    """Render a single non-monospace span with inline Markdown formatting.

    Monospace spans are handled by _render_line_spans via group merging.
    """
    text = span.text
    if not text.strip():
        return text

    stripped = text.strip()
    leading = text[:len(text) - len(text.lstrip())]
    trailing = text[len(text.rstrip()):]

    bold = span.bold and not skip_bold

    if span.link_url:
        inner = f"[{stripped}]({span.link_url})"
        if bold and span.italic:
            inner = f"***{inner}***"
        elif bold:
            inner = f"**{inner}**"
        elif span.italic:
            inner = f"*{inner}*"
        return f"{leading}{inner}{trailing}"

    if bold and span.italic:
        return f"{leading}***{stripped}***{trailing}"
    if bold:
        return f"{leading}**{stripped}**{trailing}"
    if span.italic:
        return f"{leading}*{stripped}*{trailing}"

    return text


def _render_line_spans(line: Line, in_code_section: bool = False,
                       suppress_bold: bool = False) -> str:
    """Render all spans in a line with inline formatting applied.

    Merges consecutive monospace spans into a single backtick pair
    to avoid fragmented output like `std``::``:stop_token`.
    """
    if in_code_section:
        return "".join(s.text for s in line.spans)

    groups: list[tuple[bool, list[Span]]] = []
    for span in line.spans:
        is_mono = bool(span.monospace and span.text.strip())
        if groups and groups[-1][0] == is_mono:
            groups[-1][1].append(span)
        else:
            groups.append((is_mono, [span]))

    parts = []
    for is_mono, spans in groups:
        if is_mono:
            merged_text = "".join(s.text for s in spans)
            stripped = merged_text.strip()
            if stripped:
                leading = merged_text[:len(merged_text) - len(merged_text.lstrip())]
                trailing = merged_text[len(merged_text.rstrip()):]
                parts.append(f"{leading}`{stripped}`{trailing}")
            else:
                parts.append(merged_text)
        else:
            for span in spans:
                if suppress_bold:
                    parts.append(_render_span(span, skip_bold=True))
                else:
                    parts.append(_render_span(span))
    return "".join(parts)


def _render_paragraph_spans(sec: Section) -> str:
    """Render a paragraph section using span-level formatting, then unwrap."""
    rendered_lines = []
    for line in sec.lines:
        rendered_lines.append(_render_line_spans(line))
    text = "\n".join(rendered_lines)
    text = normalize_whitespace(text)
    lines = text.split("\n")
    return " ".join(ln.strip() for ln in lines if ln.strip())


def _render_heading_spans(sec: Section) -> str:
    """Render a heading using span-level formatting for the first line.

    Bold is suppressed because the ATX prefix already conveys heading weight.
    """
    prefix = "#" * sec.heading_level
    if sec.lines:
        text = _render_line_spans(sec.lines[0], suppress_bold=True)
    else:
        text = sec.text.split("\n")[0]
    return f"{prefix} {text.strip()}"


def _normalize_bullet(char: str) -> str:
    """Replace Unicode bullet characters with *."""
    if char in BULLET_CHARS:
        return "*"
    return char


def _normalize_bullets(text: str) -> str:
    """Replace Unicode bullet characters with * throughout text."""
    return "".join(_normalize_bullet(ch) for ch in text)


def _render_list_spans(sec: Section) -> str:
    """Render a list section with span formatting and normalized bullets."""
    if sec.lines:
        result_lines = []
        for line in sec.lines:
            rendered = _render_line_spans(line).rstrip()
            if rendered:
                result_lines.append(_normalize_bullets(rendered))
        return "\n".join(result_lines)

    return _normalize_bullets(sec.text.rstrip())


_DEFAULT_CHAR_WIDTH = 6.0


def _estimate_char_width(sec_lines: list) -> float:
    """Estimate monospace character width from span bbox and text length."""
    for line in sec_lines:
        for span in line.spans:
            n = len(span.text.replace(" ", ""))
            if n >= 2:
                w = span.bbox[2] - span.bbox[0]
                if w > 0:
                    return w / n
    return _DEFAULT_CHAR_WIDTH


def _render_code_block(sec: Section) -> str:
    """Render a code section as a fenced code block.

    Uses glyph x-positions to calculate indentation: the offset
    of each line's first character from the block's left margin,
    divided by the monospace character width.
    """
    lang = sec.fence_lang or "cpp"
    if not sec.lines:
        return f"```{lang}\n{sec.text}\n```"

    char_w = _estimate_char_width(sec.lines)
    content_x = [
        ln.spans[0].bbox[0] for ln in sec.lines
        if ln.spans and ln.spans[0].text.strip()
    ]
    base_x = min(content_x) if content_x else 0.0

    lines = []
    for line in sec.lines:
        raw = _render_line_spans(line, in_code_section=True)
        if line.spans:
            first_text = line.spans[0].text
            text_indent = len(first_text) - len(first_text.lstrip())

            first_nonspace = line.spans[0]
            for sp in line.spans:
                if sp.text.strip():
                    first_nonspace = sp
                    break
            x0 = first_nonspace.bbox[0]
            x_indent = round((x0 - base_x) / char_w) if char_w > 0 else 0
            x_indent = max(x_indent, 0)

            if text_indent > 0 and x_indent > 0 and text_indent == x_indent:
                indent = text_indent
            else:
                indent = x_indent if x_indent > 0 else text_indent

            lines.append(" " * indent + raw.lstrip())
        else:
            lines.append(raw)
    code = "\n".join(lines)
    return f"```{lang}\n{code}\n```"


def _render_wording_line(line: Line) -> str:
    """Render a wording line, merging consecutive same-role spans.

    Whitespace-only spans between two same-role spans are absorbed into
    the group; whitespace between different roles is emitted as-is.
    Both ins and del use the role name directly as the HTML tag.
    """
    def _render_group(role: str | None, spans: list[Span]) -> str:
        text = "".join(s.text for s in spans)
        if role in ("ins", "del"):
            s = text.strip()
            lead = text[:len(text) - len(text.lstrip())]
            trail = text[len(text.rstrip()):]
            return f"{lead}<{role}>{s}</{role}>{trail}"
        return "".join(
            f"`{s.text.strip()}`" if s.monospace and s.text.strip() else s.text
            for s in spans
        )

    parts: list[str] = []
    group: list[Span] = []
    group_role: str | None = None
    ws_buf: list[Span] = []

    for span in line.spans:
        role = span.wording_role if span.text.strip() else None
        if role is None:
            ws_buf.append(span)
        elif role == group_role:
            group.extend(ws_buf)
            ws_buf.clear()
            group.append(span)
        else:
            if group:
                parts.append(_render_group(group_role, group))
            parts.extend(s.text for s in ws_buf)
            ws_buf.clear()
            group_role, group = role, [span]

    if group:
        parts.append(_render_group(group_role, group))
    parts.extend(s.text for s in ws_buf)
    return "".join(parts)


def _render_wording_section(sec: Section) -> str:
    """Render a wording section with Pandoc fenced div markers."""
    div_class = sec.kind.value
    rendered_lines = []
    for line in sec.lines:
        rendered_lines.append(_render_wording_line(line))
    text = normalize_whitespace("\n".join(rendered_lines))
    inner = " ".join(ln.strip() for ln in text.split("\n") if ln.strip())
    return f":::{div_class}\n\n{inner}\n\n:::"


# Words of the document's running text (not its tables), set by
# emit_markdown: how the paper itself spells a word decides a line-break
# hyphen in a table cell.
_LEXICON: Counter = Counter()
_LEX_WORD = re.compile(r"[A-Za-z]+(?:-[A-Za-z]+)*")


def _set_lexicon(sections: list[Section]) -> None:
    _LEXICON.clear()
    for sec in sections:
        if sec.kind != SectionKind.TABLE:
            _LEXICON.update(w.lower() for w in _LEX_WORD.findall(sec.text))


def _join_hyphenated(line: str, nxt: str, prefix: str) -> str:
    """Join a cell line ending in "word-" with the next line.

    The paper's own text decides first: if it writes "automatically" and
    never "automati-cally", the hyphen was a line break; if it writes
    "non-enforced", the hyphen is part of the word. Otherwise a syllable
    break drops the hyphen ("com-" + "patibility"): the part before it is a
    short fragment or the continuation is short. A compound keeps it
    ("non-" + "enforced", "effect-" + "parameterized").
    """
    suffix = re.match(r"[A-Za-z]*", nxt).group(0)
    joined, hyphened = (prefix + suffix).lower(), f"{prefix}-{suffix}".lower()
    if suffix and (_LEXICON[joined] or _LEXICON[hyphened]):
        return (line if _LEXICON[hyphened] >= _LEXICON[joined] else line[:-1]) + nxt
    if "-" in prefix:
        return line + nxt                 # inside a hyphenated chain: "warnings-as-" + "errors"
    p = prefix.lower()
    # An acronym before the hyphen is a compound ("ABI-" + "independent").
    acronym = len(prefix) >= 2 and prefix.isupper()
    syllable = (not acronym and p not in COMPOUND_PREFIXES
                and (len(p) <= 3 or len(suffix) <= 4))
    return (line[:-1] if syllable else line) + nxt


def _render_cell_spans(spans: list, suppress_bold: bool = False) -> str:
    """Render a table cell's spans with inline formatting.

    A span whose text is "\n" separates the lines of a wrapped cell; they
    are joined with <br>. Pipes are escaped so they cannot split the cell
    (GFM honours the escape inside code spans too).
    """
    parts: list[list] = [[]]
    for s in spans:
        if s.text == "\n":
            parts.append([])
        else:
            parts[-1].append(s)
    rendered = [r for r in (_render_line_spans(Line(spans=p), suppress_bold=suppress_bold).strip()
                            for p in parts if p) if r]
    if len(rendered) > 1 and all(len(r) == 1 and r.isalpha() for r in rendered):
        return "".join(rendered)          # letters stacked in a narrow cell: "S" / "F" -> "SF"
    out = rendered[:1]
    for r in rendered[1:]:
        # "word-" at the end of a line, possibly inside bold/italic that
        # continues on the next line ("ap-**" + "**plied"). Code is never
        # dehyphenated: a "-" ending a code line is part of the code.
        m = _HYPHEN_END.search(out[-1])
        n = re.match(r"(\*\*|\*)?(?=[a-z])", r)
        if m and n and (m.group(2) or "") == (n.group(1) or ""):
            mark = m.group(2) or ""
            head = out[-1][:len(out[-1]) - len(mark)]
            out[-1] = _join_hyphenated(head, r[len(mark):], m.group(1))
        else:
            out.append(r)
    return _escape_angle("<br>".join(out)).replace("|", "\\|")


_HYPHEN_END = re.compile(r"([A-Za-z]+(?:-[A-Za-z]+)*)-(\*\*|\*)?$")


def _escape_angle(text: str) -> str:
    """Escape "<" outside code spans so "<a@b.org>" is not read as a link or HTML."""
    parts = re.split(r"(`[^`]*`|<br>)", text)
    return "".join(p if i % 2 else p.replace("<", "\\<") for i, p in enumerate(parts))


_CODE_SHARE = 0.8       # body text this monospace...
_CODE_LINES = 3         # ...with a cell this many lines long: a code comparison


def _cell_lines(cell) -> list[list]:
    out, cur = [], []
    for s in cell:
        if s.text == "\n":
            out.append(cur)
            cur = []
        else:
            cur.append(s)
    out.append(cur)
    return [ln for ln in out if any(s.text.strip() for s in ln)]


def _is_code_comparison(rows) -> bool:
    """Side-by-side code: at most 3 columns and 2 rows (header + code), the
    body (nearly) all monospace, some cell several lines long."""
    if not rows or max(len(r) for r in rows) > 3 or len(rows) > 2:
        return False
    body = rows[1:] if len(rows) == 2 else rows
    spans = [s for r in body for c in r for s in c if s.text.strip() and s.text != "\n"]
    chars = sum(len(s.text.strip()) for s in spans)
    mono = sum(len(s.text.strip()) for s in spans if s.monospace)
    return (chars > 0 and mono >= _CODE_SHARE * chars and len([c for c in body[0] if c]) >= 2
            and max(len(_cell_lines(c)) for r in body for c in r) >= _CODE_LINES)


def _code_text(cell) -> str:
    """A code cell's lines exactly: indentation rebuilt from x offsets."""
    lines = _cell_lines(cell)
    widths = [(s.bbox[2] - s.bbox[0]) / len(s.text) for ln in lines for s in ln
              if s.monospace and s.text and s.bbox and s.bbox[2] > s.bbox[0]]
    em = sorted(widths)[len(widths) // 2] if widths else 0.0
    left = min((ln[0].bbox[0] for ln in lines if ln and ln[0].bbox), default=0.0)
    out = []
    for ln in lines:
        text = "".join(s.text for s in ln).rstrip()
        indent = int(round((ln[0].bbox[0] - left) / em)) if em and ln[0].bbox else 0
        out.append(" " * max(indent, 0) + text.lstrip())
    return "\n".join(out)


def _render_code_comparison(rows) -> str:
    """Paired fenced code blocks under the column headers (a pipe table cannot
    hold multi-line code), after a marker that records the structure."""
    header = rows[0] if len(rows) == 2 else [[] for _ in rows[0]]
    body = rows[-1]
    parts = [f"<!-- tomd:table kind=code-comparison cols={len(body)} -->"]
    for h, cell in zip(list(header) + [[]] * (len(body) - len(header)), body):
        title = " ".join(s.text for s in h if s.text != "\n").strip()
        if title:
            parts.append(f"**{title}**")
        parts.append("```cpp\n" + _code_text(cell) + "\n```")
    return "\n\n".join(parts)


def _render_table(sec: Section) -> str:
    """Render a table section as a Markdown table."""
    if not sec.columns:
        return sec.text
    if os.environ.get("TOMD_CODECMP") != "0" and _is_code_comparison(sec.columns):
        return _render_code_comparison(sec.columns)

    rows = sec.columns
    num_cols = max(len(row) for row in rows)
    spans = sec.metadata.get("spans") or []
    header_rows = 1 + max((s["r"] + 1 for s in spans if s["kind"] == "header"), default=0)
    grid = [[_render_cell_spans(cell, suppress_bold=r < header_rows) for cell in row]
            + [""] * (num_cols - len(row)) for r, row in enumerate(rows)]
    if spans:
        # lossless model -> plain Markdown: combined headers, labels filled
        # down, shared values kept once; the spans go in a comment after it
        sep = SEP if not any(SEP in c for r in grid for c in r) else " ⁄ "
        grid, _ = flatten(grid, spans, lambda c: not c.strip(), lambda a, b: f"{a}{sep}{b}")

    lines = ["| " + " | ".join(grid[0]) + " |", "| " + " | ".join(["---"] * num_cols) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in grid[1:]]
    if spans:
        lines += ["", marker(spans)]
    return "\n".join(lines)


def _render_section_md(sec: Section) -> str:
    """Render a single section to Markdown."""
    if sec.kind in (SectionKind.TITLE, SectionKind.HEADING):
        return _render_heading_spans(sec)

    if sec.kind == SectionKind.TABLE:
        return _render_table(sec)

    if sec.kind == SectionKind.CODE:
        return _render_code_block(sec)

    if sec.kind == SectionKind.LIST:
        return _render_list_spans(sec)

    if sec.kind in (SectionKind.WORDING, SectionKind.WORDING_ADD,
                    SectionKind.WORDING_REMOVE):
        return _render_wording_section(sec)

    if sec.kind == SectionKind.PARAGRAPH:
        return _render_paragraph_spans(sec)

    return sec.text


def emit_markdown(metadata: dict, sections: list[Section]) -> str:
    """Generate the output Markdown from structured sections.

    Confident sections are clean Markdown. Uncertain sections emit
    the MuPDF version marked with an HTML comment.
    """
    parts: list[str] = []
    _set_lexicon(sections)

    fm = format_front_matter(metadata)
    if fm:
        parts.append(fm)

    line_num = fm.count("\n") + 3 if fm else 1

    for sec in sections:
        if sec.kind == SectionKind.UNCERTAIN:
            text = sec.text.rstrip()
            text_lines = text.count("\n") + 1
            text_start = line_num + 2
            comment = f"<!-- tomd:uncertain:L{text_start}-L{text_start + text_lines - 1} -->"
            parts.append(comment)
            parts.append(text)
            line_num += text_lines + 3
            continue

        rendered = _render_section_md(sec)
        if not rendered.strip():
            continue
        if _is_uncertain_table(sec) or "possible_table" in sec.metadata:
            # Table sources disagreed, or text that looks like an unextracted
            # table: mark it like any uncertain region, keeping its rendering.
            text_lines = rendered.count("\n") + 1
            text_start = line_num + 2
            parts.append(f"<!-- tomd:uncertain:L{text_start}-L{text_start + text_lines - 1} -->")
            parts.append(rendered)
            line_num += text_lines + 3
            continue
        parts.append(rendered)
        line_num += rendered.count("\n") + 2

    md = "\n\n".join(parts)
    md = md.rstrip() + "\n"
    return md


def _is_uncertain_table(sec: Section) -> bool:
    return sec.kind == SectionKind.TABLE and sec.confidence == Confidence.UNCERTAIN


def _is_flagged(sec: Section) -> bool:
    return (sec.kind == SectionKind.UNCERTAIN or _is_uncertain_table(sec)
            or "possible_table" in sec.metadata)


def emit_prompts(sections: list[Section]) -> str | None:
    """Generate the companion prompts file for uncertain regions.

    Returns None if there are no uncertain regions.
    """
    uncertain = [(idx, s) for idx, s in enumerate(sections) if _is_flagged(s)]
    if not uncertain:
        return None

    parts: list[str] = []
    parts.append("# tomd - LLM Reconciliation Prompts")
    parts.append("")
    parts.append("Each section below contains text extracted from a PDF using two")
    parts.append("independent methods that produced different results. Reconcile")
    parts.append("each into clean Markdown.")
    parts.append("")

    for i, (idx, sec) in enumerate(uncertain):
        ctx_before = ""
        ctx_after = ""
        if idx > 0 and not _is_flagged(sections[idx - 1]):
            ctx_before = sections[idx - 1].text[:200].strip()
        if idx + 1 < len(sections) and not _is_flagged(sections[idx + 1]):
            ctx_after = sections[idx + 1].text[:200].strip()

        parts.append(f"## Region {i + 1} (page {sec.page_num})")
        parts.append("")
        parts.append("The following section was extracted from a PDF using two independent methods")
        parts.append("that produced different results. Reconcile them into clean Markdown.")
        parts.append("")
        parts.append("CRITICAL: Keep ALL data verbatim. Do not summarize, omit, or paraphrase any")
        parts.append("text. Every word from the source must appear in your output. You are only")
        parts.append("fixing structure (paragraphs, headings, lists, formatting) - never content.")
        parts.append("")

        if ctx_before:
            parts.append("Context (preceding confident section):")
            parts.append(f"> {ctx_before}")
            parts.append("")

        if "possible_table" in sec.metadata:
            parts.append("This text may be a table that was not extracted as one")
            parts.append(f"({sec.metadata['possible_table']}). If it is a table,")
            parts.append("rebuild it as one Markdown table; otherwise keep it as it is.")
            parts.append("")
            parts.append("```")
            parts.append(_render_section_md(sec))
            parts.append("```")
            parts.append("")
        elif _is_uncertain_table(sec):
            # One block per table extractor; the first is the one emitted.
            parts.append("This is a table. The extractors below disagree on its rows,")
            parts.append("columns or cell text. Produce one correct Markdown table.")
            parts.append("")
            if sec.metadata.get("table_note"):
                parts.append(sec.metadata["table_note"])
                parts.append("")
            for i, (source, table_md) in enumerate(sec.metadata.get("table_versions", [])):
                label = "emitted" if i == 0 else "alternative"
                parts.append(f"Table from the {source} extractor ({label}):")
                parts.append("```")
                parts.append(table_md)
                parts.append("```")
                parts.append("")
        else:
            parts.append("MuPDF extraction:")
            parts.append("```")
            parts.append(sec.mupdf_text or sec.text)
            parts.append("```")
            parts.append("")
            parts.append("Spatial extraction:")
            parts.append("```")
            parts.append(sec.spatial_text or sec.text)
            parts.append("```")
            parts.append("")

        if ctx_after:
            parts.append("Context (following confident section):")
            parts.append(f"> {ctx_after}")
            parts.append("")

    return "\n".join(parts)
