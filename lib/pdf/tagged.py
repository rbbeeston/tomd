"""Table detection from the PDF's accessibility tags (Tagged PDF).

When the producing application wrote a structure tree (Google Docs, Word,
LibreOffice, Typst, Chrome print), tables are explicitly marked up as
Table / TR / TH / TD elements. PyMuPDF exposes them per page through
get_text("dict") with TEXT_COLLECT_STRUCTURE: structure nodes appear as
blocks of type 2 that contain the text blocks they own.

Cross-page tables: a Table element continued on the next page appears on
both pages with the same structure index, so the parts are joined by
index; a row split by the page break (same TR index) is joined too.

Empty cells own no text, so a page's dict may omit them. Rows shorter
than the table are therefore re-aligned by x position against the column
positions of full rows.

Untagged PDFs (LaTeX/pdfTeX, ReportLab, most tools) simply yield nothing.
"""

import logging

import fitz

from .types import Line, Span, TableCandidate
from .mono import classify_monospace

_log = logging.getLogger(__name__)

_MUPDF_BOLD_BIT = 1 << 4
_MUPDF_ITALIC_BIT = 1 << 1
_ROW_KINDS = ("THead", "TBody", "TFoot")
_CELL_KINDS = ("TD", "TH")


def _lines_of(node, page_num: int) -> list[Line]:
    """All text lines owned by a structure node, in reading order."""
    out: list[Line] = []
    for b in node.get("blocks", []):
        if b.get("type") == 2:
            out.extend(_lines_of(b, page_num))
        elif b.get("type") == 0:
            for ln in b.get("lines", []):
                spans = [Span(
                    text=sp.get("text", ""), font_name=sp.get("font", ""),
                    font_size=sp.get("size", 0.0),
                    bold=bool(sp.get("flags", 0) & _MUPDF_BOLD_BIT),
                    italic=bool(sp.get("flags", 0) & _MUPDF_ITALIC_BIT),
                    monospace=classify_monospace(sp.get("font", "")),
                    bbox=tuple(sp.get("bbox", (0, 0, 0, 0))),
                    origin=tuple(sp.get("origin", (0, 0))),
                    color=sp.get("color", 0),
                ) for sp in ln.get("spans", []) if sp.get("text")]
                if spans and "".join(s.text for s in spans).strip():
                    out.append(Line(spans=spans, bbox=tuple(ln["bbox"]), page_num=page_num))
    return out


def _join_rows(lines: list[Line]) -> list[Line]:
    """Merge lines that sit on the same baseline into one Line.

    The structure dict returns each tagged run (Code, Span, Link...) as its
    own line, so "simple capture of", "x", "by copy" would otherwise become
    three lines. A space is inserted where the runs are visibly apart.
    """
    rows: list[list[Line]] = []
    for ln in sorted(lines, key=lambda l: (l.page_num, (l.bbox[1] + l.bbox[3]) / 2, l.bbox[0])):
        yc = (ln.bbox[1] + ln.bbox[3]) / 2
        if rows and rows[-1][0].page_num == ln.page_num and abs(
                (rows[-1][0].bbox[1] + rows[-1][0].bbox[3]) / 2 - yc) < 3.0:
            rows[-1].append(ln)
        else:
            rows.append([ln])
    out = []
    for row in rows:
        row.sort(key=lambda l: l.bbox[0])
        spans: list[Span] = []
        for prev, ln in zip([None] + row, row):
            if prev is not None and spans:
                gap = ln.bbox[0] - prev.bbox[2]
                size = ln.spans[0].font_size or 10.0
                if (gap > 0.1 * size and not spans[-1].text.endswith(" ")
                        and not ln.spans[0].text.startswith(" ")):
                    spans[-1].text += " "
            spans.extend(ln.spans)
        out.append(Line(spans=spans, page_num=row[0].page_num,
                        bbox=(min(l.bbox[0] for l in row), min(l.bbox[1] for l in row),
                              max(l.bbox[2] for l in row), max(l.bbox[3] for l in row))))
    return out


