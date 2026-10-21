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
