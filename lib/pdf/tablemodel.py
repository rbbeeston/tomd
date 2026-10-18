"""Lossless table model and its semantic flattening to plain Markdown.

Internally a table keeps spans: {"r", "c", "rows", "cols", "kind"} (0-based,
r/c = the cell holding the text), detected from the page geometry. Markdown
has no spans, so `flatten` renders them by meaning (the convention in the
PoC's work/TABLE_CONVENTION.md):

  header    a header cell over sub-headers -> combined headers "Top / Sub",
            the top row removed (over plain data: kept once)
  label     a category spanning rows        -> repeated in each row
  data      a shared value spanning cells   -> kept once (first cell)
  title     a full-width title/section row  -> kept once (first cell)
  ambiguous                                  -> kept as printed, flagged

and `marker` writes every span into an HTML comment beside the table, so
the structure stays machine-readable. `flatten` works on any grid of cell
values given `empty` and `combine` callbacks, so the Markdown renderer
(cells of spans) and the scorer (cells of text) share it.
"""

import re

SEP = " / "
_NUMERIC = re.compile(r"^[\d\s.,:%+\-–—/×()]+$")
_TOL = 3.0


def flatten(grid, spans, empty, combine):
    """(new grid, kept spans) with the flattening convention applied."""
    grid = [list(r) for r in grid]
    spans = sorted(spans, key=lambda s: (s["r"], s["c"]))
    # 1. header spans: combine the header row with the row under it
    for r in sorted({s["r"] for s in spans if s["kind"] == "header"}, reverse=True):
        if r + 1 >= len(grid) or not _two_level(grid, spans, r, empty):
            continue                     # a spanning header over data: kept once
        top, sub = grid[r], grid[r + 1]
        covered = {}
        for s in spans:
            if s["kind"] == "header" and s["r"] == r:
                for j in range(s["c"], min(s["c"] + s["cols"], len(sub))):
                    covered[j] = top[s["c"]]
        for j in range(len(sub)):
            if j in covered:
                sub[j] = combine(covered[j], sub[j]) if not empty(sub[j]) else covered[j]
            elif j < len(top) and not empty(top[j]):
                sub[j] = combine(top[j], sub[j]) if not empty(sub[j]) else top[j]
        del grid[r]
    # 2. label spans: fill down
    removed = sorted({s["r"] for s in spans if s["kind"] == "header"})
    shift = lambda r: r - sum(1 for x in removed if x < r)
    for s in spans:
        if s["kind"] != "label":
            continue
        r0 = shift(s["r"])
        for i in range(1, s["rows"]):
            if r0 + i < len(grid) and s["c"] < len(grid[r0 + i]) and empty(grid[r0 + i][s["c"]]):
                grid[r0 + i][s["c"]] = grid[r0][s["c"]]
    return grid, spans


def _two_level(grid, spans, r, empty) -> bool:
    """Rows r and r+1 form one two-level header when some header cell spans
    both rows ("Group" beside "GCC" over "v1 v2"). A row of data under a
    spanning header looks just like sub-headers, so nothing weaker counts."""
    return any(s["kind"] == "header" and s["r"] == r and s["rows"] >= 2 for s in spans)


def flatten_text(rows, spans):
    """Text grid version (used by the scorer)."""
    sep = SEP if not any(SEP in c for r in rows for c in r) else " ⁄ "
    out, _ = flatten(rows, spans, lambda c: not c.strip(), lambda a, b: f"{a}{sep}{b}")
    return out


def marker(spans) -> str:
    """<!-- tomd:merged ... --> for the spans (1-based rows/columns)."""
    parts = []
    for s in sorted(spans, key=lambda s: (s["r"], s["c"])):
        rows = f"row={s['r'] + 1}" if s["rows"] == 1 else f"rows={s['r'] + 1}-{s['r'] + s['rows']}"
        cols = f"col={s['c'] + 1}" if s["cols"] == 1 else f"cols={s['c'] + 1}-{s['c'] + s['cols']}"
        parts.append(f"{s['kind']} {rows} {cols}")
    return f"<!-- tomd:merged {'; '.join(parts)} -->" if parts else ""


