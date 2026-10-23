"""One rawdict extraction per page, shared by the readers that need characters
(the rule-band reader and the poll reader each extracted it on their own).
The cache lives on the document object, so it goes away with it (keying a
global cache by id() returned another document's text once ids were reused)."""
from __future__ import annotations

import os


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
        raw = cache[page.number] = _dedup_raw(page.get_text("rawdict", flags=0))
    return raw


def _dedup_raw(raw: dict) -> dict:
    """the text layer without a second copy of the same characters printed over the
    first (a header encoded twice, offset by under a point): the page shows it once"""
    import os
    if os.environ.get("TOMD_DEDUP") == "0":
        return raw
    seen: dict = {}
    dup = 0
    for blk in raw.get("blocks", []):
        for ln in blk.get("lines", []) if blk.get("type") == 0 else []:
            for sp in ln.get("spans", []):
                for ch in sp.get("chars", []):
                    if not ch.get("c", "").strip():
                        continue
                    b = ch["bbox"]
                    k = (ch["c"], round(b[0]), round(b[1] / 2))
                    if any((ch["c"], k[1] + i, k[2] + j) in seen for i in (-1, 0, 1) for j in (-1, 0, 1)
                           if abs(seen.get((ch["c"], k[1] + i, k[2] + j), (1e9, 1e9))[0] - b[0]) < 1.0
                           and abs(seen.get((ch["c"], k[1] + i, k[2] + j), (1e9, 1e9))[1] - b[1]) < 1.5):
                        ch["_dup"] = True
                        dup += 1
                    else:
                        seen[k] = (b[0], b[1])
    if not dup:
        return raw
    out = {**raw, "blocks": []}
    for blk in raw.get("blocks", []):
        if blk.get("type") != 0:
            out["blocks"].append(blk)
            continue
        lines = []
        for ln in blk.get("lines", []):
            sps = [{**sp, "chars": [c for c in sp.get("chars", []) if not c.get("_dup")]} for sp in ln.get("spans", [])]
            sps = [sp for sp in sps if sp["chars"]]
            if sps:
                lines.append({**ln, "spans": sps})
        if lines:
            out["blocks"].append({**blk, "lines": lines})
    return out


def _dedup_words(words: list) -> list:
    import os
    if os.environ.get("TOMD_DEDUP") == "0":
        return words
    out, seen = [], {}
    for w in words:
        k = (w[4], round(w[0]), round(w[1] / 2))
        if any(abs(v[0] - w[0]) < 1.0 and abs(v[1] - w[1]) < 1.5
               for i in (-1, 0, 1) for j in (-1, 0, 1) for v in seen.get((w[4], k[1] + i, k[2] + j), [])):
            continue
        seen.setdefault(k, []).append((w[0], w[1]))
        out.append(w)
    return out


def hidden_chars(page, drawings=None) -> list:
    """bboxes of characters an opaque box drawn after them covers (slide decks hide
    the rows of a build under a white box): text the page does not show"""
    import os
    if os.environ.get("TOMD_COVERED") == "0":
        return []
    doc = getattr(page, "parent", None)
    cache = getattr(doc, "_tomd_hidden", None) if doc is not None else None
    if cache is None and doc is not None:
        cache = {}
        try:
            doc._tomd_hidden = cache
        except AttributeError:
            cache = None
    if cache is not None and page.number in cache:
        return cache[page.number]
    drawings = page.get_drawings()          # all of them: a caller's list may omit fills
    fills = [(it[1], d.get("seqno", -1)) for d in drawings
             if d.get("fill") is not None and (d.get("fill_opacity") is None or d.get("fill_opacity") >= 0.99)
             for it in d["items"] if it[0] == "re" and it[1].width > 4 and it[1].height > 4]
    out = []
    if fills:
        try:
            trace = page.get_texttrace()
        except Exception as e:  # noqa: BLE001
            from . import evidence
            evidence.reader_error("covered-text check", page.number, e)
            trace = []
        for sp in trace:
            later = [r for r, q in fills if q > sp.get("seqno", 1 << 30)]
            if not later:
                continue
            # a run is hidden only when the box covers all of it: a box over the end of a
            # line (a listing clipped at a frame's edge) leaves the line in the text layer
            boxes = [tuple(ch[3]) for ch in sp.get("chars", []) if chr(ch[0]).strip()]
            if boxes and all(any(r.x0 <= (b[0] + b[2]) / 2 <= r.x1 and r.y0 <= (b[1] + b[3]) / 2 <= r.y1
                                 for r in later) for b in boxes):
                out.extend(boxes)
    if cache is not None:
        cache[page.number] = out
    return out


def remove_covered_text(pages) -> int:
    """redact (in memory) the characters hidden_chars finds; pages changed"""
    n = 0
    for page in pages:
        hidden = hidden_chars(page)
        if not hidden:
            continue
        try:
            import fitz as pymupdf
            for b in hidden:
                cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                page.add_redact_annot(pymupdf.Rect(cx - 0.5, cy - 0.5, cx + 0.5, cy + 0.5))
            page.apply_redactions(images=0, graphics=0, text=0)
            n += 1
            try:
                page.parent._tomd_covered = getattr(page.parent, "_tomd_covered", 0) + 1
            except AttributeError:
                pass
        except Exception as e:  # noqa: BLE001  (a page that cannot be redacted keeps its text)
            from . import evidence
            evidence.reader_error("covered-text removal", page.number, e)
            continue
    return n


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
        words = _dedup_words(page.get_text("words"))
        # words of rotated lines (a column label set at 90 degrees) are not words of the
        # horizontal text: the readers place such a label whole (ruled._unrotate,
        # content's rotated header), so a word-level pass must not place its words again
        if os.environ.get("TOMD_UNROTATE") != "0" and doc is not None:
            rot = [tuple(ln["bbox"]) for b in rawdict(page).get("blocks", []) if b.get("type") == 0
                   for ln in b.get("lines", []) if abs(ln.get("dir", (1, 0))[0] - 1) > 0.01]
            if rot:
                words = [w for w in words if not any(r[0] - 0.5 <= (w[0] + w[2]) / 2 <= r[2] + 0.5
                                                     and r[1] - 0.5 <= (w[1] + w[3]) / 2 <= r[3] + 0.5 for r in rot)]
        if cache is not None:
            cache[page.number] = words
    x0, y0, x1, y1 = tuple(bbox)
    return [w for w in words if x0 <= (w[0] + w[2]) / 2 <= x1 and y0 <= (w[1] + w[3]) / 2 <= y1]
