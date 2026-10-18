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


# A hanging label in a margin column: paragraph and section numbers, list
# marks, citation keys, code line numbers. Label + text is a list, not a table.
_HANGING_LABEL = re.compile(
    r"^(\(?\d+(\.\d+)*\)?\.?|[—–•◦▪o*\-]|\[[^\]]{1,40}\]|\(?[ivxlcIVXLC]+[.)]|\(?[a-zA-Z][.)])$")
_LEADER = re.compile(r"(\. ?){4,}")
_GUTTER_MIN = 8.0         # a whitespace gutter at least this wide (pt)...
_GUTTER_ROWS = 3         # ...with text on both sides in this many rows
_STOP = {"the", "a", "an", "of", "to", "and", "is", "in", "that", "for", "with", "be",
         "are", "this", "it", "on", "as", "by", "not", "or", "we", "can", "which"}


def _prose(text: str) -> bool:
    """A sentence: several words, many of them function words."""
    words = re.findall(r"[A-Za-z']+", text)
    return len(words) >= 6 and sum(w.lower() in _STOP for w in words) >= 0.2 * len(words)


def gutter_regions(blocks: list[Block]) -> list[Region]:
    """Tables found by their negative space: a vertical whitespace gutter.

    A table without rules still leaves an empty vertical strip between its
    columns that runs down consecutive lines, with text on both sides.
    Running text has none (it fills the measure and wraps), and neither do
    lists or headings. Each run of at least _GUTTER_ROWS lines with text on
    both sides of one gutter is a region, unless it is two-column prose
    (sentences on both sides), code with aligned comments, a contents page
    or title-page metadata.
    """
    out: list[Region] = []
    for page, rows in _rows(blocks).items():
        runs: list[dict] = []
        done: list[dict] = []
        for top, bot, segs in rows:
            segs = [g for g in segs if _ALNUM.search(g[2])]
            if not segs:
                continue
            gaps = [(a[1], b[0]) for a, b in zip(segs, segs[1:]) if b[0] - a[1] >= _COL_GAP]
            alive = []
            for run in runs:
                a, b = run["iv"]
                near = top - run["bot"] <= _ROW_SPACING * max(run["bot"] - run["top"], 1)
                crosses = any(g[0] < b - 1 and g[1] > a + 1 for g in segs)
                if not near or crosses:
                    done.append(run)
                    continue
                gap = next(((x, y) for x, y in gaps if x <= a + 1 and y >= b - 1 or
                            min(y, b) - max(x, a) >= _GUTTER_MIN), None)
                if gap:                       # text on both sides: narrow to the shared strip
                    run["iv"] = (max(a, gap[0]), min(b, gap[1]))
                    run["both"].append((top, bot, segs))
                run["bot"], run["top"] = bot, top
                alive.append(run)
            for gap in gaps:
                if not any(min(r["iv"][1], gap[1]) - max(r["iv"][0], gap[0]) >= _GUTTER_MIN
                           for r in alive):
                    alive.append({"iv": gap, "both": [(top, bot, segs)], "top": top, "bot": bot})
            runs = [r for r in alive if r["iv"][1] - r["iv"][0] >= _GUTTER_MIN]
        done += runs
        seen: set = set()
        for run in done:
            rws = run["both"]
            key = (rws[0][0], rws[-1][1]) if rws else None
            if len(rws) < _GUTTER_ROWS or key in seen:
                continue
            seen.add(key)
            a, b = run["iv"]
            left = [" ".join(g[2] for g in segs if g[1] <= a + 1) for _, _, segs in rws]
            right = [" ".join(g[2] for g in segs if g[0] >= b - 1) for _, _, segs in rws]
            if sum(_prose(l) and _prose(r) for l, r in zip(left, right)) >= 0.5 * len(rws):
                continue                      # two-column page layout
            if sum(r.lstrip().startswith(_COMMENT) for r in right) >= 0.5 * len(rws):
                continue                      # code with aligned comments
            if (sum(bool(_HANGING_LABEL.match(l.strip())) for l in left) >= 0.7 * len(rws)
                    and sum(len(r.split()) for r in right) >= 4 * len(rws)):
                continue                      # numbered paragraphs, citations: label + text
            if sum(bool(_LEADER.search(l + " " + r)) for l, r in zip(left, right)) >= 0.3 * len(rws):
                continue                      # contents with dot leaders
            if _is_not_table([(t, bt, sg) for t, bt, sg in rws], page):
                continue                      # contents, numbered code, front matter
            x0 = min(sg[0][0] for _, _, sg in rws)
            x1 = max(sg[-1][1] for _, _, sg in rws)
            out.append((page, (x0, rws[0][0], x1, rws[-1][1]),
                        f"a whitespace gutter runs down {len(rws)} lines with text on both sides",
                        len(rws)))
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


