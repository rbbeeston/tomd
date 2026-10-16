"""Table accuracy against the hand-verified truth set (fixtures/tables/).

For each paper whose PDF is available, convert it and check that:
  - every in-scope truth table appears in the Markdown with the same grid
    and the same text in every cell (whitespace collapsed, Markdown code and
    emphasis markers removed), unless it is listed in KNOWN_GAPS;
  - no table in the Markdown is unrelated to every truth table (a false
    table such as a bullet list or a code listing rendered as a table).

Only p0533r9 and p0957r8 have their PDFs committed. Point TOMD_TABLE_CORPUS
at a folder of <stem>.pdf files (downloaded from open-std.org, see
fixtures/tables/README.md) to run the whole set.
"""

import json
import os
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import mistune
import pytest

from lib.pdf import convert_pdf

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_TRUTH = sorted((_FIXTURES / "tables").glob("*.json"))
_CORPUS = os.environ.get("TOMD_TABLE_CORPUS")

# In-scope tables tomd does not get right yet, with the reason. Remove an
# entry when it is fixed; the test fails if a listed table starts passing so
# the list stays honest.
KNOWN_GAPS = {
    "n5040-t3": "PDF text layer prints mojibake (std::spanâ€™s); exact text differs",
    "p0533r9-t2": "booktabs table with 2 data rows; column split is ambiguous",
    "p0533r9-t4": "Comment column is empty in every body row and is dropped",
    "p0957r8-t4": "booktabs table split by a page break; neither part has enough rules",
    "p4317r1-t2": "two adjacent tables on one page share rules; caption not detected",
    "p4317r1-t3": "two adjacent tables on one page share rules; caption not detected",
    "p4317r1-t6": "zebra table continued on the next page is not stitched",
    "p4317r1-t7": "header row merged with caption band",
    "p4317r1-t12": "one cell's overprinted identifier truncated",
    "p4317r1-t15": "identifier overprints the next column in a 2-row table",
    "p4317r1-t16": "identifier overprints the next column in a 2-row table",
    "p4318r1-t3": "math font has no Unicode mapping; text layer is garbage",
}

_MD = mistune.create_markdown(renderer="ast", plugins=["table"])


def _norm(s: str) -> str:
    # GFM removes the "\|" escape inside table cells, code spans included;
    # mistune leaves it in code spans, so undo it here.
    s = unicodedata.normalize("NFKC", s).replace("`", "").replace("\\|", "|")
    return re.sub(r"\s+", " ", s).strip()


def _inline_text(nodes) -> str:
    out = []
    for n in nodes:
        if n["type"] in ("text", "codespan"):
            out.append(n.get("raw", ""))
        elif n["type"] == "inline_html":
            raw = n.get("raw", "")
            out.append(" " if raw.lower().startswith("<br") else raw)
        elif n["type"] in ("linebreak", "softbreak"):
            out.append(" ")
        if "children" in n:
            out.append(_inline_text(n["children"]))
    return "".join(out)


def _md_tables(md: str) -> list[list[list[str]]]:
    tables = []

    def walk(nodes):
        for n in nodes:
            if n["type"] == "table":
                rows = []
                for part in n["children"]:
                    if part["type"] == "table_head":
                        rows.append([_norm(_inline_text(c["children"])) for c in part["children"]])
                    else:
                        for r in part["children"]:
                            rows.append([_norm(_inline_text(c["children"])) for c in r["children"]])
                tables.append(rows)
            elif "children" in n:
                walk(n["children"])

    walk(_MD(md))
    return tables


def _text(rows) -> str:
    return re.sub(r"\s+", "", " ".join(" ".join(r) for r in rows))


def _pdf_for(stem: str) -> Path | None:
    p = _FIXTURES / "golden" / f"{stem}.pdf"
    if p.is_file():
        return p
    if _CORPUS and (Path(_CORPUS) / f"{stem}.pdf").is_file():
        return Path(_CORPUS) / f"{stem}.pdf"
    return None


@pytest.mark.parametrize("truth_file", _TRUTH, ids=[t.stem for t in _TRUTH])
def test_tables_match_truth(truth_file: Path):
    truth = json.loads(truth_file.read_text(encoding="utf-8"))
    pdf = _pdf_for(truth["paper"])
    if pdf is None:
        pytest.skip(f"PDF for {truth['paper']} not available (set TOMD_TABLE_CORPUS)")

    md, _ = convert_pdf(pdf)
    emitted = _md_tables(md)

    wrong, fixed = [], []
    for t in truth["tables"]:
        if t.get("scope", "table") != "table":
            continue
        want = [[_norm(c) for c in r] for r in t["rows"]]
        ok = want in emitted
        if not ok and t["id"] not in KNOWN_GAPS:
            wrong.append(t["id"])
        if ok and t["id"] in KNOWN_GAPS:
            fixed.append(t["id"])

    false_tables = []
    for rows in emitted:
        best = max((SequenceMatcher(None, _text(rows), _text(t["rows"]), autojunk=False).ratio()
                    for t in truth["tables"]), default=0.0)
        if best < 0.5:
            false_tables.append(" | ".join(rows[0])[:80])

    assert not wrong, f"{truth['paper']}: tables not extracted exactly: {wrong}"
    assert not fixed, f"{truth['paper']}: now correct, remove from KNOWN_GAPS: {fixed}"
    if truth["paper"] != "p4318r1":  # its garbled-font table matches nothing by text
        assert not false_tables, f"{truth['paper']}: tables not in the truth set: {false_tables}"
