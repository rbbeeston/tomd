"""Opt-in LLM repair of flagged tables: structure only, never content.

A table that is still UNCERTAIN after every deterministic reader and the
escalation moves may be sent to a vision model - only when TOMD_LLM=1 and
credentials exist: ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, or an
`ant auth login` profile (the Anthropic SDK resolves them; tomd never reads,
logs or prints a key or token). The model gets the rendered
table region and the page's own words, each with an index and position,
and returns rows of cells as lists of word indices. It cannot write text:
tomd builds every cell from the indexed page words.

The result is kept only if every word of the region is used exactly once
(nothing added, nothing lost) and the rebuilt table passes the same
geometric verification as any other table (validate.verify_layout).
Otherwise it is discarded and the table stays flagged. Any API error,
refusal or malformed answer leaves the table as it was.

Confident tables are never sent. Only paper text (public WG21 papers) and
the page image of the table are sent.
"""

import base64
import json
import logging
import os
import time

from .types import Span

_log = logging.getLogger(__name__)

MODEL = "claude-opus-5-5"
_DPI = 150
_MAX_WORDS = 1500          # a region larger than this is not sent
_SCHEMA = {
    "type": "object",
    "properties": {
        "rows": {
            "type": "array",
            "items": {"type": "array", "items": {"type": "array", "items": {"type": "integer"}}},
        },
    },
    "required": ["rows"],
    "additionalProperties": False,
}
_INSTRUCTIONS = (
    "The image shows one table from a WG21 paper. Below it is every word of the PDF's "
    "text layer inside the table's area, one per line as: index, x0, y0, x1, y1, text "
    "(page coordinates, y grows downwards).\n\n"
    "Arrange the words into the table's rows and cells, as a reader of the image would. "
    "Return rows top to bottom; each row is a list of cells left to right; each cell is "
    "the list of word indices in reading order (an empty list for an empty cell). Every "
    "row has the same number of cells. Use every index exactly once. You may only "
    "arrange the given words: never add, change or drop text. Conventions: the header "
    "row is the first row; several entries stacked in one drawn cell are separate rows; "
    "a cell whose text wraps is one cell; a cell spanning several columns goes in its "
    "first column with empty cells after it."
)


def _has_credentials() -> bool:
    """An API key, an auth token, or an `ant auth login` profile on disk -
    the sources the Anthropic SDK resolves, in that order. Nothing is read
    from them here; the SDK does that."""
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return True
    from pathlib import Path
    base = Path(os.environ.get("ANTHROPIC_CONFIG_DIR") or Path.home() / ".config" / "anthropic")
    return any((base / "credentials").glob("*.json"))


_DISABLED = False          # set after an authentication failure, for the rest of the run


def llm_enabled() -> bool:
    return os.environ.get("TOMD_LLM") == "1" and not _DISABLED and _has_credentials()


def _client():
    try:
        import anthropic
    except ImportError:
        _log.info("TOMD_LLM=1 but the anthropic package is not installed; skipping")
        return None
    return anthropic.Anthropic()


def _image(page, bbox) -> str:
    import fitz
    clip = fitz.Rect(bbox) + (-4, -4, 4, 4)
    return base64.standard_b64encode(page.get_pixmap(dpi=_DPI, clip=clip).tobytes("png")).decode()


def _prompt(words) -> str:
    lines = [f"{i}, {w[0]:.0f}, {w[1]:.0f}, {w[2]:.0f}, {w[3]:.0f}, {w[4]}" for i, w in enumerate(words)]
    return _INSTRUCTIONS + "\n\nWords:\n" + "\n".join(lines)


def ask(client, page, bbox, words):
    """(rows of index lists, model id, seconds, usage) or None."""
    t = time.perf_counter()
    try:
        resp = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": _SCHEMA}},
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                             "data": _image(page, bbox)}},
                {"type": "text", "text": _prompt(words)},
            ]}],
        )
    except Exception as e:  # any API or network error: leave the table flagged
        global _DISABLED
        if type(e).__name__ in ("AuthenticationError", "PermissionDeniedError"):
            _DISABLED = True       # bad or missing credentials: stop trying this run
            _log.warning("LLM repair disabled: the API rejected the credentials")
        else:
            _log.warning("LLM repair call failed (%s); table stays flagged", type(e).__name__)
        return None
    if getattr(resp, "stop_reason", None) == "refusal":
        return None
    text = next((b.text for b in resp.content if getattr(b, "type", "") == "text"), "")
    try:
        rows = json.loads(text)["rows"]
    except (ValueError, KeyError, TypeError):
        return None
    usage = getattr(resp, "usage", None)
    return rows, getattr(resp, "model", MODEL), time.perf_counter() - t, {
        "input_tokens": getattr(usage, "input_tokens", 0), "output_tokens": getattr(usage, "output_tokens", 0)}


def build_columns(rows, words):
    """Cells of spans from word indices, or (None, reason) if the answer is unusable:
    an index out of range, used twice, or a word left out."""
    used = [i for row in rows for cell in row for i in cell]
    if any(not isinstance(i, int) or i < 0 or i >= len(words) for i in used):
        return None, "unknown-word"
    if len(used) != len(set(used)):
        return None, "word-used-twice"
    if len(used) != len(words):
        return None, "word-left-out"
    if not rows or len({len(r) for r in rows}) != 1:
        return None, "ragged"
    columns = []
    for row in rows:
        out_row = []
        for cell in row:
            ws = [words[i] for i in cell]
            spans: list = []
            prev = None
            for w in ws:
                if prev is not None:
                    same_line = abs((w[1] + w[3]) / 2 - (prev[1] + prev[3]) / 2) <= 3
                    spans.append(Span(text=" ") if same_line else Span(text="\n"))
                spans.append(Span(text=w[4], bbox=tuple(w[:4])))
                prev = w
            out_row.append(spans)
        columns.append(out_row)
    return columns, ""


def repair(sec, page, bbox, words, verify, client=None) -> str:
    """Try to repair one flagged table in place. Returns what happened."""
    if len(words) > _MAX_WORDS or not words:
        return "skipped-size"
    client = client or _client()
    if client is None:
        return "no-client"
    answer = ask(client, page, bbox, words)
    if answer is None:
        return "no-answer"
    rows, model, seconds, usage = answer
    columns, why = build_columns(rows, words)
    record = {"model": model, "seconds": round(seconds, 2), **usage}
    if columns is None:
        sec.metadata["llm_repair"] = {**record, "result": "rejected:" + why}
        return "rejected:" + why
    import copy
    new = copy.copy(sec)
    new.columns = columns
    failed = verify(new, words)
    if failed:
        sec.metadata["llm_repair"] = {**record, "result": "rejected:" + failed}
        return "rejected:" + failed
    sec.columns = columns
    sec.text = "\n".join(" | ".join("".join(s.text for s in c) for c in r) for r in columns)
    sec.metadata["llm_repair"] = {**record, "result": "verified"}
    sec.metadata["table_source"] = "llm-structure"
    return "verified"
