"""One rawdict extraction per page, shared by the readers that need characters
(the rule-band reader and the poll reader each extracted it on their own).
The cache lives on the document object, so it goes away with it (keying a
global cache by id() returned another document's text once ids were reused)."""
from __future__ import annotations


def clear() -> None:
    """Kept for callers; the cache is per document and needs no clearing."""


def rawdict(page):
    doc = page.parent
    cache = getattr(doc, "_tomd_rawdict", None)
    if cache is None:
        cache = {}
        try:
            doc._tomd_rawdict = cache
        except AttributeError:          # an object that takes no attributes: no cache
            return page.get_text("rawdict", flags=0)
    raw = cache.get(page.number)
    if raw is None:
        raw = cache[page.number] = page.get_text("rawdict", flags=0)
    return raw


def words_in(page, bbox):
    """The page's words whose centre lies in bbox. Words are taken whole from the
    whole page: a clipped extraction drops glyphs whose ink falls outside the clip
    (a period on the baseline below a region's edge) and splits the word there."""
    doc = getattr(page, "parent", None)
    cache = getattr(doc, "_tomd_words", None) if doc is not None else None
    if cache is None and doc is not None:
        cache = {}
        try:
            doc._tomd_words = cache
        except AttributeError:
            cache = None
    words = cache.get(page.number) if cache is not None else None
    if words is None:
        words = page.get_text("words")
        if cache is not None:
            cache[page.number] = words
    x0, y0, x1, y1 = tuple(bbox)
    return [w for w in words if x0 <= (w[0] + w[2]) / 2 <= x1 and y0 <= (w[1] + w[3]) / 2 <= y1]
