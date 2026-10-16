"""Table detection from ruling lines (vector drawings).

An extractor independent of the MuPDF text blocks that table.py uses: it
looks only at the lines and thin rectangles a page draws, and at character
positions to fill cells.

Two techniques:
  Grid tables: PyMuPDF's page.find_tables(strategy="lines") for tables
    ruled in both directions (Word, Google Docs, LibreOffice exports).
  Rule-band tables: LaTeX/booktabs and ReportLab tables draw only
    horizontal rules. Rules sharing an x-extent form a group; rows come
    from the bands between rules, columns from x positions where a column
    starts in most rows, plus x ranges that no word covers.

Cell text is rebuilt from the page's characters (rawdict), grouped into
Lines and Spans the same way extract.py builds them, so fonts, bold,
italic and monospace survive. Words are assigned to a cell whole, by
their starting x, so text that overruns into the next column stays in its
own cell.

Known gaps: a booktabs table split by a page break is not detected (each
part has too few rules); column boundaries are ambiguous for tables with
very few rows. Both are caught downstream by the rule checks or by
disagreement with the other extractors.
"""

import logging
from collections import Counter

from .types import Line, Span, TableCandidate
from .mono import classify_monospace

_log = logging.getLogger(__name__)

_MUPDF_BOLD_BIT = 1 << 4
_MUPDF_ITALIC_BIT = 1 << 1

_RULE_MAX_THICK = 2.5     # a "rule" is a line or a very thin filled rect
_RULE_MIN_LEN = 40.0
_FILL_MAX_HEIGHT = 60.0   # taller filled boxes are panels, not row shading
_RULE_JOIN_GAP = 2.0      # Word draws one segment per cell; join them
_RULE_MERGE_Y = 3.5       # booktabs double rules collapse to one
_RULE_SAME_X = 3.0
_MIN_RULES = 3            # top + mid + bottom
_PER_ROW_RULES = 5        # at least this many rules: one rule per row
_HEADER_ABOVE = 16.0      # height of a header line above a double rule
_COL_GAP_MIN = 1.5        # x range no word covers separates columns...
_COL_GAP_EM = 0.6         # ...if this share of a line height wide, or if
_COL_GAP_PAIRS = 3        #    this many distinct word pairs straddle it
_COL_START_TOL = 3.0      # word starts within this distance share a column
_COL_START_SUPPORT = 0.6  # a column start must occur in this share of rows
_LINE_Y_TOL = 3.0         # characters within this y distance share a line
_CAPTION_INDENT = 4.0     # captions start this far left of padded cell text


# --------------------------------------------------------------------------
# Characters -> Lines/Spans
# --------------------------------------------------------------------------


def _page_chars(raw: dict) -> list[tuple]:
    """(char, bbox, font, size, flags, color) for every character on the page."""
    out = []
    for blk in raw.get("blocks", []):
        if blk.get("type") != 0:
            continue
        for ln in blk.get("lines", []):
            for sp in ln.get("spans", []):
                for ch in sp.get("chars", []):
                    if ch.get("c"):
                        out.append((ch["c"], tuple(ch["bbox"]), sp.get("font", ""),
                                    sp.get("size", 0.0), sp.get("flags", 0),
                                    sp.get("color", 0)))
    return out


def _page_words(raw: dict) -> list[tuple]:
    """Words from the PDF's own character runs.

    Each word is (x0, y0, x1, y1, text, chars, space_after): every character
    belongs to exactly one word even where text from two columns overprints,
    and space_after records whether the PDF put a space character after it.
    """
    words = []
    for blk in raw.get("blocks", []):
        if blk.get("type") != 0:
            continue
        for ln in blk.get("lines", []):
            cur: list[tuple] = []

            def flush(space_after):
                if cur:
                    bbs = [c[1] for c in cur]
                    words.append((min(b[0] for b in bbs), min(b[1] for b in bbs),
                                  max(b[2] for b in bbs), max(b[3] for b in bbs),
                                  "".join(c[0] for c in cur), list(cur), space_after))
                    cur.clear()

            for sp in ln.get("spans", []):
                for ch in sp.get("chars", []):
                    c = ch.get("c")
                    if not c:
                        continue
                    if c.isspace():
                        flush(True)
                        continue
                    cur.append((c, tuple(ch["bbox"]), sp.get("font", ""), sp.get("size", 0.0),
                                sp.get("flags", 0), sp.get("color", 0)))
            flush(False)
    return words


