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
    "p3654r0-t1": "side-by-side code slide, reclassified as a table 2026-10-17; not detected",
    "p3654r0-t2": "side-by-side code slide, reclassified as a table 2026-10-17; not detected",
    "p3654r0-t3": "side-by-side code slide, reclassified as a table 2026-10-17; not detected",
    "p0533r9-t4": "ambiguous: the empty Comment column shows only in the header, \"Pass Comment\" spaced like one two-word header; only a sibling table reveals two columns",
    "p4318r1-t3": "PDF text layer is damaged (math italics written without their last hex digit); not recoverable from text, so the table is marked uncertain with a note",
    # Held-out set (2026-10): misses measured before any tuning on these papers
    # and still open after the general fixes; reasons are the measured category.
    "p2654r1-t2": "held-out text nearly right (LaTeX)",
    "p2988r12-t7": "held-out partly extracted (LaTeX)",
    "p2988r12-t9": "held-out partly extracted (LaTeX)",
    "p3096r12-t4": "held-out mostly wrong (LaTeX)",
    "p3430r3-t4": "held-out text nearly right (LaTeX)",
    "p3430r3-t5": "held-out text nearly right (LaTeX)",
    "p3430r3-t6": "held-out text nearly right (LaTeX)",
    "p3430r3-t7": "held-out text nearly right (LaTeX)",
    "p3430r3-t8": "held-out text nearly right (LaTeX)",
    "p3430r3-t9": "held-out text nearly right (LaTeX)",
    "p3550r0-t2": "held-out mostly wrong (LaTeX)",
    "p3550r0-t3": "held-out mostly wrong (LaTeX)",
    "p3561r2-t1": "held-out not detected (Ghostscript)",
    "p3561r2-t2": "held-out partly extracted (Ghostscript)",
    "p3605r1-t1": "held-out not detected (Chrome/Skia)",
    "p3605r1-t2": "held-out partly extracted (Chrome/Skia)",
    "p3691r1-t8": "held-out partly extracted (LaTeX)",
    "p3691r1-t9": "held-out partly extracted (LaTeX)",
    "p3866r0-t1": "held-out not detected (Typst)",
    "p3977r0-t2": "held-out not detected (LaTeX)",
    "p4016r0-t16": "held-out partly extracted (pypdf)",
    "p4016r0-t17": "held-out not detected (pypdf)",
    "p4016r0-t20": "held-out mostly wrong (pypdf)",
    "p4016r0-t3": "held-out mostly wrong (pypdf)",
    "p4016r0-t4": "held-out not detected (pypdf)",
    "p4089r1-t2": "held-out not detected (ReportLab)",
    "p4089r1-t3": "held-out not detected (ReportLab)",
    "p4089r1-t4": "held-out partly extracted (ReportLab)",
    "p4089r1-t5": "held-out mostly wrong (ReportLab)",
    "p4195r0-t6": "held-out mostly wrong (ReportLab)",
}

# Emitted tables that match no truth table, per paper (exact count). Lower a
# count when a fix removes one; a new false table fails the test.
KNOWN_FALSE_TABLES = {
    "n5057": 1,
    "p3096r12": 2,
    "p3550r0": 1,
    "p3561r2": 1,
    "p3691r1": 2,
    "p3790r2": 1,
    "p3813r0": 1,
    "p4016r0": 3,
    "p4089r1": 1,
    "p4100r1": 1,      # front-matter key/value block, emitted uncertain
    "p4124r0": 1,
    "p4195r0": 1,
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


_CODE_CMP = re.compile(r"<!-- tomd:table kind=code-comparison cols=(\d+) -->")
_CODE_PART = re.compile(r"\s*(?:\*\*(.+?)\*\*\s*)?```[a-z]*\n(.*?)\n```", re.S)


def _code_comparisons(md: str) -> list[list[list[str]]]:
    """Code-comparison tables, rendered as paired fenced blocks under bold headers."""
    out = []
    for m in _CODE_CMP.finditer(md):
        pos, heads, codes = m.end(), [], []
        for _ in range(int(m.group(1))):
            part = _CODE_PART.match(md, pos)
            if not part:
                break
            heads.append(_norm(part.group(1) or ""))
            codes.append(_norm(part.group(2)))
            pos = part.end()
        out.append(([heads] if any(heads) else []) + [codes])
    return out


def _md_tables(md: str) -> list[list[list[str]]]:
    tables = _code_comparisons(md)

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
    allowed = KNOWN_FALSE_TABLES.get(truth["paper"], 0)
    assert len(false_tables) == allowed, (
        f"{truth['paper']}: {len(false_tables)} tables not in the truth set "
        f"(KNOWN_FALSE_TABLES allows {allowed}): {false_tables}")