_OV_FILL = 0.85          # set apart: its rows fill at most this share of the prose width
_OV_SHARED = 0.6         # two-dimensional: this share of rows repeat 2+ piece positions
_OV_MONO = 0.5           # code (monospace) is not judged here


def _visual_rows(lines):
    rows: list = []
    for ln in sorted(lines, key=lambda l: ((l.bbox[1] + l.bbox[3]) / 2, l.bbox[0])):
        yc = (ln.bbox[1] + ln.bbox[3]) / 2
        if rows and abs(yc - rows[-1][0]) <= 3:
            rows[-1][1].append(ln)
        else:
            rows.append([yc, [ln]])
    return [r for _, r in rows]


def _pieces(row):
    spans = sorted((s for ln in row for s in ln.spans if s.text.strip()), key=lambda s: s.bbox[0])
    out: list = []
    for s in spans:
        if out and s.bbox[0] - out[-1][1] < _COL_GAP:
            out[-1][1] = max(out[-1][1], s.bbox[2])
            out[-1][2] += s.text
        else:
            out.append([s.bbox[0], s.bbox[2], s.text])
    return out


def outside_view_regions(sections: list[Section]) -> list[Region]:
    """Tables seen from the outside, against the paper's own prose: a block
    that is set apart (its rows fill much less than the prose measure) AND
    two-dimensional (most rows hold 2+ pieces whose positions recur on other
    rows). A block that is set apart but one-dimensional is a quote or a
    list; prose fills the measure. Measured on the tuning sets before use."""
    body = [ln for s in sections if s.kind == SectionKind.PARAGRAPH and len(s.lines) >= 2
            for ln in s.lines]
    if len(body) < 5:
        return []
    widths = sorted(ln.bbox[2] - ln.bbox[0] for ln in body)
    measure = widths[len(widths) // 2] or 1.0
    out: list[Region] = []
    for sec in sections:
        if sec.kind in _KEEP_KINDS or "possible_table" in sec.metadata or len(sec.lines) < 2:
            continue
        rows = _visual_rows(sec.lines)
        if len(rows) < 2:
            continue
        chars = sum(len(s.text) for ln in sec.lines for s in ln.spans)
        mono = sum(len(s.text) for ln in sec.lines for s in ln.spans if s.monospace)
        if chars and mono >= _OV_MONO * chars:
            continue
        pieces = [_pieces(r) for r in rows]
        starts = [[round(p[0]) for p in ps] for ps in pieces]
        segs = sorted(len(p) for p in pieces)[len(pieces) // 2]
        shared = sum(1 for i, a in enumerate(starts) if len(a) >= 2 and any(
            j != i and sum(1 for x in a for y in b if abs(x - y) <= _START_TOL) >= 2
            for j, b in enumerate(starts))) / len(rows)
        fill = sorted(max(l.bbox[2] for l in r) - min(l.bbox[0] for l in r) for r in rows)[len(rows) // 2] / measure
        page = sec.lines[0].page_num
        if page == 0 and sum(p[0][2].strip().endswith(":") for p in pieces if p) >= 0.5 * len(rows):
            continue                          # "Date: 2024-03-19" front matter
        if segs >= 2 and shared >= _OV_SHARED and fill <= _OV_FILL:
            same = [ln for ln in sec.lines if ln.page_num == page]
            out.append((page, (min(l.bbox[0] for l in same), min(l.bbox[1] for l in same),
                               max(l.bbox[2] for l in same), max(l.bbox[3] for l in same)),
                        "a block set apart from the prose and laid out in aligned columns",
                        len(rows)))
    return out