def _word_chars(ws: list[tuple]) -> list[tuple]:
    """Characters of a cell's words, with the PDF's spaces between them."""
    out: list[tuple] = []
    for _, _, lw in _text_lines(ws):
        lw = sorted(lw, key=lambda w: w[0])
        for i, w in enumerate(lw):
            out += w[5]
            if w[6] and i + 1 < len(lw):
                last = w[5][-1]
                out.append((" ", (last[1][2], last[1][1], last[1][2] + 0.01, last[1][3])) + last[2:])
    return out


def _chars_to_lines(chars: list[tuple], page_num: int) -> list[Line]:
    """Group characters into Lines of Spans (same font run = one span)."""
    rows: list[list] = []
    for ch in sorted(chars, key=lambda c: (c[1][1] + c[1][3]) / 2):
        yc = (ch[1][1] + ch[1][3]) / 2
        if rows and yc - rows[-1][0] < _LINE_Y_TOL:
            rows[-1][1].append(ch)
        else:
            rows.append([yc, [ch]])
    lines = []
    for _, row in rows:
        row.sort(key=lambda c: c[1][0])
        spans: list[Span] = []
        prev = None
        for ch in row:
            c, bb, font, size, flags, color = ch
            gap = bb[0] - prev[1][2] if prev else 0.0
            space = (prev is not None and gap > 0.25 * max(size, 1.0)
                     and c != " " and prev[0] != " ")
            same_run = (spans and prev is not None and font == prev[2]
                        and size == prev[3] and flags == prev[4] and color == prev[5])
            if same_run:
                s = spans[-1]
                s.text += (" " if space else "") + c
                s.bbox = (s.bbox[0], min(s.bbox[1], bb[1]), bb[2], max(s.bbox[3], bb[3]))
            else:
                if space and spans:
                    spans[-1].text += " "
                spans.append(Span(
                    text=c, font_name=font, font_size=size,
                    bold=bool(flags & _MUPDF_BOLD_BIT),
                    italic=bool(flags & _MUPDF_ITALIC_BIT),
                    monospace=classify_monospace(font),
                    bbox=bb, origin=(bb[0], bb[3]), color=color,
                ))
            prev = ch
        spans = [s for s in spans if s.text]
        if spans and "".join(s.text for s in spans).strip():
            x0 = min(s.bbox[0] for s in spans); x1 = max(s.bbox[2] for s in spans)
            y0 = min(s.bbox[1] for s in spans); y1 = max(s.bbox[3] for s in spans)
            lines.append(Line(spans=spans, bbox=(x0, y0, x1, y1), page_num=page_num))
    return lines


def _chars_in(chars, rect) -> list[tuple]:
    x0, y0, x1, y1 = rect
    return [c for c in chars
            if x0 <= (c[1][0] + c[1][2]) / 2 <= x1 and y0 <= (c[1][1] + c[1][3]) / 2 <= y1]


# --------------------------------------------------------------------------
# Grid tables (ruled both ways)
# --------------------------------------------------------------------------


def _vertical_rule_count(drawings) -> int:
    n = 0
    for d in drawings:
        for it in d["items"]:
            if it[0] == "l" and abs(it[1].x - it[2].x) < 1.0 and abs(it[1].y - it[2].y) >= 8.0:
                n += 1
            elif it[0] == "re" and it[1].width <= _RULE_MAX_THICK and it[1].height >= 8.0:
                n += 1
    return n


