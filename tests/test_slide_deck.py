"""Tests for slide-deck detection in lib.pdf.__init__."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.pdf import _is_slide_deck, _is_standards_draft


def _mock_doc(pages):
    """Create a mock fitz document with given (width, height) page dimensions."""
    doc = MagicMock()
    doc.page_count = len(pages)
    mock_pages = []
    for w, h in pages:
        page = MagicMock()
        rect = MagicMock()
        rect.width = w
        rect.height = h
        page.rect = rect
        mock_pages.append(page)
    doc.__getitem__ = lambda self, i: mock_pages[i]
    return doc


class TestSlideDeckDetection:
    def test_landscape_small_is_slide_deck(self):
        doc = _mock_doc([(363, 272)] * 10)
        assert _is_slide_deck(doc) is True

    def test_portrait_letter_is_not_slide_deck(self):
        doc = _mock_doc([(612, 792)] * 10)
        assert _is_slide_deck(doc) is False

    def test_portrait_a4_is_not_slide_deck(self):
        doc = _mock_doc([(595, 842)] * 10)
        assert _is_slide_deck(doc) is False

    def test_landscape_a4_is_not_slide_deck(self):
        """A4 landscape (842x595) has width > 600, so not a slide deck."""
        doc = _mock_doc([(842, 595)] * 10)
        assert _is_slide_deck(doc) is False

    def test_empty_document(self):
        doc = _mock_doc([])
        assert _is_slide_deck(doc) is False

    def test_mixed_below_threshold(self):
        """Less than 80% landscape small pages -> not a slide deck."""
        pages = [(363, 272)] * 7 + [(612, 792)] * 3
        doc = _mock_doc(pages)
        assert _is_slide_deck(doc) is False

    def test_mixed_above_threshold(self):
        """80%+ landscape small pages -> slide deck."""
        pages = [(363, 272)] * 9 + [(612, 792)] * 1
        doc = _mock_doc(pages)
        assert _is_slide_deck(doc) is True

    def test_single_landscape_page(self):
        doc = _mock_doc([(500, 375)])
        assert _is_slide_deck(doc) is True

    def test_widescreen_presentation(self):
        """16:9 widescreen at 540x405 (common Beamer)."""
        doc = _mock_doc([(540, 405)] * 20)
        assert _is_slide_deck(doc) is True


def _titled(doc, text):
    """Give the mock's first page this text."""
    first = doc[0] if doc.page_count else None
    if first is not None:
        first.get_text = lambda *a, **k: text
    return doc


_WD = "Document Number: N5054 Working Draft Programming Languages — C++"


class TestStandardsDraftDetection:
    def test_large_working_draft_is_standards_draft(self):
        doc = _titled(_mock_doc([(612, 792)] * 250), _WD)
        assert _is_standards_draft(doc) is True

    def test_exactly_200_pages_is_standards_draft(self):
        doc = _titled(_mock_doc([(612, 792)] * 200), _WD)
        assert _is_standards_draft(doc) is True

    def test_long_paper_is_not_a_standards_draft(self):
        # p4277r0: a 233-page implementation report was skipped by page count
        doc = _titled(_mock_doc([(612, 792)] * 233),
                      "Overview and Implementation Report for P3100 Document #: P4277R0")
        assert _is_standards_draft(doc) is False

    def test_199_pages_is_not_standards_draft(self):
        doc = _titled(_mock_doc([(612, 792)] * 199), _WD)
        assert _is_standards_draft(doc) is False

    def test_small_document_is_not_standards_draft(self):
        doc = _mock_doc([(612, 792)] * 10)
        assert _is_standards_draft(doc) is False

    def test_empty_document(self):
        doc = _mock_doc([])
        assert _is_standards_draft(doc) is False
