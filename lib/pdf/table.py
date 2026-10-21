"""Table detection: the text-position detector, and selection across sources.

This module has two parts.

detect_tables() proposes tables from MuPDF text positions alone. It is one
of three independent table sources; the others are ruling lines (ruled.py)
and PDF accessibility tags (tagged.py). select_tables() compares all three
per region, picks one version, and sets its confidence (see the second half
of this file).

Text-position detection, two signals:
  Signal 1 (block structure): a block is columnar when it has 2+ lines whose
    x-starts have gaps > _COLUMN_GAP_THRESHOLD. Consecutive matching-column
    blocks form a table run.
  Signal 2 (geometric column profile): x positions that co-occur with other
    x positions in the same y-band across 2+ rows are confirmed table columns.
    Body text is always alone in its y-band and never qualifies.

Orphan absorption: single-line blocks whose x0 matches a confirmed column are
"orphans" - the first physical line of a wrapped table cell. They are absorbed
into the table run when the block following them is a confirmed table row
(one-block lookahead). Absorbed orphans are merged into the next row's first
cell so multi-line cells produce a single cell string.

Known gap: absorption is same-page only. A wrapped cell whose continuation
line is the first block on the next page is not absorbed - the table stops
at the last same-page row and the orphan appears in an uncertain region.
"""

import logging
import os
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher

from . import evidence
from .types import (Block, Line, Section, SectionKind, Confidence, Span, TableCandidate,
                    BULLET_CHARS)

_log = logging.getLogger(__name__)

_COLUMN_GAP_THRESHOLD = 50.0
_MIN_TABLE_ROWS = 2
_COLUMN_X_TOLERANCE = 10.0

_COLUMN_X_BUCKET = 5.0    # bucket size for x-position clustering
_Y_BAND_HEIGHT   = 15.0   # bucket size for y-position clustering
_MIN_SHARED_YBANDS = 2    # x must co-occur with other columns in 2+ y-bands


def _find_column_xs(blocks: list[Block]) -> frozenset[float]:
    """Return x-start positions that are genuine table columns.

    Uses the shared-y-band approach: an x position qualifies only when it
    co-occurs in the same y-band with at least one other distinct x position,
    across at least _MIN_SHARED_YBANDS such y-bands. Body text at the left
    margin is alone in every y-band and therefore never qualifies.

    Y-bands are scoped per page so that two lines on different pages at the
    same absolute y coordinate are not treated as sharing a row.
    """
    yband_to_xs: dict[tuple[int, int], set[int]] = defaultdict(set)
    for block in blocks:
        for line in block.lines:
            if not line.spans or not line.text.strip():
                continue
            x_key = round(line.bbox[0] / _COLUMN_X_BUCKET)
            y_key = round(((line.bbox[1] + line.bbox[3]) / 2.0) / _Y_BAND_HEIGHT)
            yband_to_xs[(block.page_num, y_key)].add(x_key)

    shared_counts: Counter[int] = Counter()
    for xs in yband_to_xs.values():
        if len(xs) >= 2:
            for x_key in xs:
                shared_counts[x_key] += 1

    return frozenset(
        x_key * _COLUMN_X_BUCKET
        for x_key, count in shared_counts.items()
        if count >= _MIN_SHARED_YBANDS
    )


def _is_column_aligned_orphan(block: Block, column_xs: frozenset[float]) -> bool:
    """True if block is a single-line block whose x0 aligns with a known column.

    Only single-line blocks qualify. Multi-line non-columnar blocks are genuine
    prose or captions and must not be absorbed into a table run.
    """
    if len(block.lines) != 1 or not block.lines[0].spans:
        return False
    x0 = block.lines[0].bbox[0]
    return any(abs(x0 - cx) <= _COLUMN_X_BUCKET for cx in column_xs)


def _block_column_positions(block: Block) -> list[float] | None:
    """Return the x-start positions of columns in a block, or None.

    A block is columnar if it has 2+ lines where every line after
    the first starts significantly to the right of the first line's
    x-start position.
    """
    if len(block.lines) < 2:
        return None

    x_starts = []
    for line in block.lines:
        if not line.spans:
            return None
        x_starts.append(line.bbox[0])

    for i in range(1, len(x_starts)):
        if x_starts[i] - x_starts[0] < _COLUMN_GAP_THRESHOLD:
            return None

    return x_starts


def _columns_match(cols_a: list[float], cols_b: list[float]) -> bool:
    """Check if two column position lists represent the same table structure."""
    if len(cols_a) != len(cols_b):
        return False
    return all(abs(a - b) < _COLUMN_X_TOLERANCE for a, b in zip(cols_a, cols_b))


def detect_tables(blocks: list[Block]) -> tuple[list[Section], list[Block]]:
    """Detect table regions from MuPDF block structure.

    Returns (table_sections, remaining_blocks).
    Table sections have kind=TABLE with high confidence.
    Remaining blocks are the non-table blocks for normal processing.
    """
    column_xs = _find_column_xs(blocks)  # geometric second signal

    table_sections: list[Section] = []
    remaining: list[Block] = []
    i = 0

    while i < len(blocks):
        cols = _block_column_positions(blocks[i])
        if cols is None:
            remaining.append(blocks[i])
            i += 1
            continue

        table_blocks = [blocks[i]]
        j = i + 1
        while j < len(blocks):
            next_cols = _block_column_positions(blocks[j])
            if next_cols is not None and _columns_match(cols, next_cols):
                table_blocks.append(blocks[j])
                j += 1
            elif (_is_column_aligned_orphan(blocks[j], column_xs)
                  and j + 1 < len(blocks)
                  and blocks[j].page_num == table_blocks[-1].page_num):
                # One-block lookahead: absorb only when the following block
                # confirms the table continues. The orphan must be on the same
                # page as the last table row to prevent cross-page false matches.
                # Putback is free - j stays here so the outer loop adds
                # blocks[j] to remaining if we break.
                peek_cols = _block_column_positions(blocks[j + 1])
                if (peek_cols is not None
                        and _columns_match(cols, peek_cols)
                        and blocks[j + 1].page_num == blocks[j].page_num):
                    table_blocks.append(blocks[j])
                    j += 1
                else:
                    break
            else:
                break

        if len(table_blocks) >= _MIN_TABLE_ROWS:
            num_cols = len(cols)
            rows: list[list[list]] = []
            all_lines = []

            for blk in table_blocks:
                row = []
                for line in blk.lines[:num_cols]:
                    row.append(list(line.spans))
                    all_lines.append(line)
                while len(row) < num_cols:
                    row.append([])
                for line in blk.lines[num_cols:]:
                    all_lines.append(line)
                    line_x = line.bbox[0]
                    best_col = min(
                        range(num_cols),
                        key=lambda ci: abs(line_x - cols[ci]),
                    )
                    row[best_col].extend(line.spans)
                rows.append(row)

            # Merge orphan partial rows (single populated first cell) into the
            # following row so wrapped cell text becomes one cell string.
            merged: list[list[list]] = []
            k = 0
            while k < len(rows):
                row = rows[k]
                if (k + 1 < len(rows)
                        and bool(row[0])
                        and all(not cell for cell in row[1:])
                        and bool(rows[k + 1][0])):
                    merged.append([row[0] + rows[k + 1][0]] + rows[k + 1][1:])
                    k += 2
                else:
                    merged.append(row)
                    k += 1
            rows = merged

            text = "\n".join(
                " | ".join(
                    "".join(s.text for s in cell).strip()
                    for cell in row
                )
                for row in rows
            )

            table_sections.append(Section(
                kind=SectionKind.TABLE,
                text=text,
                confidence=Confidence.HIGH,
                lines=all_lines,
                page_num=table_blocks[0].page_num,
                columns=rows,
            ))
            _log.debug("Table detected: %d rows x %d cols on page %d",
                        len(rows), num_cols, table_blocks[0].page_num)
            i = j
        else:
            remaining.append(blocks[i])
            i += 1

    return table_sections, remaining


# --------------------------------------------------------------------------
# Multi-source table selection
#
# Three independent extractors propose tables: PDF tags (tagged.py), ruling
# lines (ruled.py) and the text-position detector above. select_tables()
# groups their proposals by position, picks one version per region, and
# derives the confidence from agreement between sources plus rule checks.
# --------------------------------------------------------------------------

