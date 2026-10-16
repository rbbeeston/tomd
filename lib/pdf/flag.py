"""Mark text that is probably a table but was not extracted as one.

The table sources only emit what passes their checks, so a real table can
reach the output as plain paragraphs or code with no warning. This module
looks at what is left after table selection and marks the sections in
table-like areas uncertain (their text is kept as it is), so a reader or an
LLM pass knows to rebuild them. Two kinds of evidence:

  - a drawing or tag source found a table there, but the rule checks
    rejected its reading (select_tables' `rejected` list);
  - the text itself is laid out like a table: a run of rows split into
    columns by wide gaps, with the columns starting at the same x positions
    from row to row, or a vote line ("SF F N A SA", "Favor: 8 ...").

Nothing here decides cell boundaries; it only says "look here".
"""

import logging
import re
from collections import defaultdict

from .types import Block, Section, SectionKind, TableCandidate

_log = logging.getLogger(__name__)

_COL_GAP = 10.0          # a gap this wide (pt) between spans separates columns
_START_TOL = 3.0         # column starts closer than this are the same column
_MIN_RUN = 3             # rows in a run of aligned multi-column rows
_ROW_SPACING = 2.2       # next row starts within this many line heights
_PROSE_WIDTH = 0.3       # a segment wider than this share of the text width is prose
_VOTE = re.compile(r"^(SF\s+F\s+N\s+A\s+SA|F\s+N\s+A)$|\b(Favou?r|Against|Neutral)\s*:\s*\d", re.I)
_COMMENT = ("//", "/*", "#")
_INT = re.compile(r"^\d{1,4}$")
_ALNUM = re.compile(r"[^\W_]")
_EXTRA_SECTIONS = 2      # a table read as text: about one section per row, plus a few
# Rule-check flags that mean "a table, read wrongly" (as opposed to "not a
# table at all": numbered-list, reference-list, single-cell-rows, ...).
_MISREAD_FLAGS = {"ragged-columns", "split-code", "sparse-two-rows"}
_KEEP_KINDS = (SectionKind.TITLE, SectionKind.METADATA, SectionKind.HEADING,
               SectionKind.TABLE)

# page, bbox, reason, rows: the area holds about `rows` rows of a table
Region = tuple[int, tuple[float, float, float, float], str, int]


def _rows(blocks: list[Block]) -> dict[int, list[tuple[float, float, list]]]:
    """Per page: (top, bottom, segments) rows, segments = [(x0, x1, text, mono)]."""
    spans = defaultdict(list)
    for blk in blocks:
        for ln in blk.lines:
            for s in ln.spans:
                if s.text.strip():
                    spans[ln.page_num].append(s)
    out = {}
    for page, ss in spans.items():
        ss.sort(key=lambda s: ((s.bbox[1] + s.bbox[3]) / 2, s.bbox[0]))
        rows: list[list] = []
        for s in ss:
            yc = (s.bbox[1] + s.bbox[3]) / 2
            if rows and abs(yc - rows[-1][0]) <= 0.4 * max(s.bbox[3] - s.bbox[1], 1):
                rows[-1][1].append(s)
            else:
                rows.append([yc, [s]])
        page_rows = []
        for _, rs in rows:
            rs.sort(key=lambda s: s.bbox[0])
            segs = []
            for s in rs:
                if segs and s.bbox[0] - segs[-1][1] < _COL_GAP:
                    x0, _, t, m = segs[-1]
                    segs[-1] = (x0, max(segs[-1][1], s.bbox[2]), t + " " + s.text.strip(),
                                m and s.monospace)
                else:
                    segs.append((s.bbox[0], s.bbox[2], s.text.strip(), s.monospace))
            page_rows.append((min(s.bbox[1] for s in rs), max(s.bbox[3] for s in rs), segs))
        out[page] = page_rows
    return out


def _is_table_row(segs, width: float) -> bool:
    if len(segs) < 2:
        return False
    if any(s[2].startswith(_COMMENT) for s in segs[1:]):
        return False                     # code with a comment column
        return False
    if any(x1 - x0 > _PROSE_WIDTH * width for x0, x1, _, _ in segs):
        return False                     # two-column page layout or a long line
    return True


def _is_not_table(run, page: int) -> bool:
    """Contents, numbered code, front matter or prose columns, not a table."""
    if _is_toc_or_listing(run):
        return True
    first = [r[2][0][2] for r in run]
    if page == 0 and sum(t.endswith(":") for t in first) >= 0.5 * len(run):
        return True                      # "Document number: P1234" front matter
    wordy = sum(all(len(g[2].split()) >= 5 for g in r[2]) for r in run)
    return wordy >= 0.6 * len(run)       # every piece a phrase: prose in columns