# ------------------------------------------------------------ detection

def _box(cell):
    bs = [s.bbox for s in cell if s.text.strip() and s.text != "\n" and s.bbox]
    if not bs:
        return None
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))


def _text(cell) -> str:
    return " ".join(s.text for s in cell if s.text != "\n").strip()


def detect_spans(columns) -> list[dict]:
    """Spans read from the geometry of a table's cells (lists of spans).

    - header: a row-0 cell whose text runs over the column(s) to its right,
      which are empty in row 0, with sub-headers under them in row 1;
    - title: any other row whose only text runs across columns;
    - label/data: a cell vertically centred across rows below it whose
      cells in its column are empty (multirow); a cell aligned with the top
      of its row cannot be told from an empty cell below it, so it is left
      alone.
    """
    if len(columns) < 2:
        return []
    ncol = max(len(r) for r in columns)
    grid = [list(r) + [[] for _ in range(ncol - len(r))] for r in columns]
    boxes = [[_box(c) for c in r] for r in grid]
    bands = []
    for c in range(ncol):
        xs = [boxes[r][c] for r in range(len(grid)) if boxes[r][c]
              and sum(1 for b in boxes[r] if b) > 1]
        bands.append((min(b[0] for b in xs), max(b[2] for b in xs)) if xs else None)
    spans = []

    def run_right(r, c):
        b = boxes[r][c]
        k = 1
        while c + k < ncol and not boxes[r][c + k] and bands[c + k] and b[2] > bands[c + k][0] + _TOL:
            k += 1
        return k

    for r in range(len(grid)):
        filled = [c for c in range(ncol) if boxes[r][c]]
        for c in filled:
            k = run_right(r, c)
            if k < 2:
                continue
            if r == 0 and len(grid) > 2 and sum(1 for j in range(c, c + k) if boxes[1][j]) >= 2:
                spans.append({"r": 0, "c": c, "rows": 1, "cols": k, "kind": "header"})
                # header cells beside it with nothing under them span both rows
                for j in range(ncol):
                    if boxes[0][j] and not boxes[1][j] and not (c <= j < c + k) and not any(
                            s["r"] == 0 and s["c"] == j for s in spans):
                        spans.append({"r": 0, "c": j, "rows": 2, "cols": 1, "kind": "header"})
            elif len(filled) == 1:
                spans.append({"r": r, "c": c, "rows": 1, "cols": k, "kind": "title"})
            else:
                spans.append({"r": r, "c": c, "rows": 1, "cols": k, "kind": "ambiguous"})
    # vertical: a cell centred across the rows below it
    for c in range(ncol):
        r = 0
        while r < len(grid):
            b = boxes[r][c]
            if not b:
                r += 1
                continue
            k = 1
            while (r + k < len(grid) and not boxes[r + k][c]
                   and any(boxes[r + k][j] for j in range(ncol) if j != c)):
                k += 1
            if k >= 2:
                others = [bx for i in range(r, r + k) for j, bx in enumerate(boxes[i]) if j != c and bx]
                top, bot = min(o[1] for o in others), max(o[3] for o in others)
                mid = (b[1] + b[3]) / 2
                row_mid = [(min(bx[1] for j, bx in enumerate(boxes[i]) if bx and j != c) +
                            max(bx[3] for j, bx in enumerate(boxes[i]) if bx and j != c)) / 2
                           for i in range(r, r + k) if any(bx for j, bx in enumerate(boxes[i]) if j != c)]
                # centred across the group, clearly below the first row's middle
                if row_mid and abs(mid - (top + bot) / 2) <= _TOL * 2 and mid > row_mid[0] + _TOL:
                    kind = "data" if _NUMERIC.match(_text(grid[r][c])) else "label"
                    spans.append({"r": r, "c": c, "rows": k, "cols": 1, "kind": kind})
            r += k
    return spans