def _grid_tables(page, page_num, chars, drawings) -> list[TableCandidate]:
    # find_tables is the costliest step of conversion; a grid needs at least
    # two vertical rules, so pages without them are skipped.
    if _vertical_rule_count(drawings) < 2:
        return []
    out = []
    for t in page.find_tables(strategy="lines").tables:
        rows = []
        for r in t.rows:
            row = []
            for cell in r.cells:
                row.append(_chars_to_lines(_chars_in(chars, cell), page_num) if cell else [])
            rows.append(row)
        rows = _drop_empty(rows)
        if len(rows) < 2 or max(len(r) for r in rows) < 2:
            continue
        out.append(TableCandidate("grid", rows, {page_num: tuple(t.bbox)}))
    return out


def _drop_empty(rows):
    """Remove rows and columns in which every cell is empty."""
    rows = [r for r in rows if any(r)]
    if not rows:
        return rows
    ncol = max(len(r) for r in rows)
    keep = [j for j in range(ncol) if any(j < len(r) and r[j] for r in rows)]
    return [[r[j] if j < len(r) else [] for j in keep] for r in rows]


# --------------------------------------------------------------------------
# Rule-band tables (horizontal rules only)
# --------------------------------------------------------------------------


def _horizontal_rules(drawings) -> list[tuple[float, float, float]]:
    segs = []
    for d in drawings:
        for it in d["items"]:
            if it[0] == "l":
                a, b = it[1], it[2]
                if abs(a.y - b.y) < 1.0:
                    segs.append(((a.y + b.y) / 2, min(a.x, b.x), max(a.x, b.x)))
            elif it[0] == "re":
                r = it[1]
                if r.height <= _RULE_MAX_THICK:
                    segs.append(((r.y0 + r.y1) / 2, r.x0, r.x1))
                elif d.get("fill") is not None and r.height <= _FILL_MAX_HEIGHT:
                    # a shaded header row or zebra stripe: both edges bound a row
                    segs.append((r.y0, r.x0, r.x1))
                    segs.append((r.y1, r.x0, r.x1))
    segs.sort(key=lambda s: (round(s[0]), s[1]))
    rules: list[list[float]] = []
    for y, x0, x1 in segs:
        if rules and abs(rules[-1][0] - y) < 1.0 and x0 - rules[-1][2] <= _RULE_JOIN_GAP:
            rules[-1][2] = max(rules[-1][2], x1)
        else:
            rules.append([y, x0, x1])
    return sorted(tuple(r) for r in rules if r[2] - r[1] >= _RULE_MIN_LEN)


def _rule_groups(rules):
    """Group rules sharing an x-extent. Returns [(rules, header_above)].

    header_above marks the IEEE/revtex style: the header line sits above a
    doubled rule with no rule over it, and each later rule is drawn above
    its row, so the last row hangs below the last rule.
    """
    groups: list[list] = []
    doubled: dict[int, bool] = {}
    for y, x0, x1 in rules:
        for gi, g in enumerate(groups):
            if abs(g[0][1] - x0) <= _RULE_SAME_X and abs(g[0][2] - x1) <= _RULE_SAME_X:
                if y - g[-1][0] > _RULE_MERGE_Y:
                    g.append((y, x0, x1))
                elif len(g) == 1:
                    doubled[gi] = True
                break
        else:
            groups.append([(y, x0, x1)])
    return [(g, doubled.get(gi, False)) for gi, g in enumerate(groups)
            if len(g) >= (_MIN_RULES - 1 if doubled.get(gi) else _MIN_RULES)]


