"""Tests for lib.toc."""

from lib.toc import find_toc_indices
from lib.pdf.types import Span, Line, Block, Section, SectionKind

# Body headings the TOC entries point at; a TOC entry only counts when the
# heading it names appears again later in the document.
_BODY = ["Abstract", "Abstract text.", "Introduction", "Intro text.",
         "Motivation", "Motivation text."]


def test_find_toc_strips_dot_leaders():
    texts = ["Abstract ......... 5", "Introduction", "Motivation"] + _BODY
    headings = {"abstract", "introduction", "motivation"}
    indices = find_toc_indices(texts, headings)
    assert 0 in indices


def test_find_toc_strips_spaced_dot_leaders():
    """Regression (p2034r6): LaTeX-style ". . . ." leaders, page elsewhere."""
    texts = ["Contents", "Abstract . . . . . . . .", "Introduction . . . . .",
             "Motivation . . . . . . 3"] + _BODY
    headings = {"Contents", "Abstract", "Introduction", "Motivation"}
    assert find_toc_indices(texts, headings) == {0, 1, 2, 3}


def test_find_toc_strips_trailing_page_number():
    texts = ["Abstract 42", "Introduction 15", "Motivation 22"] + _BODY
    headings = {"abstract", "introduction", "motivation"}
    indices = find_toc_indices(texts, headings)
    assert 0 in indices


def test_find_toc_strips_section_prefix():
    texts = ["2.1 Introduction", "2.2 Motivation", "2.3 Design",
             "Introduction", "x", "Motivation", "y", "Design"]
    headings = {"introduction", "motivation", "design"}
    indices = find_toc_indices(texts, headings)
    assert 0 in indices


def test_find_toc_case_insensitive():
    texts = ["ABSTRACT", "INTRODUCTION", "MOTIVATION"] + _BODY
    headings = {"abstract", "introduction", "motivation"}
    indices = find_toc_indices(texts, headings)
    assert 0 in indices


def test_find_toc_collapses_whitespace():
    texts = ["Lexical   Scope", "Overload   Sets", "Module   Units",
             "Lexical Scope", "x", "Overload Sets", "y", "Module Units"]
    headings = {"lexical scope", "overload sets", "module units"}
    indices = find_toc_indices(texts, headings)
    assert 0 in indices


def test_find_toc_basic_run():
    texts = ["Abstract", "Introduction", "Motivation", "Body text here"] + _BODY
    headings = {"Abstract", "Introduction", "Motivation"}
    indices = find_toc_indices(texts, headings)
    assert 0 in indices
    assert 1 in indices
    assert 2 in indices
    assert 3 not in indices


def test_find_toc_gap_bridging():
    texts = ["Abstract", "non-match", "Introduction", "Motivation"] + _BODY
    headings = {"Abstract", "Introduction", "Motivation"}
    indices = find_toc_indices(texts, headings)
    assert 1 in indices


def test_find_toc_too_few_matches():
    texts = ["Abstract", "Introduction", "Abstract", "Introduction"]
    headings = {"Abstract", "Introduction"}
    indices = find_toc_indices(texts, headings)
    assert len(indices) == 0


def test_find_toc_duplicate_stops_scan():
    texts = ["Abstract", "Introduction", "Motivation",
             "Abstract"]
    headings = {"Abstract", "Introduction", "Motivation"}
    indices = find_toc_indices(texts, headings)
    assert 3 not in indices


def test_find_toc_label_included():
    texts = ["Table of Contents", "Abstract", "Introduction", "Motivation"] + _BODY
    headings = {"Abstract", "Introduction", "Motivation"}
    indices = find_toc_indices(texts, headings)
    assert 0 in indices


def test_find_toc_ignores_document_own_headings():
    """Regression (p2721r1): headings collected from the document match
    their own text. A paper with no TOC must keep its leading sections."""
    texts = ["Deprecating function in C++29", "Abstract", "Revisions",
             "R1: Retargeting paper to C++29.", "Motivation",
             "As function was incompatible with noexcept...",
             "Previous Polls", "Impact on the Standard", "Proposed Wording"]
    headings = {"Deprecating function in C++29", "Abstract", "Revisions",
                "R1: Retargeting paper to C++29.", "Motivation",
                "Previous Polls", "Impact on the Standard",
                "Proposed Wording"}
    assert find_toc_indices(texts, headings) == set()


def test_find_toc_real_toc_with_own_headings():
    """A real TOC is still stripped when headings come from the body."""
    texts = ["Title", "Contents",
             "1 Abstract ..... 1", "2 Motivation ..... 2", "3 Design ..... 4",
             "1 Abstract", "Abstract text.", "2 Motivation", "Why.",
             "3 Design", "How."]
    headings = {"1 Abstract", "2 Motivation", "3 Design"}
    assert find_toc_indices(texts, headings) == {1, 2, 3, 4}


def test_find_toc_ignores_repeated_block():
    """Regression (p1112r4): a block of content extracted twice is not a TOC
    of its second copy."""
    block = ["Interaction", "para a", "para b", "Why", "para c",
             "Details", "para d"]
    texts = ["Title", "Intro", "body"] + block + block
    headings = {"Title", "Intro", "Interaction", "Why", "Details"}
    assert find_toc_indices(texts, headings) == set()


