"""Check a HIGH table's text layer against the picture of the page.

Table sources agree because they all read the same text layer, so a text
layer that differs from what is printed fools them all at once (p3830r0:
the text layer says "WF" where the page shows "F", and all three sources
agreed). This check uses a different modality: it renders the table's
header row - and a poll's vote row - and reads it with OCR (Tesseract),
then compares tokens. A short token (a vote label, a count) must appear in
the OCR exactly; a longer word may differ a little (OCR noise). Any token of
the text layer that the picture does not show makes the table UNCERTAIN.

Opt-in (TOMD_OCR=1) and only when the tesseract command is installed.
"""

import os
import re
import shutil
import subprocess
from difflib import SequenceMatcher

_DPI = 300
_SHORT = 3            # tokens up to this length must match exactly
_FUZZY = 0.75         # longer tokens: this similarity to some OCR token
_TOKEN = re.compile(r"[A-Za-z0-9]+")


def ocr_enabled() -> bool:
    return os.environ.get("TOMD_OCR") == "1" and shutil.which("tesseract") is not None


def _ocr(page, bbox) -> str:
    import fitz
    clip = fitz.Rect(bbox) + (-2, -2, 2, 2)
    png = page.get_pixmap(dpi=_DPI, clip=clip).tobytes("png")
    try:
        r = subprocess.run(["tesseract", "stdin", "stdout", "--psm", "6"], input=png,
                           capture_output=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout.decode("utf-8", "replace")


def _row_box(row):
    bs = [s.bbox for cell in row for s in cell if s.text.strip() and s.text != "\n" and s.bbox]
    if not bs:
        return None
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))


def mismatched_tokens(text_tokens: list[str], ocr_text: str) -> list[str]:
    """Text-layer tokens the OCR does not show."""
    seen = [t.lower() for t in _TOKEN.findall(ocr_text)]
    if not seen:
        return []                       # no OCR evidence: no verdict
    bad = []
    for t in text_tokens:
        tl = t.lower()
        if tl in seen:
            continue
        if len(tl) > _SHORT and any(SequenceMatcher(None, tl, s).ratio() >= _FUZZY for s in seen):
            continue
        bad.append(t)
    return bad


def check_table(page, sec) -> str:
    """"" if the header (and a poll's votes) read the same in the picture, else a note."""
    rows = sec.columns[:1]
    if sec.metadata.get("table_source") == "poll":
        rows = sec.columns[:2]
    bad: list[str] = []
    for row in rows:
        box = _row_box(row)
        if box is None:
            continue
        text = " ".join(s.text for cell in row for s in cell if s.text != "\n")
        bad += mismatched_tokens(_TOKEN.findall(text), _ocr(page, box))
    if not bad:
        return ""
    return ("The printed page does not show " + ", ".join(f'"{b}"' for b in bad[:5]) +
            " where the PDF's text layer has it; read those cells from the page image.")