def _is_toc_or_listing(run) -> bool:
    """Contents lines (title ... page) or numbered code lines, not a table."""
    last = [r[2][-1][2] for r in run]
    if sum(bool(_INT.match(t)) for t in last) >= 0.8 * len(run):
        nums = [int(t) for t in last if _INT.match(t)]
        if nums == sorted(nums):
            return True
    first = [r[2][0][2] for r in run]
    if all(_INT.match(t) for t in first):
        nums = [int(t) for t in first]
        if all(b == a + 1 for a, b in zip(nums, nums[1:])):
            return True
    return False


def _shared_starts(a, b) -> int:
    return sum(1 for x in a for y in b if abs(x - y) <= _START_TOL)


def text_regions(blocks: list[Block]) -> list[Region]:
    """Table-like areas in the remaining text."""
    out: list[Region] = []
    for page, rows in _rows(blocks).items():
        if not rows:
            continue
        width = max(r[2][-1][1] for r in rows) - min(r[2][0][0] for r in rows) or 1.0
        for top, bot, segs in rows:
            text = " ".join(t for _, _, t, _ in segs)
            # laid out in columns, not a sentence that reports a vote
            if len(segs) >= 3 and _VOTE.search(text):
                out.append((page, (segs[0][0], top, segs[-1][1], bot), "vote line", 1))
        run: list = []

        def close():
            if len(run) >= _MIN_RUN and not _is_not_table(run, page):
                out.append((page, (min(r[2][0][0] for r in run), run[0][0],
                                   max(r[2][-1][1] for r in run), run[-1][1]),
                            f"{len(run)} rows aligned in columns", len(run)))

        for top, bot, segs in rows:
            segs = [g for g in segs if _ALNUM.search(g[2])]    # bullets, boxes
            if not segs:
                continue
            ok = _is_table_row(segs, width)
            if ok and run:
                prev = run[-1]
                near = top - prev[1] <= _ROW_SPACING * max(prev[1] - prev[0], 1)
                aligned = _shared_starts([s[0] for s in prev[2]], [s[0] for s in segs]) >= 2
                if not (near and aligned):
                    close()
                    run = []
            if ok:
                run.append((top, bot, segs))
            else:
                close()
                run = []
        close()
    return out


def rejected_regions(rejected: list[TableCandidate], tables: list[Section]) -> list[Region]:
    """Areas of rejected drawing/tag tables that no selected table covers."""
    taken = defaultdict(list)
    for t in tables:
        for ln in t.lines:
            taken[ln.page_num].append(ln.bbox)
    out = []
    for c in rejected:
        if len(c.rows) < 2 or max(len(r) for r in c.rows) < 2:
            continue
        if not set(c.flags) <= _MISREAD_FLAGS:
            continue
        for page, (x0, y0, x1, y1) in c.bboxes.items():
            if any(x0 <= (b[0] + b[2]) / 2 <= x1 and y0 <= (b[1] + b[3]) / 2 <= y1
                   for b in taken[page]):
                continue
            out.append((page, (x0, y0, x1, y1),
                        f"the {c.source} extractor found a table here but its reading "
                        f"failed the checks ({', '.join(c.flags) or 'unknown'})", len(c.rows)))
    return out


def flag_possible_tables(sections: list[Section], regions: list[Region]) -> int:
    """Mark sections with a line inside a region; returns how many."""
    def inside(sec, page, bbox):
        x0, y0, x1, y1 = bbox
        return any(ln.page_num == page
                   and x0 - 2 <= (ln.bbox[0] + ln.bbox[2]) / 2 <= x1 + 2
                   and y0 - 2 <= (ln.bbox[1] + ln.bbox[3]) / 2 <= y1 + 2
                   for ln in sec.lines)

    n = 0
    for page, bbox, reason, rows in regions:
        hits = [sec for sec in sections if inside(sec, page, bbox)]
        if not hits or len(hits) > rows + _EXTRA_SECTIONS:
            continue                     # more sections than rows: wording in a box
        if any(sec.kind in _KEEP_KINDS for sec in hits):
            continue                     # crosses a heading or an extracted table
        for sec in hits:
            if "possible_table" not in sec.metadata:
                sec.metadata["possible_table"] = reason
                n += 1
    if n:
        _log.info("Marked %d section(s) as possible tables", n)
    return n