def _rows_of(table):
    for b in table.get("blocks", []):
        if b.get("type") != 2:
            continue
        if b.get("std") == "TR":
            yield b
        elif b.get("std") in _ROW_KINDS:
            yield from _rows_of(b)


def _page_tables(page, page_num, acc: dict):
    """Collect Table nodes of one page into acc[table_index][tr_index]."""
    data = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT | fitz.TEXT_COLLECT_STRUCTURE)

    def walk(b):
        if b.get("type") != 2:
            return
        if b.get("std") == "Table":
            rows = acc.setdefault(b.get("index"), {})
            for tr in _rows_of(b):
                cells = [_join_rows(_lines_of(td, page_num)) for td in tr.get("blocks", [])
                         if td.get("type") == 2 and td.get("std") in _CELL_KINDS]
                prev = rows.get(tr.get("index"))
                if prev is None:
                    rows[tr.get("index")] = cells
                else:  # row continued on this page: append line by line
                    for k, c in enumerate(cells):
                        if k < len(prev):
                            prev[k].extend(c)
                        else:
                            prev.append(c)
            return
        for c in b.get("blocks", []):
            walk(c)

    for b in data.get("blocks", []):
        walk(b)


def _realign(rows: list[list[list[Line]]]) -> list[list[list[Line]]]:
    """Place the cells of short rows into columns by x position."""
    width = max(len(r) for r in rows)
    full = [r for r in rows if len(r) == width]
    if not full:
        return rows
    col_x = []
    for c in range(width):
        xs = sorted(ln.bbox[0] for r in full for ln in r[c][:1])
        col_x.append(xs[len(xs) // 2] if xs else None)
    if any(x is None for x in col_x):
        return rows
    out = []
    for r in rows:
        if len(r) == width:
            out.append(r)
            continue
        new: list[list[Line]] = [[] for _ in range(width)]
        for cell in r:
            if not cell:
                continue
            # rightmost column that starts at or before the cell's text
            x = cell[0].bbox[0]
            ci = max([k for k in range(width) if col_x[k] <= x + 3.0], default=0)
            if new[ci]:  # collision: fall back to first free slot
                ci = next((k for k in range(width) if not new[k]), ci)
            new[ci].extend(cell)
        out.append(new)
    return out


_BROKEN_TREE_MARKERS = ("structure tree",)


def extract_tagged_tables(doc) -> list[TableCandidate]:
    """All tables marked up in the document's structure tree.

    When MuPDF reports structure-tree errors while reading the pages (some
    Word exports), every candidate gets the "tags-malformed" flag so table
    selection ranks it below the ruling-line version.
    """
    if doc.xref_get_key(doc.pdf_catalog(), "StructTreeRoot")[0] == "null":
        return []                       # untagged PDF
    acc: dict = {}
    fitz.TOOLS.mupdf_warnings()          # discard warnings from earlier work
    for page in doc:
        try:
            _page_tables(page, page.number, acc)
        except Exception as e:  # malformed structure trees are common
            _log.debug("Page %d: structure tree unreadable (%s)", page.number, e)
    out = []
    for _, tr_map in sorted(acc.items(), key=lambda kv: kv[0] or 0):
        rows = [cells for _, cells in sorted(tr_map.items(), key=lambda kv: kv[0] or 0) if cells]
        if len(rows) < 2 or max(len(r) for r in rows) < 2:
            continue
        rows = _realign(rows)
        bboxes: dict[int, tuple] = {}
        for r in rows:
            for cell in r:
                for ln in cell:
                    b = bboxes.get(ln.page_num, ln.bbox)
                    bboxes[ln.page_num] = (min(b[0], ln.bbox[0]), min(b[1], ln.bbox[1]),
                                           max(b[2], ln.bbox[2]), max(b[3], ln.bbox[3]))
        if bboxes:
            out.append(TableCandidate("tags", rows, bboxes))
    warnings = fitz.TOOLS.mupdf_warnings()
    if out and any(m in warnings for m in _BROKEN_TREE_MARKERS):
        _log.info("Structure tree reported malformed; tagged tables demoted")
        for t in out:
            t.flags.append("tags-malformed")
    if out:
        _log.debug("%d tagged table(s)", len(out))
    return out
