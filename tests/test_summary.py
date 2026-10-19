"""Paper-level summary: header comment placement, line markers, fields."""

import re
from pathlib import Path

import pytest

from lib.pdf import convert_pdf, convert_pdf_with_summary

_PDF = Path(__file__).resolve().parent / "fixtures" / "golden" / "p0957r8.pdf"


@pytest.fixture(scope="module")
def both():
    if not _PDF.is_file():
        pytest.skip("missing PDF fixture")
    mp = pytest.MonkeyPatch()
    mp.setenv("TOMD_SUMMARY", "0")
    plain, _ = convert_pdf(_PDF)
    mp.undo()
    md, prompts, summary = convert_pdf_with_summary(_PDF)
    return plain, md, prompts, summary


def test_comment_follows_front_matter(both):
    plain, md, _, _ = both
    lines = md.split("\n")
    end = lines.index("---", 1)
    assert lines[end + 1].startswith("<!-- tomd:summary tables=")
    # nothing else changed (marker numbers move: checked below)
    strip = lambda t: re.sub(r"tomd:uncertain:L\d+-L\d+", "", t)
    assert strip("\n".join(lines[:end + 1] + lines[end + 2:])) == strip(plain)


def test_uncertain_markers_still_point_at_their_lines(both):
    plain, md, _, _ = both
    pl, ml = plain.split("\n"), md.split("\n")
    a = re.findall(r"tomd:uncertain:L(\d+)-L(\d+)", plain)
    b = re.findall(r"tomd:uncertain:L(\d+)-L(\d+)", md)
    assert a and len(a) == len(b)
    for (x0, x1), (y0, y1) in zip(a, b):
        assert pl[int(x0) - 1] == ml[int(y0) - 1]
        assert pl[int(x1) - 1] == ml[int(y1) - 1]


def test_summary_fields(both):
    _, _, prompts, s = both
    t = s["tables"]
    assert t["total"] == t["trusted"] + t["flagged"]
    assert 0.0 <= s["unfamiliarity"]["score"] <= 1.0
    c = s["confidence"]
    assert c is not None and 0.0 <= c["value"] <= c["band"]
    # an unfamiliar paper never gets the familiar papers' figure
    assert c["value"] <= 1.0 - 0.5 * s["unfamiliarity"]["score"] + 1e-9
    assert "## Paper summary" in prompts
