"""WG21 poll result tables.

WG21 papers and minutes record straw polls in a fixed shape: a header line
"SF F N A SA" (Strongly For, For, Neutral, Against, Strongly Against) with
the vote counts in the line below, one count under each header. Authors draw
it in many ways - ruled, unruled, inside a coloured box, tab-aligned - and
the other table sources miss most of them (too few rules, no tags), so this
source looks for the shape itself.

A poll is recognised when a text line consists of exactly the five header
tokens in order. Rows of numbers directly below whose numbers sit under the
header columns are its counts (up to _MAX_ROWS). A suggested poll with no
counts yet is emitted with an empty vote row when one is drawn under the
header, otherwise as a header-only table. A header followed by text on
the same line ("SF F N A SA: 4 5 1 0 0") is inline prose and is left alone.
"""

import logging
import re

from .pagecache import rawdict as _rawdict
from .types import TableCandidate
from .ruled import _page_words, _word_chars, _chars_to_lines, _text_lines

_log = logging.getLogger(__name__)

_HEADER = ["SF", "F", "N", "A", "SA"]
# Vote labels and their side: +1 for, 0 neutral, -1 against. A header is a
# line made only of these, in that order (for ... neutral ... against):
# "SF F N A SA", "SF WF N WA SA", "F N A", "Strongly Favor ... Strongly Against".
VOTE_LABELS = {
    "sf": 1, "wf": 1, "f": 1, "strongly favor": 1, "strongly for": 1, "weakly favor": 1,
    "weakly for": 1, "favor": 1, "for": 1, "favour": 1, "strongly favour": 1,
    "n": 0, "neutral": 0,
    "wa": -1, "a": -1, "sa": -1, "against": -1, "weakly against": -1, "strongly against": -1,
}


def vote_header(labels: list[str]) -> bool:
    """These cell texts form a poll header (see VOTE_LABELS)."""
    sides = [VOTE_LABELS.get(" ".join(t.lower().split())) for t in labels]
    if len(sides) < 3 or None in sides or 1 not in sides or -1 not in sides:
        return False
    return sides == sorted(sides, reverse=True)


def _label_cells(lw: list) -> list[list]:
    """Group a line's words into cells: words closer than a word gap join."""
    cells: list[list] = []
    for w in lw:
        if cells and w[0] - cells[-1][-1][2] < 0.6 * (w[3] - w[1]):
            cells[-1].append(w)
        else:
            cells.append([w])
    return cells
_ZERO_WIDTH = "​‌‍﻿"
_COUNT_RE = re.compile(r"^(\d{1,3}|[-–—])$")
_MAX_ROWS = 3
_ROW_GAP_RATIO = 2.5      # a count row starts within this many line heights
_EMPTY_ROW_RATIO = 3.0    # rules this close below the header bound an empty vote row


def _clean(text: str) -> str:
    return text.strip(_ZERO_WIDTH + " |")


def _row_cells(words, centers, half):
    """Assign words to the nearest header column; None if any does not fit."""
    cells: list[list] = [[] for _ in centers]
    for w in words:
        xc = (w[0] + w[2]) / 2
        k = min(range(len(centers)), key=lambda i: abs(centers[i] - xc))
        if abs(centers[k] - xc) > half:
            return None
        cells[k].append(w)
    return cells


def _strip_zero_width(lines):
    for ln in lines:
        for s in ln.spans:
            s.text = "".join(c for c in s.text if c not in _ZERO_WIDTH)
        ln.spans = [s for s in ln.spans if s.text]
    return [ln for ln in lines if ln.spans]


def extract_poll_tables(page, page_num: int, words_hint=None) -> list[TableCandidate]:
    """Poll result tables on one page. `words_hint` (the page's words, already
    extracted) lets a page with no vote label skip the character extraction."""
    if words_hint is not None and not any(VOTE_LABELS.get(_clean(w[4]).lower()) == -1 for w in words_hint):
        return []
    raw = _rawdict(page)
    words = [w for w in _page_words(raw) if _clean(w[4])]
    if not any(VOTE_LABELS.get(_clean(w[4]).lower()) == -1 for w in words):
        return []
    lines = _text_lines(words)
    out = []
    for i, (top, bot, lw) in enumerate(lines):
        lw = sorted(lw, key=lambda w: w[0])
        # one label per word ("SF F N A SA", however tightly set), else
        # words grouped into multi-word labels ("Strongly Favor ...")
        head = [[w] for w in lw]
        if not vote_header([_clean(w[4]) for w in lw]):
            head = _label_cells(lw)
            if not vote_header([" ".join(_clean(w[4]) for w in c) for c in head]):
                continue
        centers = [(c[0][0] + c[-1][2]) / 2 for c in head]
        half = min(b - a for a, b in zip(centers, centers[1:])) / 2
        height = bot - top
        rows = [head]
        last_bot = bot
        for top2, bot2, lw2 in lines[i + 1:i + 1 + _MAX_ROWS]:
            if top2 - last_bot > _ROW_GAP_RATIO * height:
                break
            if not all(_COUNT_RE.match(_clean(w[4])) for w in lw2):
                break
            cells = _row_cells(lw2, centers, half)
            if cells is None:
                break
            rows.append(cells)
            last_bot = bot2
        table_rows = [[_strip_zero_width(_chars_to_lines(_word_chars(c), page_num)) for c in row]
                      for row in rows]
        if len(rows) == 1:
            # a suggested poll (no counts yet) still has its vote row, blank -
            # drawn or not (convention: every poll is a header and a vote row)
            table_rows.append([[] for _ in head])
        x0 = min(w[0] for w in lw) - 2
        x1 = max(w[2] for w in lw) + 2
        cand = TableCandidate("poll", table_rows, {page_num: (x0, top - 1, x1, last_bot + 1)})
        if len(rows) == 1:
            cand.flags.append("blank-row-inferred")       # by convention, not seen: no evidence
        out.append(cand)
    if out:
        _log.debug("Page %d: %d poll table(s)", page_num, len(out))
    return out