# When sources disagree the primary is chosen in this order. Tags are the
# author's own markup; a WG21 poll (poll.py) is an exact fixed pattern; a
# grid ruled in both directions is the next most
# direct evidence; horizontal-rule tables have ambiguous columns; text
# positions are the weakest signal. Tags from a structure tree that MuPDF
# reports as malformed rank just below the grid.
_SOURCE_PRIORITY = {"tags": 0, "poll": 1, "grid": 2, "tags-malformed": 3, "rules": 4, "codepair": 5, "tomd": 6,
                    "content": 7, "records": 8}


def _row_top(row) -> float | None:
    ys = [ln.bbox[1] for cell in row for ln in cell if ln.text.strip()]
    return min(ys) if ys else None


def _priority(c: TableCandidate) -> int:
    if c.source == "content" and "refines-rules" in c.flags:
        return _SOURCE_PRIORITY["rules"]
    if c.source == "tags" and "tags-malformed" in c.flags:
        return _SOURCE_PRIORITY["tags-malformed"]
    return _SOURCE_PRIORITY[c.source]
_GROUP_OVERLAP = 0.3       # vertical overlap (share of the smaller table)
_SAME_REGION = 0.5         # half of an alternative must lie within the primary
_CELL_AGREE = 0.85         # whitespace-free similarity for "same cell"
_STITCH_X_TOL = 6.0        # page-continued tables keep their x-extent
_REGION_MARGIN = 2.0

_TRAIL_OP_RE = re.compile(r"(&&|\|\||==|!=|>=|<=|::|[,(<\[{=]|\s[+\-*/])\s*$")
_LEAD_CONT_RE = re.compile(r"^\s*(&&|\|\||[)>\]},.;=]|::)")
_PAGE_NUM_CELL_RE = re.compile(r"^\d{1,4}$")
_WORD_RE = re.compile(r"\w+")
_REF_LABEL_RE = re.compile(r"(^|\S)\[[A-Z][A-Za-z0-9.+_'\u2019-]{1,29}\]$")    # [N2529], [P3847R1], [O'Dwyer2018]
_REF_LEAD_RE = re.compile(r"^\[[A-Z][A-Za-z0-9.+_'\u2019-]{1,29}\]\s+\S")  # "[P2831R0] Timur ..."
_SECTION_NUM_CELL_RE = re.compile(r"^(\d+(\.\d+)+\.?|[IVXLC]+\.)$")        # "9.1", "1.2.3", "IV."
_ASCII_ART_RE = re.compile(r"[+|]-{2,}|-{3,}[+|]")


def _key(s: str) -> str:
    return re.sub(r"\s+", "", s)


def _cells_agree(a: str, b: str) -> bool:
    ka, kb = _key(a), _key(b)
    if ka == kb:
        return True
    if not ka or not kb:
        return False
    return SequenceMatcher(None, ka, kb, autojunk=False).ratio() >= _CELL_AGREE


def candidates_agree(a: TableCandidate, b: TableCandidate) -> bool:
    """Same grid shape and every cell matching."""
    if a.shape != b.shape:
        return False
    ta, tb = a.text_rows(), b.text_rows()
    return all(_cells_agree(x, y)
               for ra, rb in zip(ta, tb) for x, y in zip(ra + [""] * (len(rb) - len(ra)),
                                                         rb + [""] * (len(ra) - len(rb))))


_DAMAGED_RANGE = (0x1D00, 0x1DBF)   # phonetic extensions: not WG21 text; seen as
                                   # math italics with the last hex digit dropped


_ALNUM = re.compile(r"[^\W_]", re.UNICODE)


def conservation_error(cand: TableCandidate, blocks: list[Block]) -> str:
    """Check that the text in the table's area went into its cells exactly once.

    The area is where the cells' own lines sit on each page. Every letter and
    digit of the page lines centred in that area must appear in the cells as
    often as on the page: a deficit is text the table lost (a dropped row,
    an overprinted word), a surplus is text it duplicated. Compared as
    character counts, so line breaks, hyphenation and spacing do not matter.
    Returns "" when conserved, else a note for the prompt.
    """
    area: dict[int, list[float]] = {}
    for row in cand.rows:
        for cell in row:
            for ln in cell:
                b = area.get(ln.page_num)
                area[ln.page_num] = (list(ln.bbox) if b is None else
                                     [min(b[0], ln.bbox[0]), min(b[1], ln.bbox[1]),
                                      max(b[2], ln.bbox[2]), max(b[3], ln.bbox[3])])
    if not area:
        return ""
    page_chars: Counter[str] = Counter()
    for blk in blocks:
        r = area.get(blk.page_num)
        if r is None:
            continue
        for ln in blk.lines:
            xc, yc = (ln.bbox[0] + ln.bbox[2]) / 2, (ln.bbox[1] + ln.bbox[3]) / 2
            if r[0] - 1 <= xc <= r[2] + 1 and r[1] - 1 <= yc <= r[3] + 1:
                page_chars.update(_ALNUM.findall(ln.text))
    if not page_chars:
        return ""                     # the area's lines are not in the block stream
    cell_chars = Counter(_ALNUM.findall(" ".join(" ".join(r) for r in cand.text_rows())))
    lost = sum((page_chars - cell_chars).values())
    extra = sum((cell_chars - page_chars).values())
    if lost or extra:
        return (f"Text conservation failed: {lost} characters on the page are not in "
                f"any cell and {extra} appear in cells more often than on the page.")
    if _aligned_neighbour_row(cand, blocks):
        return ("A row of text just above or below the table is split into the "
                "table's columns: it may be a header or row the table lost.")
    return ""


_NEIGHBOUR_PITCH = 1.6     # look this many row pitches above and below the table
_SEGMENT_GAP = 10.0        # spans further apart than this are separate cells


