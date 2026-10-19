"""One content-first row/column builder for every table class.

The layout class only locates the region; inside it, rows and columns come
from the words themselves, top down:

  lines    words sharing a baseline (vertical overlap) form a visual line
  pieces   words in a line closer than a word gap form a piece (a phrase)
  columns  gutters: x ranges that (almost) no piece crosses, over all lines;
           columns are the spans between gutters that hold pieces. A piece
           crossing a gutter in at most _SPAN_LINES lines is a spanning cell
           (a header over several columns), not evidence against the gutter.
  rows     a line starts a new row when the vertical gap above it is a row
           gap (the region's own natural break between line leading and row
           spacing), or - when gaps do not separate rows (LaTeX booktabs,
           p{} wraps with row spacing equal to leading) - when it has text in
           the key column (the leftmost column filled in most rows) and the
           line above was not a lone wrap of that column. A line that fills
           only some columns, continuing cells from above, joins the row
           above (wrap continuation).
  cells    the pieces of each row and column, joined in reading order.

Every decision is recorded (`trace`) so a specialist's evidence can be
compared against it: drawn rules, box edges and tags confirm or contradict
this grid; they do not build it.
"""
from __future__ import annotations

import logging
from collections import Counter

from .types import TableCandidate
from .types import Line, Span  # noqa: E402

_log = logging.getLogger(__name__)

_WORD_GAP = 0.6        # a gap below this many line heights stays inside a piece
_MIN_GUTTER = 4.0      # points: narrower white space is word spacing, not a column
_SPAN_LINES = 1        # a gutter may be crossed by this many lines (spanning cells)
_GAP_RATIO = 1.5       # row gap: at least this many times the typical leading
_KEY_FILL = 0.5        # key column: filled in at least this share of rows