def _text_lines(words):
    """Cluster words into text lines by y-centre: [(top, bottom, words)]."""
    lines: list[list] = []
    for w in sorted(words, key=lambda w: (w[1] + w[3]) / 2):
        yc = (w[1] + w[3]) / 2
        if lines and yc - lines[-1][3] < 2.5:
            lines[-1][2].append(w)
            lines[-1][0] = min(lines[-1][0], w[1]); lines[-1][1] = max(lines[-1][1], w[3])
            lines[-1][3] = yc
        else:
            lines.append([w[1], w[3], [w], yc])
    return [(a, b, ws) for a, b, ws, _ in lines]


def _column_starts(row_words: list[list]) -> list[float]:
    """Column boundaries for a block of rows.

    Union of two signals: (1) gaps in the union of word extents that no
    row covers; (2) x positions where a word starts after a visible gap in
    at least _COL_START_SUPPORT of the rows - this survives a cell that
    overruns into the next column, which closes the gap in signal 1.
    Returns the sorted x of each column's left boundary (first is -inf).
    """
    words = [w for ws in row_words for w in ws]
    # A narrow x range that no row covers is a column gap only when rows
    # disagree about what sits on either side of it (distinct word pairs
    # across it); identical repeated text, or a table of one or two rows,
    # leaves coincidental gaps between ordinary words. Those gaps must be
    # wide to count.
    heights = sorted(w[3] - w[1] for w in words)
    wide = max(_COL_GAP_MIN, _COL_GAP_EM * heights[len(heights) // 2])
    ivs = sorted((w[0], w[2]) for w in words)
    merged = [list(ivs[0])]
    for a, b in ivs[1:]:
        if a - merged[-1][1] < _COL_GAP_MIN:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    seps = set()
    for i in range(len(merged) - 1):
        g0, g1 = merged[i][1], merged[i + 1][0]
        pairs = set()
        for ws in row_words:
            for _, _, lw in _text_lines(ws):
                left = [w for w in lw if w[2] <= g0 + 0.5]
                right = [w for w in lw if w[0] >= g1 - 0.5]
                if left and right:
                    pairs.add((max(left, key=lambda w: w[2])[4], min(right, key=lambda w: w[0])[4]))
        if g1 - g0 >= wide or len(pairs) >= _COL_GAP_PAIRS:
            seps.add((g0 + g1) / 2)

    starts: Counter[int] = Counter()
    for ws in row_words:
        seen = set()
        ws = sorted(ws, key=lambda w: w[0])
        for i, w in enumerate(ws):
            gap_before = w[0] - ws[i - 1][2] if i else 1e9
            size = w[3] - w[1]
            if gap_before > 0.9 * size:
                k = round(w[0] / _COL_START_TOL)
                if k not in seen:
                    seen.add(k); starts[k] += 1
    left = min(w[0] for w in words)
    need = max(2, _COL_START_SUPPORT * len(row_words))
    for k, n in starts.items():
        x = k * _COL_START_TOL
        if n >= need and x - left > 2 * _COL_START_TOL:
            if not any(abs(x - s) < 4 * _COL_START_TOL for s in seps):
                seps.add(x - _COL_START_TOL)
    return [float("-inf")] + sorted(seps)


def _is_caption_band(lw: list, cell_left: float) -> bool:
    """A band holding a single line that starts left of where cell text
    starts (cells are padded, captions are not): e.g. "Bounds (3)", the
    caption of the next table, not a row of this one."""
    return len(_text_lines(lw)) == 1 and min(w[0] for w in lw) < cell_left - _CAPTION_INDENT


def _rule_band_tables(page_num, words_all, group, header_above) -> list[TableCandidate]:
    ys = [g[0] for g in group]
    x0 = min(g[1] for g in group) - 2
    x1 = max(g[2] for g in group) + 2
    if header_above:
        step = min(b - a for a, b in zip(ys, ys[1:])) if len(ys) > 1 else 14.0
        step = min(max(step, 11.0), 16.0)
        ys = [ys[0] - _HEADER_ABOVE] + ys + [ys[-1] + step]
    in_x = [w for w in words_all if w[0] >= x0 and w[2] <= x1]
    words = [w for w in in_x if ys[0] < (w[1] + w[3]) / 2 < ys[-1]]
    if not words:
        return []

    per_row_rules = len(ys) >= _PER_ROW_RULES
    band_words = [(top, bot, [w for w in words if top < (w[1] + w[3]) / 2 < bot])
                  for top, bot in zip(ys, ys[1:])]
    # where cell text usually starts: the commonest left edge of the bands
    lefts = Counter(round(min(w[0] for w in bw)) for _, _, bw in band_words if bw)
    cell_left = lefts.most_common(1)[0][0] if lefts else x0
    segments: list[list[tuple[float, float]]] = [[]]
    for top, bot, bw in band_words:
        if not bw:
            continue
        if per_row_rules:
            if _is_caption_band(bw, cell_left) and segments[-1]:
                segments.append([])         # two tables share the rules' width
                continue
            segments[-1].append((top, bot))
        else:
            segments[-1].extend((a - 1, b + 1) for a, b, _ in _text_lines(bw))
    out = []
    for bands in segments:
        t = _bands_to_table(page_num, in_x, bands, x0, x1, header_above)
        if t is not None:
            out.append(t)
    return out


def _bands_to_table(page_num, in_x, bands, x0, x1, header_above) -> TableCandidate | None:
    if len(bands) < 2:
        return None
    row_words = [[w for w in in_x if a <= (w[1] + w[3]) / 2 <= b] for a, b in bands]
    seps = _column_starts(row_words)
    if len(seps) < 2:
        return None
    top = bands[0][0]

    # A header line just above the first rule, aligned with the columns,
    # belongs to the table (tables whose top rule is under the header).
    if not header_above:
        above = [w for w in in_x if top - 18.0 < (w[1] + w[3]) / 2 < top]
        if above:
            col_of = lambda w: sum(1 for s in seps if w[0] >= s) - 1
            col_x: dict[int, float] = {}
            for w in (w for ws in row_words for w in ws):
                col_x[col_of(w)] = min(col_x.get(col_of(w), w[0]), w[0])
            aligned = {col_of(w) for w in above
                       if abs(w[0] - col_x.get(col_of(w), -1e9)) <= _COL_START_TOL}
            if len(aligned) >= 2:
                top = min(w[1] for w in above) - 1
                row_words.insert(0, above)

    rows = []
    for ws in row_words:
        cells: list[list] = [[] for _ in seps]
        for w in ws:
            cells[sum(1 for s in seps if w[0] >= s) - 1].append(w)
        rows.append([_chars_to_lines(_word_chars(cw), page_num) for cw in cells])
    rows = _drop_empty(rows)
    if len(rows) < 2 or max(len(r) for r in rows) < 2:
        return None
    return TableCandidate("rules", rows, {page_num: (x0, top, x1, bands[-1][1])})


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def _overlaps(a, b) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def extract_ruled_tables(page, page_num: int) -> list[TableCandidate]:
    """All tables on one page that ruling lines reveal."""
    drawings = page.get_drawings()
    if not any(it[0] in ("l", "re") for d in drawings for it in d["items"]):
        return []                       # nothing drawn: no ruled table
    raw = page.get_text("rawdict", flags=0)
    chars = _page_chars(raw)
    words = _page_words(raw)
    tables = _grid_tables(page, page_num, chars, drawings)
    grids = [t.bboxes[page_num] for t in tables]
    for group, header_above in _rule_groups(_horizontal_rules(drawings)):
        bb = (min(r[1] for r in group), group[0][0] - (_HEADER_ABOVE if header_above else 0),
              max(r[2] for r in group), group[-1][0])
        if any(_overlaps(bb, g) for g in grids):
            continue
        tables.extend(_rule_band_tables(page_num, words, group, header_above))
    if tables:
        _log.debug("Page %d: %d ruled table(s)", page_num, len(tables))
    return tables