def _aligned_neighbour_row(cand: TableCandidate, blocks: list[Block]) -> bool:
    """A text row just outside the table whose pieces fall in 2+ of its columns.

    Both sources can lose the same row (a header drawn outside the tagged
    table, a row above the first rule), and then they agree on a wrong
    table. A caption is one piece; a lost row splits at the column gaps.
    """
    cols: dict[int, list[float]] = {}
    tops: list[float] = []
    for row in cand.rows:
        ys = [ln.bbox[1] for cell in row for ln in cell]
        if ys:
            tops.append(min(ys))
        for c, cell in enumerate(row):
            for ln in cell:
                b = cols.get(c)
                cols[c] = ([ln.bbox[0], ln.bbox[2]] if b is None else
                           [min(b[0], ln.bbox[0]), max(b[1], ln.bbox[2])])
    if len(cols) < 2 or len(tops) < 2 or len(cand.pages) != 1:
        return False
    page = cand.pages[0]
    tops.sort()
    pitch = sorted(b - a for a, b in zip(tops, tops[1:]))[(len(tops) - 1) // 2]
    x0 = min(v[0] for v in cols.values())
    x1 = max(v[1] for v in cols.values())
    y0 = min(ln.bbox[1] for r in cand.rows for cell in r for ln in cell)
    y1 = max(ln.bbox[3] for r in cand.rows for cell in r for ln in cell)
    bands = ((y0 - _NEIGHBOUR_PITCH * pitch, y0 - 0.5), (y1 + 0.5, y1 + _NEIGHBOUR_PITCH * pitch))
    for lo, hi in bands:
        spans = sorted((s for blk in blocks if blk.page_num == page for ln in blk.lines
                        for s in ln.spans if s.text.strip()
                        and lo <= (s.bbox[1] + s.bbox[3]) / 2 <= hi
                        and x0 - 2 <= (s.bbox[0] + s.bbox[2]) / 2 <= x1 + 2),
                       key=lambda s: s.bbox[0])
        segs: list[list[float]] = []
        for sp in spans:
            if segs and sp.bbox[0] - segs[-1][1] < _SEGMENT_GAP:
                segs[-1][1] = max(segs[-1][1], sp.bbox[2])
            else:
                segs.append([sp.bbox[0], sp.bbox[2]])
        if len(segs) < 2:
            continue
        hit = {c for a, b in segs for c, (ca, cb) in cols.items()
               if a < cb - 1 and b > ca + 1}
        if len(hit) >= 2 and all(any(a < cb - 1 and b > ca + 1 for ca, cb in cols.values())
                                 for a, b in segs):
            return True
    return False


def _damaged_text(cand: TableCandidate) -> str:
    """Characters showing that the PDF's own text layer is wrong."""
    bad = sorted({ch for row in cand.text_rows() for cell in row for ch in cell
                  if _DAMAGED_RANGE[0] <= ord(ch) <= _DAMAGED_RANGE[1]})
    return " ".join(bad[:6])


def partial_reading(primary: TableCandidate, other: TableCandidate) -> bool:
    """True when `other` is tomd's text-position reading of part of a fully
    ruled table: same columns, and every one of its rows matches, cell for
    cell, a row of the ruled table in the same order. The text-position
    detector often stops early or starts late on ruled tables; a correct
    subset confirms the rows it saw rather than contradicting the rest."""
    if other.source != "tomd" or primary.source not in ("grid", "rules"):
        return False
    if other.shape[1] != primary.shape[1] or other.shape[0] > primary.shape[0]:
        return False
    rows = primary.text_rows()
    i = 0
    seen = set()
    for orow in other.text_rows():
        while i < len(rows) and not all(_cells_agree(x, y) for x, y in zip(orow, rows[i])):
            i += 1
        if i == len(rows):
            return False
        seen.add(i)
        i += 1
    # The rows tomd did not see are unconfirmed: they must be the minority,
    # and none may look like another table's header (every cell bold) -
    # a ruled box around two tables passed as one (p4089r1).
    if len(seen) < _SUBSET_SHARE * len(rows):
        return False
    return not any(r > 0 and r not in seen and _all_bold(primary.rows[r])
                   for r in range(len(rows)))


_SUBSET_SHARE = 0.5


def _all_bold(row) -> bool:
    spans = [s for cell in row for ln in cell for s in ln.spans if s.text.strip()]
    return bool(spans) and all(s.bold for s in spans)


def table_flags(cand: TableCandidate) -> list[str]:
    """Rule-based sanity checks. Flags in BAD_TABLE_FLAGS mean the grid is
    probably wrong; the others are informational."""
    rows = cand.text_rows()
    flags: list[str] = []
    if not rows:
        return ["empty"]
    ncol = cand.shape[1]
    # The header row may legitimately have an empty corner cell.
    body = rows[1:] if len(rows) > 2 else rows
    # A column filled in under half the rows is a sparse annotation column
    # ("<- reconsider!", a mostly empty last column): legitimate, so it does
    # not count towards raggedness. Most columns sparse is a misread layout.
    fill = [sum(1 for r in body if j < len(r) and r[j]) / len(body) for j in range(ncol)]
    dense = [j for j in range(ncol) if fill[j] >= 0.5]
    if ncol >= 3 and len(dense) < ncol / 2:
        flags.append("sparse-columns")
    filled = [sum(1 for j in dense if j < len(r) and r[j]) for r in body]
    mode = Counter(filled).most_common(1)[0][0]
    # A misread layout shows rows that fill more of the dense columns than
    # usual (not in a grid ruled both ways, where lines fix the cells), rows
    # with an empty key cell (a wrapped line taken for a row), or a lone cell
    # in a wide table. Fewer filled cells is normal: "TLS | (none found) | ".
    keyed = sum(1 for r in body if r and r[0]) >= len(body) / 2
    extra = cand.source != "grid"
    ragged = sum(1 for r, f in zip(body, filled)
                 if (extra and f > mode) or (keyed and r and not r[0])
                 or (sum(1 for c in r if c) == 1 and ncol >= 3))
    if ragged / len(body) > 0.2:
        flags.append("ragged-columns")
    # Two rows with a gap: too little evidence for a grid (fragments of a
    # framed text box). Real two-row tables are full.
    if len(rows) == 2 and any(not c for r in rows for c in r + [""] * (ncol - len(r))):
        flags.append("sparse-two-rows")
    cells = [c for r in rows for c in r] + [""] * sum(ncol - len(r) for r in rows)
    if sum(1 for c in cells if not c) / max(1, len(cells)) > 0.4:
        flags.append("empty-cells")
    split = sum(1 for c in cells if c and (_TRAIL_OP_RE.search(c) or _LEAD_CONT_RE.search(c)
                                            or any(c.count(o) != c.count(k) for o, k in ("()", "[]", "{}"))))
    if split >= 2 or (cells and split / len(cells) >= 0.1):
        flags.append("split-code")
    # A (nearly) constant row-key column is a margin label beside code.
    if len(rows) >= 4:
        col0 = [r[0] for r in rows if r and r[0]]
        if col0 and Counter(col0).most_common(1)[0][1] >= 0.7 * len(rows):
            flags.append("constant-first-column")
    # Every row after the first fills a single cell: a framed paragraph or
    # code sample with a lead-in line ("POLL: ...", "Ranges-based overload:").
    if ncol >= 2 and len(body) >= 2 and rows is not body and all(f == 1 for f in filled):
        flags.append("single-cell-rows")
    # Look-alikes of tables that the text-position detector produces:
    last = [r[-1] for r in rows if r and r[-1]]
    first = [r[0] for r in rows if r and r[0]]
    if (ncol == 2 and len(rows) >= 2 and len(last) == len(rows)
            and all(_PAGE_NUM_CELL_RE.match(c) for c in last)):
        flags.append("toc-like")                    # "References | 5"
    elif (ncol >= 2 and len(rows) >= 3
            and sum(1 for c in last if _PAGE_NUM_CELL_RE.match(c)) >= 0.8 * len(rows)):
        # page numbers in a table of contents never go down; counts do
        nums = [int(c) for c in last if _PAGE_NUM_CELL_RE.match(c)]
        if all(a <= b for a, b in zip(nums, nums[1:])):
            flags.append("toc-like")
    if first and all(c.strip("\u200b ")[:1] in BULLET_CHARS for c in first):
        flags.append("bullet-list")                 # "● | item text", "• item | more"
    if (ncol == 2 and first and len(first) == len(rows)
            and all(_SECTION_NUM_CELL_RE.match(c) for c in first)) \
            or (rows[0] and _SECTION_NUM_CELL_RE.match(rows[0][0])):
        flags.append("numbered-list")               # "9.1 | feature test macro" (a header cell is never a section number)
    if sum(1 for c in cells if c and _ASCII_ART_RE.search(c)) >= 2:
        flags.append("ascii-art")                   # "+---+ +---+" box diagrams
    comment_cols = [j for j in range(ncol)
                    if [r[j] for r in rows if j < len(r) and r[j]]
                    and all(set(r[j].split()) == {"//"} for r in rows if j < len(r) and r[j])]
    if comment_cols:
        flags.append("code-comment-column")         # "using x = y; | // | exposition only"
    if len(last) >= 2 and all(c.startswith("//") for c in last):
        flags.append("code-comment-column")         # "Fun fun; | // exposition only"
    # (a label may arrive glued to the previous entry's URL: "...pdf[N2550]")
    if first and len(first) >= 0.5 * len(rows) and all(
            _REF_LABEL_RE.search(c) or _REF_LEAD_RE.match(c) for c in first):
        flags.append("reference-list")              # "[N2529] | Lambda Expressions..."
    return flags


BAD_TABLE_FLAGS = frozenset({"ragged-columns", "empty-cells", "split-code",
                             "constant-first-column", "toc-like", "bullet-list",
                             "code-comment-column", "reference-list",
                             "single-cell-rows", "sparse-two-rows", "numbered-list",
                             "ascii-art", "sparse-columns"})
# Tags are explicit markup: an empty column or an empty corner is the
# author's choice there, not an extraction error.
_TAG_EXEMPT_FLAGS = frozenset({"ragged-columns", "empty-cells"})
# a code pair's cells are whole code blocks by construction: code in cells is the point
_CODEPAIR_EXEMPT_FLAGS = frozenset({"split-code", "code-comment-column", "sparse-two-rows",
                                    "constant-first-column", "single-cell-rows"})


_MARK = re.compile(r"^(✔|✓|✗|✘|×|x|X|-|–|—|N/A|n/a|yes|no|Yes|No|Y|N|CE|\?|\*|●|○)$")
_SPARSE_FLAGS = frozenset({"empty-cells", "sparse-columns", "ragged-columns"})


def mark_matrix(cand: TableCandidate) -> bool:
    """A check-mark matrix (status, feature or compliance tables): row keys in
    the first column, and the filled cells beside them are marks. Sparse by
    design, so empty cells and sparse or ragged columns are not misreadings."""
    rows = cand.text_rows()
    if len(rows) < 2 or cand.shape[1] < 3:
        return False
    keyed = [r for r in rows[1:] if r and r[0].strip()]          # body rows: those with a row key
    body = [c.strip() for r in keyed for c in r[1:] if c.strip()]
    need = 1 if cand.shape[1] >= 5 else 3                         # a wide grid of marks: one row suffices
    return len(keyed) >= 1 and len(body) >= need and sum(bool(_MARK.match(c)) for c in body) >= 0.8 * len(body)


def _is_bad(cand: TableCandidate) -> bool:
    bad = set(cand.flags) & BAD_TABLE_FLAGS
    if bad & _SPARSE_FLAGS and (mark_matrix(cand)
                                or "rotated_header" in getattr(cand, "trace", {}).get("specialists", {})):
        bad -= _SPARSE_FLAGS          # sparse by design: marks, or a grid its rotated header labels define
    if cand.source == "tags":
        bad -= _TAG_EXEMPT_FLAGS
    if cand.source == "poll":
        bad -= {"empty-cells", "sparse-two-rows", "single-cell-rows", "ragged-columns"}   # a suggested poll's blank vote row
    if cand.source == "codepair" or (cand.source == "content" and getattr(cand, "trace", {}).get("code")):
        bad -= _CODEPAIR_EXEMPT_FLAGS
    return bool(bad)


def candidate_from_section(sec: Section) -> TableCandidate:
    """Wrap a detect_tables() section (cells are span lists) as a candidate."""
    rows = []
    for row in sec.columns:
        cells = []
        for spans in row:
            if spans:
                bbs = [s.bbox for s in spans]
                cells.append([Line(spans=list(spans), page_num=sec.page_num,
                                   bbox=(min(b[0] for b in bbs), min(b[1] for b in bbs),
                                         max(b[2] for b in bbs), max(b[3] for b in bbs)))])
            else:
                cells.append([])
        rows.append(cells)
    bboxes: dict[int, tuple] = {}
    for ln in sec.lines:
        b = bboxes.get(ln.page_num, ln.bbox)
        bboxes[ln.page_num] = (min(b[0], ln.bbox[0]), min(b[1], ln.bbox[1]),
                               max(b[2], ln.bbox[2]), max(b[3], ln.bbox[3]))
    return TableCandidate("tomd", rows, bboxes)


def _overlap(a: TableCandidate, b: TableCandidate) -> float:
    best = 0.0
    for pg in set(a.bboxes) & set(b.bboxes):
        x, y = a.bboxes[pg], b.bboxes[pg]
        if x[2] < y[0] or y[2] < x[0]:
            continue
        inter = min(x[3], y[3]) - max(x[1], y[1])
        smaller = min(x[3] - x[1], y[3] - y[1]) or 1.0
        best = max(best, inter / smaller)
    return best


def _text_outside(blocks: list[Block], page: int, below: float | None = None,
                  above: float | None = None, furniture: frozenset = frozenset()) -> bool:
    """True if any text line on the page lies below/above the given y
    (page furniture - running headers, page numbers - does not count)."""
    for blk in blocks:
        if blk.page_num != page:
            continue
        for ln in blk.lines:
            yc = (ln.bbox[1] + ln.bbox[3]) / 2
            if (below is not None and yc > below) or (above is not None and yc < above):
                if ln.text.strip() and _furniture_key(ln) not in furniture:
                    return True
    return False


_DIGITS = re.compile(r"\d+")


def _furniture_key(ln) -> tuple:
    return (round((ln.bbox[1] + ln.bbox[3]) / 2 / 4), _DIGITS.sub("#", " ".join(ln.text.split())))


def page_furniture(blocks: list[Block], min_pages: int = 3) -> frozenset:
    """Lines repeated at the same height on several pages once digits are
    normalised: running headers and footers with page numbers that header
    stripping missed (a header block holding the page number)."""
    by_page: dict = defaultdict(list)
    for blk in blocks:
        for ln in blk.lines:
            if ln.text.strip():
                by_page[blk.page_num].append(ln)
    pages: dict = defaultdict(set)
    for pg, lines in by_page.items():
        # furniture is the outermost text on the page: a repeated heading
        # further in (a slide title, "[P1371R3] examples") is not
        ys = sorted({round((ln.bbox[1] + ln.bbox[3]) / 2) for ln in lines})
        edge = set(ys[:2]) | set(ys[-2:])
        for ln in lines:
            if round((ln.bbox[1] + ln.bbox[3]) / 2) in edge:
                pages[_furniture_key(ln)].add(pg)
    # running headers and footers are on nearly every page; a heading that
    # recurs on a few pages is content
    need = max(min_pages, len(by_page) // 2)
    return frozenset(k for k, v in pages.items() if len(v) >= need)


def _same_region(primary: TableCandidate, other: TableCandidate) -> bool:
    """At least half of `other` lies within the primary's rows on a shared page.

    A partial reading of the table (tomd stopping early) still counts as
    another reading; a box drawn around the table, mostly outside it, does not.
    """
    for pg in set(primary.bboxes) & set(other.bboxes):
        x, y = primary.bboxes[pg], other.bboxes[pg]
        inter = min(x[3], y[3]) - max(x[1], y[1])
        if inter >= _SAME_REGION * max(y[3] - y[1], 1.0):
            return True
    return False


def stitch_pages(cands: list[TableCandidate], blocks: list[Block],
                 furniture: frozenset = frozenset()) -> list[TableCandidate]:
    """Join a table that ends one page with one that starts the next page.

    Requires the same column count and x-extent, and no text after the first
    part or before the second (headers and footers are already stripped from
    blocks) - a caption in between means two different tables. A header row
    that the PDF repeats on the continuation is dropped."""
    cands = sorted(cands, key=lambda c: (c.pages[0], c.bboxes[c.pages[0]][1]))
    out: list[TableCandidate] = []
    for c in cands:
        prev = out[-1] if out else None
        if prev is not None:
            last_pg = prev.pages[-1]
            first_on_pg = min((d for d in cands if d.pages[0] == c.pages[0]),
                              key=lambda d: d.bboxes[d.pages[0]][1])
            last_on_prev = max((d for d in out if d.pages[-1] == last_pg),
                               key=lambda d: d.bboxes[last_pg][3])
            pb, cb = prev.bboxes[last_pg], c.bboxes[c.pages[0]]
            if (c.pages[0] == last_pg + 1 and c is first_on_pg and prev is last_on_prev
                    and not _new_header(c, prev)
                    and prev.shape[1] == c.shape[1]
                    and ((abs(pb[0] - cb[0]) <= _STITCH_X_TOL and abs(pb[2] - cb[2]) <= _STITCH_X_TOL)
                         or _same_columns(prev, last_pg, c, c.pages[0])
                         or _continuation_votes(prev, last_pg, c, c.pages[0], blocks))
                    and not _text_outside(blocks, last_pg, below=pb[3] + _REGION_MARGIN, furniture=furniture)
                    and not _text_outside(blocks, c.pages[0], above=cb[1] - _REGION_MARGIN, furniture=furniture)):
                rows = list(c.rows)
                if _same_header(c.text_rows()[0], prev.text_rows()[0]):
                    rows = rows[1:]                  # the header the PDF repeats
                merged = False
                if rows and prev.rows and not "".join(ln.text for ln in rows[0][0]).strip() \
                        and any("".join(ln.text for ln in cell).strip() for cell in rows[0][1:]):
                    # a row split mid-cell by the page break: empty key, cells continuing
                    head = [list(a) + list(b) for a, b in zip(prev.rows[-1], rows[0])]
                    prev_rows = prev.rows[:-1] + [head]
                    rows = rows[1:]
                    merged = True
                else:
                    prev_rows = prev.rows
                joined = TableCandidate(prev.source, prev_rows + rows, {**prev.bboxes, **c.bboxes})
                joined.flags = list(prev.flags)
                # the pieces, so each can be verified on its own page and the join reversed
                pieces = list(getattr(prev, "pieces", None) or [(last_pg, 0, len(prev.rows))])
                pieces.append((c.pages[0], len(prev_rows), len(prev_rows) + len(rows)))
                joined.pieces = pieces
                evidence.current().feature(prev.source, c.pages[0], cb, "continues from previous page", "words",
                                           {"pages": joined.pages, "split_row_merged": merged})
                out[-1] = joined
                continue
        out.append(c)
    return out


def cross_reader_continuation(cands: list[TableCandidate], blocks: list[Block],
                              furniture: frozenset = frozenset()) -> list[TableCandidate]:
    """A table continuing across a page is the same table whichever reader read
    each piece (user: preserve meaningful spatial relationships regardless of
    mechanism). After every reader's own stitching, a piece ending low on page N
    joins a piece from a different reader starting high on page N+1 under the
    same conditions as same-reader stitching: the same column count and column
    starts (or extent), no different header, nothing between them (page
    furniture aside). Polls are never joined this way. The joined table keeps
    the first piece's reader, is flagged 'cross-reader' and records both."""
    # the tag tree states where a tagged table ends; never extend one with another reader's piece
    single = [c for c in cands if len(c.pages) >= 1 and c.source not in ("poll", "tags")]
    used: set = set()
    out_extra = []
    for a in single:
        if id(a) in used:
            continue
        pa = a.pages[-1]
        ab = a.bboxes[pa]
        top_a, bot_a = _page_span(blocks, pa)
        if ab[3] < bot_a - _EDGE * (bot_a - top_a):
            continue                              # does not end low on its page
        best = None
        for b in single:
            if b is a or b.source == a.source or id(b) in used or b.pages[0] != pa + 1:
                continue
            bb = b.bboxes[b.pages[0]]
            top_b, bot_b = _page_span(blocks, b.pages[0])
            if bb[1] > top_b + _EDGE * (bot_b - top_b):
                continue                          # does not start high on its page
            if a.shape[1] != b.shape[1] or _new_header(b, a):
                continue
            if not ((abs(ab[0] - bb[0]) <= _STITCH_X_TOL and abs(ab[2] - bb[2]) <= _STITCH_X_TOL)
                    or _same_columns(a, pa, b, b.pages[0])):
                continue
            if (_text_outside(blocks, pa, below=ab[3] + _REGION_MARGIN, furniture=furniture)
                    or _text_outside(blocks, b.pages[0], above=bb[1] - _REGION_MARGIN, furniture=furniture)):
                continue
            # the first piece on page N+1 and the last on page N, as in stitching
            if any(d is not b and d.pages[0] == b.pages[0] and d.bboxes[d.pages[0]][1] < bb[1] - 2
                   and _overlap(d, b) < _GROUP_OVERLAP for d in single):
                continue
            best = b
            break
        if best is None:
            continue
        rows = list(best.rows)
        if _same_header(best.text_rows()[0], a.text_rows()[0]):
            rows = rows[1:]
        joined = TableCandidate(a.source, list(a.rows) + rows, {**a.bboxes, **best.bboxes})
        joined.flags = list(a.flags) + ["cross-reader"]
        joined.pieces = list(getattr(a, "pieces", None) or [(pa, 0, len(a.rows))]) + \
            [(best.pages[0], len(a.rows), len(a.rows) + len(rows))]
        evidence.current().feature(a.source, best.pages[0], best.bboxes[best.pages[0]],
                                   "continues from previous page (another reader)", "words",
                                   {"readers": [a.source, best.source], "pages": joined.pages})
        used |= {id(a), id(best)}
        out_extra.append(joined)
    if not out_extra:
        return cands
    return [c for c in cands if id(c) not in used] + out_extra


_CONT = re.compile(r"\((cont(inued|\.|'d)?)\)|\bcontinued\b", re.I)


def _norm_header(row) -> list[str]:
    return [" ".join(_CONT.sub("", t).split()).lower() for t in row]


def _same_header(a, b) -> bool:
    """Identical header rows, after whitespace, case and "(cont.)"."""
    return _norm_header(a) == _norm_header(b)


def _bold_row(row) -> bool:
    cells = [cell for cell in row if any(ln.text.strip() for ln in cell)]
    return bool(cells) and all(all(sp.bold for ln in cell for sp in ln.spans if sp.text.strip()) for cell in cells)


def _is_header_row(cand: TableCandidate) -> bool:
    """The first row reads as a header: short bold labels over a body that
    is not bold (where every row is bold, bold says nothing)."""
    cells = [cell for cell in cand.rows[0] if any(ln.text.strip() for ln in cell)]
    texts = [" ".join(ln.text.strip() for ln in cell) for cell in cells]
    return (_bold_row(cand.rows[0]) and (len(cand.rows) < 2 or not _bold_row(cand.rows[1]))
            and all(len(t.split()) <= 6 and not re.search(r"[;{}()<>=]|::|&&", t) for t in texts))


def split_at_headers(cand: TableCandidate) -> list[TableCandidate]:
    """Two tables stacked in one reading: a different header row inside the body
    (short bold labels after a non-bold row) starts a new table (the user's
    header rule; an identical header repeated is the same table and stays).
    Single-page readings only; tags and polls delimit their own tables."""
    if len(cand.pages) != 1 or cand.source in ("tags", "poll") or len(cand.rows) < 4 or not _is_header_row(cand):
        return [cand]
    head = cand.text_rows()[0]
    text = cand.text_rows()
    cuts = []
    for i in range(2, len(cand.rows) - 1):
        probe = TableCandidate(cand.source, cand.rows[i:], {})
        if (_is_header_row(probe) and not _bold_row(cand.rows[i - 1])
                and not _same_header(text[i], head)):
            cuts.append(i)
    if not cuts:
        return [cand]
    # only a clean reading splits: a cell of absorbed prose (40+ words) means the
    # reading is wrong anyway, and splitting it would lose the region's flag
    if any(len(x.split()) >= 40 for r in text for x in r):
        return [cand]
    out = []
    pg = cand.pages[0]
    for a, b in zip([0] + cuts, cuts + [len(cand.rows)]):
        rows = cand.rows[a:b]
        lines = [ln for r in rows for c in r for ln in c]
        if not lines:
            continue
        box = (min(l.bbox[0] for l in lines), min(l.bbox[1] for l in lines),
               max(l.bbox[2] for l in lines), max(l.bbox[3] for l in lines))
        part = TableCandidate(cand.source, rows, {pg: box})
        part.flags = list(cand.flags) + ["split-at-header"]
        if hasattr(cand, "trace"):
            part.trace = cand.trace
        out.append(part)
    return out


def _new_header(c: TableCandidate, prev: TableCandidate) -> bool:
    """A different header row starts a new table (user, 2026-10-19)."""
    if _same_header(c.text_rows()[0], prev.text_rows()[0]):
        return False
    return _is_header_row(c) and _is_header_row(prev)


_SIGNATURE_TOL = 4.0       # column starts closer than this are the same column


def _column_starts_on(cand: TableCandidate, page: int) -> list[float | None]:
    out = []
    for c in range(cand.shape[1]):
        xs = [ln.bbox[0] for row in cand.rows if c < len(row) for ln in row[c] if ln.page_num == page]
        out.append(min(xs) if xs else None)
    return out


def _same_columns(a: TableCandidate, pa: int, b: TableCandidate, pb: int) -> bool:
    """The two parts start their columns at the same x positions (a page
    continuation keeps the page geometry; its outer edge may move with
    content). Every column seen on both pages must match, and at least two."""
    if os.environ.get("TOMD_STITCHSIG") == "0":
        return False
    sa, sb = _column_starts_on(a, pa), _column_starts_on(b, pb)
    pairs = [(x, y) for x, y in zip(sa, sb) if x is not None and y is not None]
    return len(pairs) >= 2 and all(abs(x - y) <= _SIGNATURE_TOL for x, y in pairs)


def _page_left(blocks: list[Block], page: int) -> float | None:
    """The page's text margin: where its body lines start (odd and even pages
    of a book layout differ)."""
    xs = sorted(ln.bbox[0] for b in blocks if b.page_num == page for ln in b.lines
                if ln.bbox[2] - ln.bbox[0] > 200)
    return xs[len(xs) // 10] if len(xs) >= 5 else None


def _continuation_votes(a: TableCandidate, pa: int, b: TableCandidate, pb: int, blocks: list[Block]) -> bool:
    """Level-0 continuation votes for a join whose only failure is position:
    footprint - both parts sit at the same inset from their own page's text
    margin (a page template shifts the whole page, not the table); word gaps -
    each column starts at the same offset from the table's left edge on both
    pages. Both must agree; stop signals (text between, a new header, a
    different column count) are checked before and still override."""
    if os.environ.get("TOMD_JOIN_VOTES") == "0":
        return False
    la, lb = _page_left(blocks, pa), _page_left(blocks, pb)
    if la is None or lb is None:
        return False
    ba, bb = a.bboxes[pa], b.bboxes[pb]
    footprint = abs((ba[0] - la) - (bb[0] - lb)) <= _STITCH_X_TOL
    sa, sb = _column_starts_on(a, pa), _column_starts_on(b, pb)
    pairs = [(x - ba[0], y - bb[0]) for x, y in zip(sa, sb) if x is not None and y is not None]
    columns = len(pairs) >= 2 and all(abs(x - y) <= _SIGNATURE_TOL for x, y in pairs)
    if footprint and columns:
        from . import evidence
        evidence.current().feature(a.source, pb, bb, "continuation votes: footprint and column starts", "words", 1.0)
    return footprint and columns


def _cell_spans(cell: list[Line]) -> list[Span]:
    """A cell's spans, with a "\\n" span between wrapped lines."""
    out: list[Span] = []
    for i, ln in enumerate(cell):
        if i:
            out.append(Span(text="\n"))
        out.extend(ln.spans)
    return out


def _as_markdown_rows(cand: TableCandidate) -> str:
    rows = cand.text_rows()
    width = cand.shape[1]
    lines = []
    for i, r in enumerate(rows):
        cells = [c.replace("|", "\\|") for c in r] + [""] * (width - len(r))
        lines.append("| " + " | ".join(cells) + " |")
        if i == 0:
            lines.append("| " + " | ".join(["---"] * width) + " |")
    return "\n".join(lines)


def _to_section(cand: TableCandidate, confidence: Confidence,
                alternatives: list[TableCandidate]) -> Section:
    all_lines = sorted((ln for row in cand.rows for cell in row for ln in cell),
                       key=lambda ln: (ln.page_num, ln.bbox[1], ln.bbox[0]))
    first_pg = cand.pages[0]
    sec = Section(
        kind=SectionKind.TABLE,
        text="\n".join(" | ".join(r) for r in cand.text_rows()),
        confidence=confidence,
        lines=all_lines,
        page_num=first_pg,
        columns=[[_cell_spans(cell) for cell in row] for row in cand.rows],
    )
    sec.metadata["table_source"] = cand.source
    if "extent:header-below" in cand.flags:
        # the header row was found under its columns on the page (extent.py)
        sec.metadata["header_below"] = True
    if confidence == Confidence.UNCERTAIN:
        sec.mupdf_text = _as_markdown_rows(cand)
        sec.spatial_text = "\n\n".join(
            f"({alt.source} extractor)\n{_as_markdown_rows(alt)}" for alt in alternatives)
        sec.metadata["table_versions"] = (
            [(cand.source, _as_markdown_rows(cand))]
            + [(alt.source, _as_markdown_rows(alt)) for alt in alternatives])
    return sec


def select_tables(tomd_sections: list[Section],
                  ruled: list[TableCandidate],
                  tagged: list[TableCandidate],
                  blocks: list[Block],
                  polls: list[TableCandidate] = (),
                  rejected: list[TableCandidate] | None = None,
                  codepairs: list[TableCandidate] = (),
                  content: list[TableCandidate] = ()) -> list[Section]:
    """Choose one table per region from the three extractors.

    Primary version by source priority (tags, polls, ruling lines, text positions),
    skipping versions that fail the rule checks. Confidence:
      - another source agrees cell for cell, or tomd's
        reading is a correct subset of a ruled table -> HIGH
      - only one source found the table            -> UNCERTAIN
      - other sources found it but disagree        -> UNCERTAIN, and every
        version is kept for the prompts file
      - the cells lose or duplicate text of the
        table's area (conservation_error)          -> UNCERTAIN
    A candidate that fails the rule checks and has no better version is
    dropped, so its blocks flow back into normal processing. Dropped
    candidates from the drawing and tag sources are appended to `rejected`
    when given: their area probably is a table, so flag.py marks it.
    """
    tomd = [candidate_from_section(s) for s in tomd_sections]
    # Continuation fragments (the last rows of a table on the next page) only
    # count once stitched onto the table they continue.
    # one continuation step for every reader that reads page by page
    furniture = page_furniture(blocks)
    ruled = [c for c in stitch_pages(ruled, blocks, furniture) if "continuation-fragment" not in c.flags]
    if os.environ.get("TOMD_STITCH_ALL") != "0":
        codepairs = stitch_pages(list(codepairs), blocks, furniture) if codepairs else []
        content = stitch_pages(list(content), blocks, furniture) if content else []
    cands = tagged + list(polls) + ruled + list(codepairs) + tomd + list(content)
    if os.environ.get("TOMD_CROSS_READER") != "0":
        cands = cross_reader_continuation(cands, blocks, furniture)
    if os.environ.get("TOMD_HEADER_SPLIT") != "0":
        cands = [part for c in cands for part in split_at_headers(c)]
    rec = evidence.current()
    for c in cands:
        c.flags = c.flags + table_flags(c)
        for pg, bb in c.bboxes.items():
            rec.nominate(c.source, pg, bb, "candidate " + "x".join(map(str, c.shape)), _INFO_TYPE.get(c.source, "words"))
        if len(c.bboxes) == 1:
            rec.readings.append((c.source, c.pages[0], c.bboxes[c.pages[0]], c.text_rows()))

    # A code pair inside a drawn table that is clearly larger is a fragment of
    # that table, not a comparison of its own: the table's cells are its extent.
    drawn = [c for c in cands if c.source in ("rules", "grid") and len(c.bboxes) == 1]
    for c in [c for c in cands if c.source == "codepair"]:
        pg, bb = c.pages[0], c.bboxes[c.pages[0]]
        for d in drawn:
            db = d.bboxes.get(pg)
            if (db and db[0] - 2 <= bb[0] and db[1] - 2 <= bb[1] and bb[2] <= db[2] + 2 and bb[3] <= db[3] + 2
                    and (db[2] - db[0]) * (db[3] - db[1]) >= 1.5 * (bb[2] - bb[0]) * (bb[3] - bb[1])):
                rec.exclude("codepair", pg, bb, "fragment of a drawn table", "paths")
                cands = [x for x in cands if x is not c]
                break
    # Rows inside a code pair come from the shared row builder (separators,
    # row gaps): when the content reading of the pair's region keeps its two
    # columns and finds more rows, the pair defers to it.
    for c in [c for c in cands if c.source == "codepair"]:
        pg, bb = c.pages[0], c.bboxes[c.pages[0]]
        for k in [k for k in cands if k.source == "content" and k.pages == [pg]]:
            kb = k.bboxes[pg]
            if (abs(kb[0] - bb[0]) <= 8 and abs(kb[2] - bb[2]) <= 8 and min(kb[3], bb[3]) - max(kb[1], bb[1]) > 0
                    and k.shape[1] == c.shape[1] and k.shape[0] > c.shape[0] and not _is_bad(k)
                    and sum(all(cell for cell in r) for r in k.text_rows()) >= 0.6 * k.shape[0]):
                rec.feature("codepair", pg, bb, "rows from the shared builder", "words", k.shape[0])
                k.flags = k.flags + ["code-rows"]
                cands = [x for x in cands if x is not c]
                break
    # Rows come from content and drawn rules confirm them: a content reading
    # of a rule reader's region that keeps every drawn row boundary and finds
    # more rows inside the bands (several records per band) refines the rule
    # reading, and takes its place (and its priority).
    if os.environ.get("TOMD_CONTENT_REFINES") != "0":
        for c in [c for c in cands if c.source == "rules" and len(c.pages) == 1]:
            pg, bb = c.pages[0], c.bboxes[c.pages[0]]
            tops_r = [_row_top(r) for r in c.rows[1:]]
            for k in [k for k in cands if k.source == "content" and k.pages == [pg]]:
                kb = k.bboxes[pg]
                if not (abs(kb[0] - bb[0]) <= 8 and abs(kb[2] - bb[2]) <= 8 and min(kb[3], bb[3]) > max(kb[1], bb[1])):
                    continue
                if k.shape[1] != c.shape[1] or k.shape[0] < c.shape[0] + 2 or _is_bad(k):
                    continue
                tops_k = [_row_top(r) for r in k.rows]
                # the extra rows (not at a drawn boundary) must be records with
                # a short key, not wrapped sentences continuing the row above
                extra = [r for r, t in zip(k.rows[1:], tops_k[1:])
                         if t is not None and not any(u is not None and abs(u - t) <= 3 for u in tops_r)]
                keys = [" ".join(ln.text.strip() for ln in r[0]).strip() if r else "" for r in extra]
                # an empty key is a record too when two or more other cells start items
                # (the line-alignment rule: "| graph_reference_t<G> | g | Graph reference")
                filled = [sum(any(ln.text.strip() for ln in cell) for cell in r[1:]) for r in extra]
                records = all((kk and len(kk.split()) <= 6 and not kk[0].islower() and not kk.startswith(('"', "“")))
                              or (not kk and n >= 2) for kk, n in zip(keys, filled))
                if records and all(t is None or any(u is not None and abs(u - t) <= 3 for u in tops_k) for t in tops_r):
                    rec.feature("rules", pg, bb, "content rows refine the rule bands", "words", k.shape[0])
                    k.flags = k.flags + ["refines-rules"]
                    cands = [x for x in cands if x is not c]
                    break
    # Two or more runs of records (records.py) inside one reading's region that
    # together hold its text: the region is several stacked tables read as one.
    # The records readings take its place (single source: flagged). Tags and
    # polls delimit their own tables and are never split.
    if os.environ.get("TOMD_RECORDS_SPLIT") != "0":
        splits = [k for k in cands if k.source == "records" and "records-split" in k.flags]
        for c in [c for c in cands if c.source not in ("records", "tags", "poll") and len(c.pages) == 1]:
            pg = c.pages[0]
            inside = [k for k in splits if k.pages == [pg] and _same_region(c, k)]
            # stacked tables: each run has its own header, and they share a column count
            if (len(inside) < 2 or not all("records-headed" in k.flags for k in inside)
                    or len({k.shape[1] for k in inside}) != 1):
                continue
            have = Counter(w for r in c.text_rows() for x in r for w in x.split())
            got = Counter(w for k in inside for r in k.text_rows() for x in r for w in x.split())
            if sum((have & got).values()) >= 0.9 * max(sum(have.values()), 1):
                rec.feature("records", pg, c.bboxes[pg], "region holds several runs of records", "meaning", len(inside))
                cands = [x for x in cands if x is not c]
    # A poll whose vote row was inferred (blank) yields to another reading of
    # the same region that has the votes under the same header.
    for c in [c for c in cands if c.source == "poll" and "blank-row-inferred" in c.flags]:
        head = [_key(t) for t in c.text_rows()[0]]
        for o in cands:
            if o is c or o.source == "poll" or not (set(o.pages) & set(c.pages)) or _overlap(o, c) < _GROUP_OVERLAP:
                continue
            rows = o.text_rows()
            for i, r in enumerate(rows[:-1]):
                if [_key(t) for t in r] == head and all(_VOTE.match(x.strip()) for x in rows[i + 1] if x.strip()) \
                        and any(x.strip() for x in rows[i + 1]):
                    rec.feature("poll", c.pages[0], c.bboxes[c.pages[0]], "votes read by another reader", "words", o.source)
                    cands = [x for x in cands if x is not c]
                    break
            if c not in cands:
                break
    # Greedy selection: take the best remaining candidate, settle everything
    # that overlaps it, repeat. (Grouping by overlap first would chain
    # separate tables together through one large box that overlaps them all.)
    remaining = sorted(cands, key=_priority)
    out: list[Section] = []
    while True:
        # a records reading of code is an alternative only, never the emitted reading
        good = [c for c in remaining if not _is_bad(c) and not (c.source == "records" and "records-code" in c.flags)]
        if not good:
            break
        primary = good[0]
        settled = [c for c in remaining
                   if c is primary or _overlap(c, primary) >= _GROUP_OVERLAP]
        # Alternatives are other sources' readings of the same region: they
        # must pass the rule checks and lie mostly within the primary. A box
        # drawn around a poll is not another reading of the poll.
        others = [c for c in settled if c is not primary and c.source != primary.source
                  and not _is_bad(c) and _same_region(primary, c)]
        # a code pair is a witness when it agrees, not another reading to doubt by
        others = [c for c in others if c.source not in ("codepair", "content", "records")
                  or candidates_agree(primary, c) or partial_reading(primary, c)]
        content_read = [c for c in settled if c.source == "content" and c is not primary
                        and not _is_bad(c) and _same_region(primary, c)]
        content_disagrees = bool(content_read) and not any(
            candidates_agree(primary, c) or partial_reading(primary, c) for c in content_read)
        # HIGH only when an independent source produced the same table.
        # A single source, however plausible, is UNCERTAIN: measured on fresh
        # papers, single-source tables carry most silent errors.
        notes = []
        # (a tomd reading that is an exact subset of a ruled table counts:
        # the ruled table's extra rows are the part tomd could not see)
        # a code pair reads its cell text from the same text layer as every
        # other reader: its agreement is a witness for the record, not for HIGH
        voters = ([] if primary.source in ("codepair", "content", "records")
                  else [o for o in others if o.source not in ("codepair", "content", "records")])
        exact = any(candidates_agree(primary, o) for o in voters)
        agree = exact or any(partial_reading(primary, o) for o in voters)
        conf = Confidence.HIGH if agree else Confidence.UNCERTAIN
        reasons = []                     # why it is UNCERTAIN; the gate reads these
        if not agree:
            reasons.append("single-source" if not voters else "disagree")
            notes.append("Only one table source produced this table." if not voters else
                         "The table sources disagree; every version is below.")
        if (not agree and primary.source == "codepair" and "labelled" in primary.flags
                and os.environ.get("TOMD_CODEPAIR_HIGH") == "1"):
            agree = True                 # geometry and shared code: two witnesses (measured variant)
            conf = Confidence.HIGH
            reasons.clear()
            notes.clear()
        if "cross-reader" in primary.flags:
            # joined from two readers' pieces: no single reading backs the whole table
            conf = Confidence.UNCERTAIN
            reasons.append("cross-reader")
            notes.append("This table was joined across a page break from two different readers' pieces.")
        lost = conservation_error(primary, blocks)
        if lost:
            conf = Confidence.UNCERTAIN
            reasons.append("conservation")
            notes.append(lost)
        damaged = _damaged_text(primary)
        if damaged:
            conf = Confidence.UNCERTAIN
            reasons.append("damaged")
            notes.append(
                "The PDF's text layer is damaged in this table (characters such as "
                f"{damaged} are wrong in the file itself, e.g. math italics written "
                "without their last hex digit). Read the symbols from the page image.")
        sec = _to_section(primary, conf, others)
        if notes:
            sec.metadata["table_note"] = " ".join(notes)
        sec.metadata["table_agreement"] = "exact" if exact else "subset" if agree else "none"
        agreeing = [primary] + [o for o in others
                                if candidates_agree(primary, o) or partial_reading(primary, o)]
        w = sec.metadata["witness"] = witness(primary, agreeing, cands, blocks)
        if (w["extent"] == "open" and not w["tree_extent"] and class_check(primary) != "poll"
                and os.environ.get("TOMD_EXTENT") != "0"):
            # no source measured where this table ends: page-local readers
            # agreeing on a page piece is the page grid seen twice
            sec.confidence = Confidence.UNCERTAIN
            reasons.append("extent")
            sec.metadata["table_note"] = (sec.metadata.get("table_note", "") + " A table with the same "
                                          "columns continues on the adjacent page; this may be one part "
                                          "of it.").strip()
        sec.metadata["uncertain_reasons"] = reasons
        if content_disagrees:
            # the shared builder read this region differently: flag, don't pick silently
            sec.metadata["content_disagrees"] = True
            sec.metadata["table_note"] = (sec.metadata.get("table_note", "") + " The content-first reading of "
                                          "this region (rows from baselines and gaps, columns from gutters) "
                                          "differs from this one.").strip()
        sec.metadata["class_check"] = class_check(primary)
        # what the classifier sees: every source and rule flag in this region
        sec.metadata["region_sources"] = sorted({c.source for c in settled})
        sec.metadata["region_flags"] = sorted({f for c in settled for f in c.flags})
        sec.metadata["region_bbox"] = (primary.pages[0], primary.bboxes[primary.pages[0]])
        if mark_matrix(primary) or "rotated_header" in getattr(primary, "trace", {}).get("specialists", {}):
            sec.metadata["sparse_by_design"] = True     # empty cells are data: no span filling
        if len(primary.pages) > 1:
            sec.metadata["page_bboxes"] = dict(primary.bboxes)
            if getattr(primary, "pieces", None):
                sec.metadata["pieces"] = primary.pieces
        # every other source's reading of this region (rejected ones too):
        # escalation may switch to one when the primary fails verification
        sec.metadata["alternatives"] = [
            (c.source, [[_cell_spans(cell) for cell in row] for row in c.rows])
            for c in settled if c is not primary and c.source != primary.source
            and c.pages == primary.pages]
        out.append(sec)
        _log.debug("Table p%d %dx%d from %s: %s", primary.pages[0], *primary.shape,
                   primary.source, conf.value)
        remaining = [c for c in remaining if not any(c is x for x in settled)]
    for c in remaining:
        _log.debug("Dropping %s table candidate on page %d: %s", c.source, c.pages[0], c.flags)
        for pg, bb in c.bboxes.items():
            rec.exclude(c.source, pg, bb, "dropped: " + (", ".join(f for f in c.flags if f in BAD_TABLE_FLAGS)
                                                        or "outranked"), _INFO_TYPE.get(c.source, "words"))
        if rejected is not None and c.source not in ("content", "records"):
            rejected.append(c)
    return out


# What each source actually measures, per property (stage 0: independence is
# different underlying information, not different code). rows / cols: where
# the boundaries are; members: which words go in which cell; extent: where
# the table starts and ends.
_INFO = {
    "tomd": {"rows": "words", "cols": "words", "members": "words"},
    "rules": {"rows": "paths", "cols": "words", "members": "words"},
    "grid": {"rows": "paths", "cols": "paths", "members": "words"},
    "tags": {"rows": "tree", "cols": "tree", "members": "tree"},
    "poll": {"rows": "words", "cols": "pattern", "members": "words"},
    "codepair": {"rows": "words", "cols": "words", "members": "words"},
    "records": {"rows": "meaning", "cols": "meaning", "members": "words"},
}
# the information type a source's region decision rests on (evidence record)
_INFO_TYPE = {"tomd": "words", "rules": "paths", "grid": "paths", "tags": "tree", "poll": "meaning",
              "codepair": "words", "content": "words", "records": "meaning"}
_EDGE = 0.25               # a table ending in the last quarter of the page text may continue


def _page_span(blocks: list[Block], page: int) -> tuple[float, float]:
    ys = [y for b in blocks if b.page_num == page for ln in b.lines for y in (ln.bbox[1], ln.bbox[3])]
    return (min(ys), max(ys)) if ys else (0.0, 1.0)


def _extent_open(primary: TableCandidate, cands: list[TableCandidate], blocks: list[Block]) -> bool:
    """A table with the same columns on the adjacent page, where this one ends
    low (or starts high) and that one starts high (or ends low), was not
    stitched to it: the page break cut the table and no source measured its
    end. Agreement on a page piece is then the page grid seen twice."""
    last, first = primary.pages[-1], primary.pages[0]
    for c in cands:
        if c is primary or c.shape[1] != primary.shape[1]:
            continue
        if c.pages[0] == last + 1:
            top, bot = _page_span(blocks, last)
            ntop, nbot = _page_span(blocks, c.pages[0])
            if (primary.bboxes[last][3] >= bot - _EDGE * (bot - top)
                    and c.bboxes[c.pages[0]][1] <= ntop + _EDGE * (nbot - ntop)
                    and _same_columns(primary, last, c, c.pages[0])):
                return True
        if c.pages[-1] == first - 1:
            top, bot = _page_span(blocks, first)
            ptop, pbot = _page_span(blocks, c.pages[-1])
            if (primary.bboxes[first][1] <= top + _EDGE * (bot - top)
                    and c.bboxes[c.pages[-1]][3] >= pbot - _EDGE * (pbot - ptop)
                    and _same_columns(c, c.pages[-1], primary, first)):
                return True
    return False


def witness(primary: TableCandidate, agreeing: list[TableCandidate],
            cands: list[TableCandidate], blocks: list[Block]) -> dict:
    """Per property, the distinct information sources behind the agreeing readings."""
    props = {p: sorted({_INFO.get(c.source, {}).get(p, c.source) for c in agreeing})
             for p in ("rows", "cols", "members")}
    # a well-formed structure tree delimits its Table elements, across pages too
    tree = any(c.source == "tags" and "tags-malformed" not in c.flags for c in agreeing)
    return {"agree": sorted({c.source for c in agreeing}), "props": props,
            "extent": "open" if _extent_open(primary, cands, blocks) else "closed",
            "tree_extent": tree}


_VOTE = re.compile(r"^\d{1,3}$")


def class_check(cand: TableCandidate) -> str:
    """Why this table can be trusted from one source, or "".

    Each check is specific to how the table was built, and only used when
    the classifier puts the region in the matching layout class:
      - poll: exactly the SF F N A SA (or F N A) header, then rows that are
        all vote counts, or one all-empty row (a suggested poll);
      - grid: read from drawn cell boundaries, rectangular, no column or
        row left empty;
      - tags: from a well-formed structure tree, every row as wide as the
        table, no empty column.
    """
    rows = cand.text_rows()
    if not rows or _is_bad(cand):
        return ""
    width = max(len(r) for r in rows)
    if any(len(r) != width for r in rows):
        return ""
    if cand.source == "poll":
        from .poll import vote_header
        if "blank-row-inferred" in cand.flags:
            return ""                     # the blank row was added by convention, not read
        if vote_header(rows[0]) and len(rows) >= 2 and all(
                all(_VOTE.match(c.strip()) for c in r) or not any(c.strip() for c in r)
                for r in rows[1:]):
            return "poll"
        return ""
    empty_col = any(not any(r[c].strip() for r in rows) for c in range(width))
    empty_row = any(not any(c.strip() for c in r) for r in rows)
    if cand.source == "grid" and not empty_col and not empty_row:
        return "grid"
    if cand.source == "tags" and not empty_col:
        return "tagged"
    return ""


def remove_table_regions(blocks: list[Block], tables: list[Section]) -> list[Block]:
    """Drop the lines that fall inside any chosen table's region.

    A line inside the region whose text is not in the table is kept, so it
    stays in the document as ordinary text: never lose words to a table whose
    cells missed them.
    """
    table_words = set(_WORD_RE.findall(" ".join(sec.text for sec in tables)))

    def captured(ln: Line) -> bool:
        words = _WORD_RE.findall(ln.text)
        return not words or sum(w in table_words for w in words) >= 0.5 * len(words)

    regions: dict[int, list[tuple]] = {}
    for sec in tables:
        per_page: dict[int, list] = {}
        for ln in sec.lines:
            per_page.setdefault(ln.page_num, []).append(ln.bbox)
        for pg, bbs in per_page.items():
            regions.setdefault(pg, []).append(
                (min(b[0] for b in bbs) - _REGION_MARGIN, min(b[1] for b in bbs) - _REGION_MARGIN,
                 max(b[2] for b in bbs) + _REGION_MARGIN, max(b[3] for b in bbs) + _REGION_MARGIN))
    if not regions:
        return blocks
    out = []
    for blk in blocks:
        rs = regions.get(blk.page_num)
        if not rs:
            out.append(blk)
            continue
        keep = [ln for ln in blk.lines
                if not any(r[0] <= (ln.bbox[0] + ln.bbox[2]) / 2 <= r[2]
                           and r[1] <= (ln.bbox[1] + ln.bbox[3]) / 2 <= r[3] for r in rs)
                or not captured(ln)]
        if len(keep) == len(blk.lines):
            out.append(blk)
        elif keep:
            out.append(Block(lines=keep, page_num=blk.page_num,
                             bbox=(min(l.bbox[0] for l in keep), min(l.bbox[1] for l in keep),
                                   max(l.bbox[2] for l in keep), max(l.bbox[3] for l in keep))))
    return out
