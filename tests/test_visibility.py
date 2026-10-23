"""Text the PDF holds but the page does not show (lib/pdf/visibility.py).

adv.pdf (built by fixtures/hidden_text/mkfix.py) is one paper page carrying
eleven hiding tricks, each with a HIDDEN* marker word, and one visible control
line. None of the hidden lines may reach the body; every one must be listed.
"""
import re
from pathlib import Path

import pytest

import lib.pdf as pdf
from lib.pdf import convert_pdf_with_summary, visibility

_ADV = Path(__file__).resolve().parent / "fixtures" / "hidden_text" / "adv.pdf"
_MARKERS = ["HIDDENMODE3", "HIDDENWHITE", "HIDDENLIGHT", "HIDDENTINY", "HIDDENOFFPAGE", "HIDDENOFFRIGHT",
            "HIDDENUNDERIMAGE", "HIDDENUNDERBOX", "HIDDENCLIPPED", "HIDDENSAMECOLOR", "HIDDENOPACITY0"]
_HEADING = "## Text present in the PDF but not visible on the page (removed)"


@pytest.fixture(scope="module")
def adv():
    return convert_pdf_with_summary(_ADV)


def test_no_hidden_text_in_body(adv):
    md, _, _ = adv
    body, _, listing = md.partition(_HEADING)
    assert listing, "the hidden text is listed"
    assert "VISIBLECONTROL" in body
    assert re.findall(r"HIDDEN\w+", body) == []


def test_every_hidden_line_listed(adv):
    md, _, _ = adv
    listing = md.partition(_HEADING)[2]
    for m in _MARKERS:
        assert m in listing, m
    # quoted in code fences, each with its page, box and reason
    assert listing.count("<!-- tomd:hidden page=1 bbox=") == 10
    for line in listing.splitlines():
        if line.startswith("HIDDEN"):
            prev = listing.split(line)[0].rstrip("\n").splitlines()[-1]
            assert prev.startswith("```"), line


def test_summary_and_prompts(adv):
    _, prompts, summary = adv
    vis = summary["visibility"]
    assert vis["regions"] == 10
    assert set(vis["by_why"]) == {"invisible-render-mode", "opacity-0", "clipped", "tiny", "under-image",
                                  "same-colour", "under-box", "off-page"}
    assert all(set(h) >= {"page", "bbox", "why", "chars", "action", "text"} for h in vis["hidden"])
    assert sum("HIDDEN" in h["text"] for h in vis["hidden"]) == 10
    assert "## Visibility" in prompts
    assert re.search(r"hidden: text in the invisible render mode: 1 region\(s\), \d+ characters removed "
                     r"on page\(s\) 1", prompts)


def test_off(monkeypatch):
    monkeypatch.setenv("TOMD_VISIBILITY", "0")
    md, _, summary = convert_pdf_with_summary(_ADV)
    assert _HEADING not in md
    assert "HIDDENMODE3" in md


def test_duplicate_of_visible_text_kept():
    """an invisible copy printed over the same visible line hides nothing"""
    import fitz
    doc = fitz.open()
    p = doc.new_page()
    p.insert_text((72, 100), "Visible words printed twice", fontsize=11)
    p.insert_text((72, 100), "Visible words printed twice", fontsize=11, render_mode=3)
    assert visibility.classify(p) == []


def test_fence_longer_than_backticks():
    assert visibility._fence("a ``` b") == "````"
    assert visibility._fence("plain") == "```"


def test_unreadable_text_layer_is_never_empty(monkeypatch):
    """no readable text and no graphic pages (n2926): a loud warning, not an empty file"""
    monkeypatch.setattr(pdf, "is_readable", lambda text: False)
    md, prompts, summary = convert_pdf_with_summary(_ADV)
    assert "why=unreadable-text-layer" in md
    assert "tomd warning" in md
    assert prompts and "Not converted" in prompts
    assert summary["confidence"]["value"] == 0.0
    assert summary["not_converted"]["why"] == "unreadable-text-layer"


def test_transparent_text_over_an_image_kept():
    """macOS draws an emoji as an image under a transparent copy of the character"""
    import fitz
    doc = fitz.open()
    p = doc.new_page()
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 10, 10), False)
    pix.set_rect(pix.irect, (0, 160, 0))
    p.insert_image(fitz.Rect(70, 88, 84, 102), pixmap=pix)
    p.insert_text((72, 100), "X", fontsize=11, fill_opacity=0.0)
    p.insert_text((100, 100), "Visible words", fontsize=11)
    assert visibility.classify(p) == []

