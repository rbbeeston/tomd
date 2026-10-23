"""Readers never fail silently.

A reader, check or specialist that raises is recorded (stage, page, exception
type and message), every table it touched drops to UNCERTAIN with the reason
"reader error", and the prompts note lists it. In g79 a missing import made the
tagged reader raise on every tagged paper; the pipeline swallowed it and 60
tables degraded with no trace.
"""
from pathlib import Path

import pytest

import lib.pdf as P
from lib.pdf.types import Confidence

GOLDEN = Path(__file__).parent / "fixtures" / "golden"
PDFS = sorted(GOLDEN.glob("*.pdf"))


@pytest.mark.parametrize("pdf", PDFS, ids=[p.stem for p in PDFS])
def test_every_reader_runs_without_raising(pdf, monkeypatch):
    """TOMD_STRICT=1 re-raises any recorded reader error: every reader, check and
    specialist must run cleanly on the golden papers."""
    monkeypatch.setenv("TOMD_STRICT", "1")
    res = P._run_pipeline(pdf)
    assert not getattr(res, "reader_errors", [])


def test_a_raising_reader_is_recorded_and_flags_its_tables(monkeypatch):
    """A page reader that raises: recorded as a code error on that page, the page's
    tables are at most UNCERTAIN with "reader error", and the prompts list it."""
    pdf = GOLDEN / "p0533r9.pdf"
    calls = []

    def broken(page, pg_num, drawings=None):
        calls.append(pg_num)
        if pg_num == 0:
            raise NameError("name 'os' is not defined")
        return []

    monkeypatch.setattr(P, "extract_ruled_tables", broken)
    res = P._run_pipeline(pdf)
    errs = res.reader_errors
    assert errs and errs[0]["stage"] == "page table readers" and errs[0]["page"] == 0
    assert errs[0]["kind"] == "code" and errs[0]["type"] == "NameError"
    for sec in res.sections:
        if sec.kind.value == "table" and sec.page_num == 0:
            assert sec.confidence == Confidence.UNCERTAIN
            assert "reader error" in sec.metadata.get("uncertain_reasons", [])
    assert "Reader errors" in (res.prompts or "")
    assert "NameError" in (res.prompts or "")
    # the Markdown marks them too (the downgrade happens before it is written)
    flagged = sum(1 for sec in res.sections if sec.kind.value == "table" and sec.confidence == Confidence.UNCERTAIN)
    assert (res.md or "").count("tomd:uncertain:") >= flagged


def test_a_stage_that_cannot_touch_tables_downgrades_none(monkeypatch):
    """Locality (2026-10-23): a failure in a stage that cannot touch a table's content (here
    the figure labels) is still recorded and listed for the paper, but downgrades no table."""
    pdf = GOLDEN / "p0533r9.pdf"
    import lib.pdf.figures as F

    def broken(doc, tables):
        raise NameError("name 'x' is not defined")

    monkeypatch.setattr(F, "label_figure_tables", broken)
    res = P._run_pipeline(pdf)
    assert any(e["stage"] == "figure labels" for e in res.reader_errors)
    assert "Reader errors" in (res.prompts or "")
    for sec in res.sections:
        if sec.kind.value == "table":
            assert "reader error" not in sec.metadata.get("uncertain_reasons", [])


def test_one_tables_check_failure_does_not_downgrade_its_neighbours(monkeypatch):
    """A per-table check (the fit witness) that raises for one table downgrades that table
    only, not the other tables on its page or in the paper."""
    pdf = GOLDEN / "p0533r9.pdf"
    import lib.pdf.fit as FIT
    real = FIT.fit
    seen = []

    def first_fails(page, bbox, words, columns):
        seen.append(bbox)
        if len(seen) == 1:
            raise ValueError("bad cell")
        return real(page, bbox, words, columns)

    monkeypatch.setattr(FIT, "fit", first_fails)
    res = P._run_pipeline(pdf)
    errs = [e for e in res.reader_errors if e["stage"] == "fit"]
    assert len(errs) == 1 and errs[0]["table"]
    tables = [sec for sec in res.sections if sec.kind.value == "table"]
    hit = [sec for sec in tables if "reader error" in sec.metadata.get("uncertain_reasons", [])]
    assert len(tables) >= 2 and len(hit) == 1
