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
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher

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
# author's own markup; a grid ruled in both directions is the next most
# direct evidence; horizontal-rule tables have ambiguous columns; text
# positions are the weakest signal. Tags from a structure tree that MuPDF
# reports as malformed rank just below the grid.
_SOURCE_PRIORITY = {"tags": 0, "grid": 1, "tags-malformed": 2, "rules": 3, "tomd": 4}


def _priority(c: TableCandidate) -> int:
    if c.source == "tags" and "tags-malformed" in c.flags:
        return _SOURCE_PRIORITY["tags-malformed"]
    return _SOURCE_PRIORITY[c.source]
_GROUP_OVERLAP = 0.3       # vertical overlap (share of the smaller table)
_CELL_AGREE = 0.85         # whitespace-free similarity for "same cell"
_STITCH_X_TOL = 6.0        # page-continued tables keep their x-extent
_REGION_MARGIN = 2.0

_TRAIL_OP_RE = re.compile(r"(&&|\|\||==|!=|>=|<=|::|[,(<\[{=]|\s[+\-*/])\s*$")
_LEAD_CONT_RE = re.compile(r"^\s*(&&|\|\||[)>\]},.;]|::)")
_PAGE_NUM_CELL_RE = re.compile(r"^\d{1,4}$")
_REF_LABEL_RE = re.compile(r"(^|\S)\[[A-Z][A-Za-z0-9.+_-]{1,29}\]$")    # [N2529], [P3847R1], [Smith20]


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
    filled = [sum(1 for c in r if c) for r in body]
    mode = Counter(filled).most_common(1)[0][0]
    ragged = sum(1 for f in filled if f != mode)
    if ragged / len(body) > 0.2:
        flags.append("ragged-columns")
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
        flags.append("toc-like")
    if first and all(c.strip() in BULLET_CHARS or c.strip("\u200b ") in BULLET_CHARS
                     for c in first):
        flags.append("bullet-list")                 # "● | item text"
    if last and len(last) >= 0.8 * len(rows) and all(c.startswith("//") for c in last):
        flags.append("code-comment-column")         # "Fun fun; | // exposition only"
    # (a label may arrive glued to the previous entry's URL: "...pdf[N2550]")
    if first and len(first) >= 0.5 * len(rows) and all(_REF_LABEL_RE.search(c) for c in first):
        flags.append("reference-list")              # "[N2529] | Lambda Expressions..."
    return flags


BAD_TABLE_FLAGS = frozenset({"ragged-columns", "empty-cells", "split-code",
                             "constant-first-column", "toc-like", "bullet-list",
                             "code-comment-column", "reference-list",
                             "single-cell-rows"})
# Tags are explicit markup: an empty column or an empty corner is the
# author's choice there, not an extraction error.
_TAG_EXEMPT_FLAGS = frozenset({"ragged-columns", "empty-cells"})


def _is_bad(cand: TableCandidate) -> bool:
    bad = set(cand.flags) & BAD_TABLE_FLAGS
    if cand.source == "tags":
        bad -= _TAG_EXEMPT_FLAGS
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
                  above: float | None = None) -> bool:
    """True if any text line on the page lies below/above the given y."""
    for blk in blocks:
        if blk.page_num != page:
            continue
        for ln in blk.lines:
            yc = (ln.bbox[1] + ln.bbox[3]) / 2
            if (below is not None and yc > below) or (above is not None and yc < above):
                if ln.text.strip():
                    return True
    return False


def stitch_pages(cands: list[TableCandidate], blocks: list[Block]) -> list[TableCandidate]:
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
                    and prev.shape[1] == c.shape[1]
                    and abs(pb[0] - cb[0]) <= _STITCH_X_TOL and abs(pb[2] - cb[2]) <= _STITCH_X_TOL
                    and not _text_outside(blocks, last_pg, below=pb[3] + _REGION_MARGIN)
                    and not _text_outside(blocks, c.pages[0], above=cb[1] - _REGION_MARGIN)):
                rows = c.rows
                if [_key(t) for t in c.text_rows()[0]] == [_key(t) for t in prev.text_rows()[0]]:
                    rows = rows[1:]
                out[-1] = TableCandidate(prev.source, prev.rows + rows,
                                         {**prev.bboxes, **c.bboxes})
                continue
        out.append(c)
    return out


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
                  blocks: list[Block]) -> list[Section]:
    """Choose one table per region from the three extractors.

    Primary version by source priority (tags, ruling lines, text positions),
    skipping versions that fail the rule checks. Confidence:
      - another source agrees cell for cell        -> HIGH
      - only one source found the table            -> HIGH
      - other sources found it but disagree        -> UNCERTAIN, and every
        version is kept for the prompts file
    A text-position table that fails the rule checks and has no better
    version is dropped, so its blocks flow back into normal processing.
    """
    tomd = [candidate_from_section(s) for s in tomd_sections]
    cands = tagged + stitch_pages(ruled, blocks) + tomd
    for c in cands:
        c.flags = c.flags + table_flags(c)

    groups: list[list[TableCandidate]] = []
    for c in cands:
        hit = [g for g in groups if any(_overlap(c, d) >= _GROUP_OVERLAP for d in g)]
        if not hit:
            groups.append([c])
            continue
        merged = [c] + [d for g in hit for d in g]
        groups = [g for g in groups if g not in hit] + [merged]

    out: list[Section] = []
    for g in groups:
        g.sort(key=_priority)
        good = [c for c in g if not _is_bad(c)]
        if not good:
            _log.debug("Dropping table candidates on page %d: %s",
                       g[0].pages[0], [(c.source, c.flags) for c in g])
            continue
        primary = good[0]
        others = [c for c in g if c is not primary and c.source != primary.source]
        if not others:
            conf = Confidence.HIGH
        elif any(candidates_agree(primary, o) for o in others):
            conf = Confidence.HIGH
        else:
            conf = Confidence.UNCERTAIN
        out.append(_to_section(primary, conf, others))
        _log.debug("Table p%d %dx%d from %s: %s", primary.pages[0], *primary.shape,
                   primary.source, conf.value)
    return out


def remove_table_regions(blocks: list[Block], tables: list[Section]) -> list[Block]:
    """Drop the lines that fall inside any chosen table's region."""
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
                           and r[1] <= (ln.bbox[1] + ln.bbox[3]) / 2 <= r[3] for r in rs)]
        if len(keep) == len(blk.lines):
            out.append(blk)
        elif keep:
            out.append(Block(lines=keep, page_num=blk.page_num,
                             bbox=(min(l.bbox[0] for l in keep), min(l.bbox[1] for l in keep),
                                   max(l.bbox[2] for l in keep), max(l.bbox[3] for l in keep))))
    return out
