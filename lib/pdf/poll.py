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

from .types import TableCandidate
from .ruled import _page_words, _word_chars, _chars_to_lines, _text_lines, _horizontal_rules

_log = logging.getLogger(__name__)

_HEADER = ["SF", "F", "N", "A", "SA"]
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


def _drawn_empty_row(rules, header_words, bottom, height) -> bool:
    """Two rules spanning the header just below it: a ruled, empty vote row."""
    x0 = min(w[0] for w in header_words) - 2
    x1 = max(w[2] for w in header_words) + 2
    below = [r for r in rules if bottom - 1 <= r[0] <= bottom + _EMPTY_ROW_RATIO * height
             and r[1] <= x0 + 5 and r[2] >= x1 - 5]
    return len(below) >= 2


def extract_poll_tables(page, page_num: int) -> list[TableCandidate]:
    """Poll result tables on one page."""
    raw = page.get_text("rawdict", flags=0)
    words = [w for w in _page_words(raw) if _clean(w[4])]
    if not any(_clean(w[4]) == "SA" for w in words):
        return []
    lines = _text_lines(words)
    rules = _horizontal_rules(page.get_drawings())
    out = []
    for i, (top, bot, lw) in enumerate(lines):
        lw = sorted(lw, key=lambda w: w[0])
        if [_clean(w[4]) for w in lw] != _HEADER:
            continue
        centers = [(w[0] + w[2]) / 2 for w in lw]
        half = min(b - a for a, b in zip(centers, centers[1:])) / 2
        height = bot - top
        rows = [[[w] for w in lw]]
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
        if len(rows) == 1 and _drawn_empty_row(rules, lw, bot, height):
            table_rows.append([[] for _ in _HEADER])       # a suggested poll's blank vote row
        x0 = min(w[0] for w in lw) - 2
        x1 = max(w[2] for w in lw) + 2
        out.append(TableCandidate("poll", table_rows, {page_num: (x0, top - 1, x1, last_bot + 1)}))
    if out:
        _log.debug("Page %d: %d poll table(s)", page_num, len(out))
    return out
