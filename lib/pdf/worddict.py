"""A fixed English word list for deciding line-end hyphens in table cells (2026-10-23).

The decision used to rest on the paper's running text, which is outside the table (locality),
and was wrong where the paper never wrote the word whole ("re-gion", "illformed"). The word list
is the system's Webster's Second (/usr/share/dict/web2), used only when its contents match the
pinned hash, so the output never depends on which word list a machine happens to have; without
it the earlier behaviour stands.
"""
from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

DICT_PATH = Path("/usr/share/dict/web2")
DICT_SHA256 = "be41ad97963bf8dabedd5871d5d691596175269d540956b0f9965a885c2bbab9"


@lru_cache(maxsize=1)
def words() -> frozenset | None:
    try:
        data = DICT_PATH.read_bytes()
    except OSError:
        return None
    if hashlib.sha256(data).hexdigest() != DICT_SHA256:
        return None
    return frozenset(w.strip().lower() for w in data.decode("utf-8", "replace").splitlines() if w.strip())


def is_word(w: str) -> bool:
    """w, or w with a common inflection removed, is in the word list (False without one)."""
    d = words()
    if not d or not w:
        return False
    w = w.lower()
    if w in d:
        return True
    cands = []
    if w.endswith("ies"):
        cands.append(w[:-3] + "y")
    if w.endswith("es"):
        cands.append(w[:-2])
    if w.endswith("s"):
        cands.append(w[:-1])
    if w.endswith("ed"):
        cands += [w[:-2], w[:-1]]
    if w.endswith("ing"):
        cands += [w[:-3], w[:-3] + "e"]
    if w.endswith("ly"):
        cands.append(w[:-2])
    return any(c in d for c in cands)


def available() -> bool:
    return words() is not None
