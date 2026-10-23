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