def test_find_toc_ignores_fuzzy_sibling_headings():
    """Regression (p3955r2): similarly named consecutive headings fuzzy-match
    each other; a run whose targets lie inside itself is not a TOC."""
    texts = ["Proposed Design", "exit_scope_sender<Sender>", "desc a",
             "exit_scope_sender_in<Sender, Env...>", "desc b",
             "enter_scope_sender<Sender>", "desc c",
             "enter_scope_sender_in<Sender, Env...>", "desc d",
             "Wording", "more text"]
    headings = {"Proposed Design", "exit_scope_sender<Sender>",
                "exit_scope_sender_in<Sender, Env...>",
                "enter_scope_sender<Sender>",
                "enter_scope_sender_in<Sender, Env...>", "Wording"}
    assert find_toc_indices(texts, headings) == set()


def test_find_toc_empty_inputs():
    assert find_toc_indices([], set()) == set()
    assert find_toc_indices(["x"], set()) == set()
    assert find_toc_indices([], {"x"}) == set()


# ---------------------------------------------------------------------------
# Structural hints fallback (headingless wording papers)
# ---------------------------------------------------------------------------

def _make_toc_section(title: str, page: str, x: float = 400.0) -> "Section":
    """Build a Section whose text has a bare page number on the second line."""
    page_span = Span(text=page, bbox=(x, 0, x + 20, 10))
    page_line = Line(spans=[page_span])
    title_span = Span(text=title)
    title_line = Line(spans=[title_span])
    return Section(
        kind=SectionKind.WORDING_ADD,
        text=f"{title}\n{page}",
        lines=[title_line, page_line],
    )


def _hints(sections) -> "list[bool]":
    from lib.pdf.__init__ import _toc_structural_hints
    return _toc_structural_hints(sections)


class TestStructuralTocHints:
    def test_basic_run_detected(self):
        secs = [
            _make_toc_section("Introduction", "5"),
            _make_toc_section("Motivation", "8"),
            _make_toc_section("Design", "12"),
        ]
        hints = _hints(secs)
        indices = find_toc_indices(
            [s.text for s in secs], set(), hints)
        assert {0, 1, 2} == indices

    def test_too_few_entries_not_detected(self):
        secs = [_make_toc_section("A", "1"), _make_toc_section("B", "2")]
        hints = _hints(secs)
        indices = find_toc_indices([s.text for s in secs], set(), hints)
        assert len(indices) == 0

    def test_non_toc_section_excluded(self):
        body = Section(kind=SectionKind.PARAGRAPH,
                       text="This is body text with no page number.")
        secs = [
            _make_toc_section("Introduction", "5"),
            _make_toc_section("Motivation", "8"),
            _make_toc_section("Design", "12"),
            body,
        ]
        hints = _hints(secs)
        indices = find_toc_indices([s.text for s in secs], set(), hints)
        assert 3 not in indices

    def test_headings_present_ignores_structural_hints(self):
        """When headings are non-empty the structural fallback is not used."""
        secs = [_make_toc_section("X", "1"), _make_toc_section("Y", "2")]
        # Normally 2 entries would not form a TOC via structural hints.
        # With headings supplied they should also not form a TOC (too few).
        hints = _hints(secs)
        indices = find_toc_indices(
            [s.text for s in secs], {"X", "Y"}, hints)
        assert len(indices) == 0

    def test_outlier_x_position_excluded_from_hints(self):
        """A candidate whose x differs from the cluster is not marked as a hint."""
        from lib.pdf.__init__ import _toc_structural_hints, _TOC_X_TOLERANCE
        normal_x = 400.0
        outlier_x = normal_x + _TOC_X_TOLERANCE + 20.0
        secs = [
            _make_toc_section("A", "1", x=normal_x),
            _make_toc_section("B", "2", x=normal_x),
            _make_toc_section("C", "3", x=outlier_x),
        ]
        hints = _toc_structural_hints(secs)
        assert hints[0] is True
        assert hints[1] is True
        assert hints[2] is False


def test_exact_match_skips_fuzzy_on_large_heading_set():
    """When headings exceed _MAX_FUZZY_HEADINGS, only exact matches are used."""
    headings = {f"Section {i} body" for i in range(300)}
    texts = ["Section 0 body", "Section 1 body", "Section 2 body",
             "Section 3 body", "Body paragraph", "Section 5 body",
             "Section 0 body", "a", "Section 1 body", "b",
             "Section 2 body", "c", "Section 3 body"]
    result = find_toc_indices(texts, headings)
    assert 0 in result
    assert 1 in result
    assert 2 in result
    assert 3 in result


def test_large_toc_completes_quickly():
    """Performance guard: 1000 sections x 500 headings must finish in < 2s."""
    import time
    headings = {f"Heading {i}" for i in range(500)}
    texts = [f"Heading {i % 500}" for i in range(1000)]
    t0 = time.monotonic()
    find_toc_indices(texts, headings)
    elapsed = time.monotonic() - t0
    assert elapsed < 2.0, f"TOC detection took {elapsed:.1f}s, expected < 2s"