def visual_lines(words):
    """words: (x0, y0, x1, y1, text) -> lines of words sorted left to right."""
    ws = sorted(words, key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    lines: list[list] = []
    for w in ws:
        h = w[3] - w[1]
        if lines:
            ln = lines[-1]
            top, bot = min(x[1] for x in ln), max(x[3] for x in ln)
            if min(bot, w[3]) - max(top, w[1]) >= 0.5 * min(h, bot - top):
                ln.append(w)
                continue
        lines.append([w])
    return [sorted(ln, key=lambda w: w[0]) for ln in lines]


def pieces_of(line):
    h = max(w[3] - w[1] for w in line)
    out: list[list] = []
    for w in line:
        if out and w[0] - out[-1][-1][2] < _WORD_GAP * h:
            out[-1].append(w)
        else:
            out.append([w])
    return [(min(w[0] for w in p), max(w[2] for w in p), p) for p in out]


def gutters(lines_pieces, x_lo, x_hi):
    """x intervals crossed by at most _SPAN_LINES lines' pieces."""
    step = 1.0
    n = int((x_hi - x_lo) / step) + 1
    cross = [0] * n
    for ps in lines_pieces:
        seen = [False] * n
        for a, b, _ in ps:
            for i in range(max(0, int((a - x_lo) / step)), min(n, int((b - x_lo) / step) + 1)):
                seen[i] = True
        for i in range(n):
            cross[i] += seen[i]
    limit = _SPAN_LINES if len(lines_pieces) > 3 * _SPAN_LINES else 0
    out, start = [], None
    for i in range(n):
        free = cross[i] <= limit
        if free and start is None:
            start = i
        if (not free or i == n - 1) and start is not None:
            end = i if not free else i + 1
            if (end - start) * step >= _MIN_GUTTER and start > 0 and end < n:
                out.append((x_lo + start * step, x_lo + end * step))
            start = None
    return out


SPECIALISTS = {"code_rows": True, "separators": True}


def build(words, hrules=(), specialists=None):
    """-> (rows of cell strings, trace).

    hrules: y positions of drawn horizontal separators that cross most of the
    region (a specialist's evidence at the row level: a drawn line between
    two text lines separates rows; no line is not evidence of anything)."""
    sp = dict(SPECIALISTS, **(specialists or {}))
    trace = {"specialists": {}}
    lines = visual_lines(words)
    if len(lines) < 2:
        return [], {"abstain": "fewer than two lines"}
    lp = [pieces_of(ln) for ln in lines]
    x_lo = min(w[0] for w in words) - 1
    x_hi = max(w[2] for w in words) + 1
    # gutters from single words, not phrases: a narrow column ("." | "Period")
    # must not be merged away. Wider than the region's own word spacing.
    spaces = sorted(b[0] - a[2] for ln in lines for a, b in zip(ln, ln[1:]) if b[0] > a[2])
    lh = sorted(max(w[3] for w in ln) - min(w[1] for w in ln) for ln in lines)[len(lines) // 2]
    # word spacing from the tight gaps only: in a numeric table most gaps
    # between neighbouring words are column gaps
    word_space = min(spaces[len(spaces) // 4] if spaces else 2.5, 0.5 * lh)
    gs = [g for g in gutters([[(w[0], w[2], [w]) for w in ln] for ln in lines], x_lo, x_hi)
          if g[1] - g[0] >= max(_MIN_GUTTER, 1.6 * word_space)]
    bounds = [x_lo] + [(a + b) / 2 for a, b in gs] + [x_hi]
    ncol = len(bounds) - 1
    trace["gutters"] = [(round(a), round(b)) for a, b in gs]
    if ncol < 2:
        return [], {**trace, "abstain": "one column"}

    def col_of(x0, x1):
        xc = (x0 + x1) / 2
        for c in range(ncol):
            if bounds[c] <= xc < bounds[c + 1]:
                return c
        return ncol - 1
    grid_lines = []
    for ps in lp:
        cells: dict = {}
        for a, b, p in ps:
            cells.setdefault(col_of(a, b), []).extend(p)
        grid_lines.append(cells)
    tops = [min(w[1] for w in ln) for ln in lines]
    bots = [max(w[3] for w in ln) for ln in lines]
    gaps = [tops[i] - bots[i - 1] for i in range(1, len(lines))]
    heights = sorted(b - t for t, b in zip(tops, bots))
    h = heights[len(heights) // 2]
    leading = sorted(gaps)[len(gaps) // 4] if gaps else 0.0     # the tight end: line leading
    # the region's own natural break: the largest jump in the sorted gaps
    sg = sorted(gaps)
    jumps = [(b - a, (a + b) / 2) for a, b in zip(sg, sg[1:]) if b - a >= 1.5 and b >= a * 1.3 + 0.5]
    row_gap = max(jumps)[1] if jumps else max(leading * _GAP_RATIO, leading + 0.35 * h)
    code = sp["code_rows"] and len(words[0]) > 5 and sum(w[5] for w in words) >= 0.6 * len(words)
    if code:
        row_gap = max(row_gap, leading + 1.5 * h)     # a blank line inside code is not a row gap
    gap_votes = [g > row_gap for g in gaps]
    # gaps separate rows only when row gaps recur: a single wide gap is the
    # space under a header rule (booktabs), not the row pattern
    gaps_separate = sum(gap_votes) >= max(2, 0.2 * len(gaps)) and not all(gap_votes)
    fill = Counter(c for cl in grid_lines for c in cl)
    key = min((c for c in range(ncol) if fill[c] >= 2), default=0)   # leftmost column used on 2+ lines
    trace.update({"ncol": ncol, "key": key, "leading": round(leading, 1), "row_gap": round(row_gap, 1),
                  "gaps_separate": gaps_separate})
    # specialist at the row level: code cells. In code, every line has text
    # in the key column, so key-column starts say nothing; only row gaps do.
    trace["code"] = code
    # content's own row starts first
    content_new = [True]
    for i in range(1, len(grid_lines)):
        cl = grid_lines[i]
        if gap_votes[i - 1]:
            new = True
        elif gaps_separate or code:
            new = False
        else:
            prev = grid_lines[i - 1]
            lone_key_wrap = set(prev) == {key}
            new = key in cl and not (lone_key_wrap and len(cl) == 1)
        content_new.append(new)
    # specialist (row level): drawn separators confirm, add or contradict
    ruled = [False] + [any(bots[i - 1] - 1 <= y <= tops[i] + 1 for y in hrules) for i in range(1, len(lines))]
    final_new = list(content_new)
    if sp["separators"] and hrules:
        added = [i for i in range(1, len(lines)) if ruled[i] and not content_new[i]]
        starts_c = [i for i in range(1, len(lines)) if content_new[i]]
        confirmed = [i for i in starts_c if ruled[i]]
        every_row = len(starts_c) >= 2 and len(confirmed) >= 0.6 * len(starts_c) and len(confirmed) >= 2
        removed = [i for i in starts_c if every_row and not ruled[i]]
        for i in added:
            final_new[i] = True
        for i in removed:
            final_new[i] = False
        trace["specialists"]["separators"] = {"confirmed": len(confirmed), "added": added, "removed": removed,
                                              "rules_every_row": every_row}
    rows: list[dict] = [dict(grid_lines[0])]
    starts = [0]
    for i in range(1, len(grid_lines)):
        cl = grid_lines[i]
        new = final_new[i]
        if new:
            rows.append(dict(cl))
            starts.append(i)
        else:
            for c, ws in cl.items():
                rows[-1].setdefault(c, []).extend(ws)
    trace["row_starts"] = starts
    out = []
    for r in rows:
        # reading order inside a cell: its own visual lines (raised references
        # and superscripts stay on their line), left to right
        out.append([visual_lines(r.get(c, [])) for c in range(ncol)])
    # drop columns empty in every row (a gutter split inside white space)
    keep = [c for c in range(ncol) if any(r[c] for r in out)]
    return [[r[c] for c in keep] for r in out], trace


def build_text(words, hrules=(), specialists=None):
    """Rows of cell strings (for measurement)."""
    rows, trace = build(words, hrules, specialists)
    return [[" ".join(w[4] for ln in cell for w in ln) for cell in r] for r in rows], trace


_MONO_FONTS = ("mono", "courier", "code", "cmtt", "consol", "menlo", "lmmono")


def page_words(page) -> list[tuple]:
    """(x0, y0, x1, y1, text, monospace) for every word on the page."""
    spans = [(sp["bbox"], bool(sp["flags"] & 8) or any(k in sp["font"].lower() for k in _MONO_FONTS))
             for b in page.get_text("dict")["blocks"] for ln in b.get("lines", []) for sp in ln["spans"]]

    def mono(w):
        xc, yc = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
        return any(bb[0] <= xc <= bb[2] and bb[1] <= yc <= bb[3] and m for bb, m in spans)
    return [tuple(w[:5]) + (mono(w),) for w in page.get_text("words")]


def page_hrules(page, drawings=None) -> list[tuple[float, float, float]]:
    """Drawn horizontal separators on the page: (y, x0, x1)."""
    out = []
    for d in (page.get_drawings() if drawings is None else drawings):
        for it in d["items"]:
            if it[0] == "l" and abs(it[1].y - it[2].y) <= 1:
                out.append((it[1].y, min(it[1].x, it[2].x), max(it[1].x, it[2].x)))
            elif it[0] == "re" and it[1].height <= 2:
                r = it[1]
                out.append(((r.y0 + r.y1) / 2, r.x0, r.x1))
    return out


def _region_rules(rules, words):
    x0, x1 = min(w[0] for w in words), max(w[2] for w in words)
    y0, y1 = min(w[1] for w in words) - 4, max(w[3] for w in words) + 4
    return [y for y, a, b in rules if y0 <= y <= y1 and a <= x0 + 0.5 * (x1 - x0) and b - a >= 0.6 * (x1 - x0)]


def _cell_lines(cell, page_num) -> list[Line]:
    out = []
    for ln in cell:
        spans = []
        for i, w in enumerate(ln):
            if i:
                spans.append(Span(text=" ", monospace=w[5] if len(w) > 5 else False))
            spans.append(Span(text=w[4], bbox=tuple(w[:4]), monospace=w[5] if len(w) > 5 else False))
        out.append(Line(spans=spans, page_num=page_num,
                        bbox=(min(w[0] for w in ln), min(w[1] for w in ln),
                              max(w[2] for w in ln), max(w[3] for w in ln))))
    return out


def content_candidates(pages, regions, specialists=None, rules_by_page=None) -> list[TableCandidate]:
    """For every located region (page, bbox) - from any reader, kept or not -
    the content-first grid of the words inside it."""
    cache: dict = {}
    out: list[TableCandidate] = []
    seen = set()
    for page_num, bbox in regions:
        key = (page_num, tuple(round(v) for v in bbox))
        if key in seen:
            continue
        seen.add(key)
        if page_num not in cache:
            rules = (rules_by_page or {}).get(page_num)
            cache[page_num] = (page_words(pages[page_num]),
                               rules if rules is not None else page_hrules(pages[page_num]))
        words_all, rules = cache[page_num]
        x0, y0, x1, y1 = bbox
        words = [w for w in words_all if w[0] >= x0 - 2 and w[2] <= x1 + 2 and w[1] >= y0 - 2 and w[3] <= y1 + 2]
        if len(words) < 2:
            continue
        rows, trace = build(words, _region_rules(rules, words), specialists)
        if len(rows) < 2 or max(len(r) for r in rows) < 2:
            continue
        cells = [[_cell_lines(c, page_num) for c in r] for r in rows]
        cand = TableCandidate("content", cells, {page_num: bbox})
        cand.trace = trace
        out.append(cand)
    return out
