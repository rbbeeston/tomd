"""Opt-in LLM second look at questionable tables: a narrow check, asked twice.

For a table at L3 (structure uncertain) or L4 (content at risk) - never L0-L2 - a
vision model gets the page crop and tomd's reading, and answers one narrow question:
do these rows and columns match the table on the page (yes / no, and which rows are
wrong). The question is asked twice; only identical answers count (user, 2026-10-23).
Answers are cached by PDF hash, region, model and prompt version; the model is pinned.

What an answer can do: a "match" confirmed twice raises the table at most to LIKELY
(L1), never HIGH, and only when an independent reader already agrees with the reading
(the witness record); a "no" names the rows to check in the table's note. The text of
the table is never changed here (repair is llmrepair.py, measured apart).

On only with TOMD_LLM_CHECK=1 (the --corpus profile); credentials as llmrepair.py
resolves them (the SDK reads them; tomd never reads, logs or prints a key or token).
A budget per paper (TOMD_LLM_CHECK_BUDGET, questions; default 12) caps the cost.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path

from .llmrepair import _has_credentials, _image

_log = logging.getLogger(__name__)

CHECK_MODEL = "claude-sonnet-5-5"
PROMPT_VERSION = "check-v1"
_SCHEMA = {
    "type": "object",
    "properties": {"match": {"type": "boolean"},
                   "wrong_rows": {"type": "array", "items": {"type": "integer"}}},
    "required": ["match", "wrong_rows"],
    "additionalProperties": False,
}
_QUESTION = (
    "The image shows one table from a WG21 paper. Below is a reading of it as rows of "
    "cells (row 1 is the first row; cells separated by ' | '). Compare the reading with the "
    "image: are the rows and columns right - every row of the image present once, in order, "
    "each cell's text in the column it sits in on the page, nothing from outside the table "
    "added? Spacing, hyphenation and markup do not matter. Answer match=true only if the "
    "reading has the image's rows and columns. Otherwise match=false and list the numbers "
    "of the rows that are wrong, missing their content, or misplaced."
)
_STATE = {"questions": 0, "input_tokens": 0, "output_tokens": 0, "seconds": 0.0, "cache_hits": 0, "errors": 0}


def enabled() -> bool:
    return os.environ.get("TOMD_LLM_CHECK") == "1" and _has_credentials()


def _budget() -> int:
    v = os.environ.get("TOMD_LLM_CHECK_BUDGET", "12")
    return int(v) if v.isdigit() else 12


def state() -> dict:
    return dict(_STATE)


def reset() -> None:
    _STATE.update({"questions": 0, "input_tokens": 0, "output_tokens": 0, "seconds": 0.0, "cache_hits": 0, "errors": 0})


def _cache_path(pdf_hash: str, page: int, bbox, rows) -> Path:
    key = json.dumps([pdf_hash, page, [round(v, 1) for v in bbox], rows, CHECK_MODEL, PROMPT_VERSION])
    h = hashlib.sha256(key.encode()).hexdigest()[:32]
    base = Path(os.environ.get("TOMD_CACHE_DIR") or Path.home() / ".cache" / "tomd") / "llmcheck"
    return base / f"{h}.json"


def _ask_once(client, image_b64, rows):
    reading = "\n".join(f"{i + 1}: " + " | ".join(r) for i, r in enumerate(rows))
    t = time.perf_counter()
    resp = client.messages.create(
        model=CHECK_MODEL, max_tokens=1024,
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": _SCHEMA}},
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_b64}},
            {"type": "text", "text": _QUESTION + "\n\nReading:\n" + reading}]}])
    _STATE["seconds"] += time.perf_counter() - t
    u = getattr(resp, "usage", None)
    _STATE["input_tokens"] += getattr(u, "input_tokens", 0) or 0
    _STATE["output_tokens"] += getattr(u, "output_tokens", 0) or 0
    if getattr(resp, "stop_reason", None) == "refusal":
        return None
    text = next((b.text for b in resp.content if getattr(b, "type", "") == "text"), "")
    a = json.loads(text)
    return {"match": bool(a["match"]), "wrong_rows": sorted(int(x) for x in a.get("wrong_rows") or [])}


def check(client, page, bbox, rows, pdf_hash: str) -> dict | None:
    """{"match", "wrong_rows", "consistent"} from two identical answers, or None (the
    answers differed, an error, or the budget is spent)"""
    path = _cache_path(pdf_hash, page.number, bbox, rows)
    if path.exists():
        _STATE["cache_hits"] += 1
        return json.loads(path.read_text())
    if _STATE["questions"] + 2 > _budget():
        return None
    try:
        img = _image(page, bbox)
        a = _ask_once(client, img, rows)
        b = _ask_once(client, img, rows)
        _STATE["questions"] += 2
    except Exception as e:  # noqa: BLE001  (any API or network error: the table stays as it is)
        _STATE["errors"] += 1
        from . import evidence
        evidence.reader_error("llm check", page.number, e)
        return None
    out = {"match": a["match"], "wrong_rows": a["wrong_rows"], "consistent": a == b} if a and b else None
    if out is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(out))
    return out
