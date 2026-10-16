"""Tests for multi-source table selection (lib.pdf.table) and table output."""

from conftest import make_span
from lib.pdf.types import Block, Line, Section, SectionKind, Confidence, TableCandidate
from lib.pdf.table import (
    table_flags, candidates_agree, select_tables, stitch_pages,
    remove_table_regions,
)
from lib.pdf.emit import emit_markdown, emit_prompts, _render_cell_spans
from lib.pdf.qa import compute_metrics


def _line(text, x, y, page=0, mono=False):
    return Line(spans=[make_span(text, monospace=mono, bbox=(x, y, x + 6 * len(text), y + 10))],
                bbox=(x, y, x + 6 * len(text), y + 10), page_num=page)


def _cand(source, rows, page=0, x0=50, y0=100, row_h=20, col_w=150):
    """A candidate whose cells are laid out on a regular grid."""
    cells = [[[_line(t, x0 + c * col_w, y0 + r * row_h, page)] if t else []
              for c, t in enumerate(row)] for r, row in enumerate(rows)]
    bbox = (x0, y0, x0 + col_w * max(len(r) for r in rows), y0 + row_h * len(rows))
    return TableCandidate(source, cells, {page: bbox})


_GOOD = [["Name", "Value"], ["alpha", "1"], ["beta", "2"]]


class TestTableFlags:
    def _flags(self, rows):
        return table_flags(_cand("tomd", rows))

    def test_clean_table_has_no_flags(self):
        assert self._flags(_GOOD) == []

    def test_bullet_list(self):
        assert "bullet-list" in self._flags([["●", "first item"], ["●", "second item"]])

    def test_code_comment_column(self):
        rows = [["Fun fun;", "// exposition only"], ["Rcvr& rcvr;", "// exposition only"]]
        assert "code-comment-column" in self._flags(rows)

    def test_reference_list_including_glued_label(self):
        rows = [["[N2529]", "Lambda expressions"], ["http://x/n2529.pdf[N2550]", "Revision 4"]]
        assert "reference-list" in self._flags(rows)

    def test_capture_syntax_is_not_a_reference_list(self):
        rows = [["", "() const", "() mutable"], ["[x]", "a", "b"], ["[mutable x]", "c", "d"]]
        assert "reference-list" not in self._flags(rows)

    def test_two_row_toc(self):
        assert "toc-like" in self._flags([["Acknowledgments", "4"], ["References", "5"]])

    def test_single_cell_rows(self):
        rows = [["POLL:", "Modify the paper by adding"], ["a feature test macro and", ""],
                ["send it to LWG.", ""]]
        assert "single-cell-rows" in self._flags(rows)

    def test_constant_first_column(self):
        rows = [["constexpr", f"int f{i}();"] for i in range(5)]
        assert "constant-first-column" in self._flags(rows)

    def test_split_code(self):
        rows = [["A", "F::minimum_copyability =="], ["constraint_level::trivial B", "x &&"],
                ["C", "y"]]
        assert "split-code" in self._flags(rows)


class TestAgreement:
    def test_same_cells_agree(self):
        assert candidates_agree(_cand("tags", _GOOD), _cand("rules", _GOOD))

    def test_whitespace_differences_agree(self):
        other = [["Name", "Value"], ["al pha", "1"], ["beta", "2"]]
        assert candidates_agree(_cand("tags", _GOOD), _cand("rules", other))

    def test_shape_difference_disagrees(self):
        assert not candidates_agree(_cand("tags", _GOOD), _cand("rules", _GOOD[:2]))


class TestSelectTables:
    def _tomd_section(self, rows):
        c = _cand("tomd", rows)
        return Section(kind=SectionKind.TABLE, text="", page_num=0,
                       lines=[ln for r in c.rows for cell in r for ln in cell],
                       columns=[[[s for ln in cell for s in ln.spans] for cell in r] for r in c.rows])

    def test_agreeing_sources_are_high(self):
        out = select_tables([self._tomd_section(_GOOD)], [_cand("rules", _GOOD)], [], [])
        assert len(out) == 1 and out[0].confidence == Confidence.HIGH

    def test_single_source_is_high(self):
        out = select_tables([], [_cand("grid", _GOOD)], [], [])
        assert out[0].confidence == Confidence.HIGH

    def test_disagreement_is_uncertain_with_all_versions(self):
        bad = [["Name", "Value"], ["alpha", "1"]]
        out = select_tables([self._tomd_section(bad)], [_cand("rules", _GOOD)], [], [])
        assert out[0].confidence == Confidence.UNCERTAIN
        sources = [s for s, _ in out[0].metadata["table_versions"]]
        assert sources == ["rules", "tomd"]

    def test_tags_win_over_ruling_lines(self):
        other = [["Name", "Value"], ["alpha", "1"], ["gamma", "3"]]
        out = select_tables([], [_cand("grid", other)], [_cand("tags", _GOOD)], [])
        assert out[0].metadata["table_source"] == "tags"

    def test_malformed_tags_rank_below_grid(self):
        tags = _cand("tags", [["Name", "Value"], ["alpha", "1"], ["gamma", "3"]])
        tags.flags.append("tags-malformed")
        out = select_tables([], [_cand("grid", _GOOD)], [tags], [])
        assert out[0].metadata["table_source"] == "grid"

    def test_flagged_tomd_table_is_dropped(self):
        rows = [["constexpr", f"int f{i}();"] for i in range(5)]
        assert select_tables([self._tomd_section(rows)], [], [], []) == []


class TestStitchPages:
    def test_continued_table_is_joined_and_repeated_header_dropped(self):
        a = _cand("grid", _GOOD, page=0, y0=600)
        b = _cand("grid", [["Name", "Value"], ["gamma", "3"]], page=1, y0=60)
        out = stitch_pages([a, b], [])
        assert len(out) == 1
        assert out[0].text_rows() == _GOOD + [["gamma", "3"]]
        assert out[0].pages == [0, 1]

    def test_caption_between_parts_prevents_join(self):
        a = _cand("grid", _GOOD, page=0, y0=600)
        b = _cand("grid", [["Name", "Value"], ["gamma", "3"]], page=1, y0=60)
        caption = Block(lines=[_line("Table 2 - Something", 50, 700, page=0)], page_num=0)
        assert len(stitch_pages([a, b], [caption])) == 2


def test_remove_table_regions_keeps_text_outside():
    table = select_tables([], [_cand("grid", _GOOD)], [], [])
    inside = _line("alpha", 52, 121)
    outside = _line("A paragraph below the table", 50, 300)
    blocks = [Block(lines=[inside, outside], page_num=0)]
    out = remove_table_regions(blocks, table)
    assert [ln.text for b in out for ln in b.lines] == ["A paragraph below the table"]


class TestTableOutput:
    def test_cell_lines_joined_with_br_and_pipes_escaped(self):
        spans = [make_span("a || b", monospace=True), make_span("\n"), make_span("next")]
        assert _render_cell_spans(spans) == "`a \\|\\| b`<br>next"

    def test_hyphenated_word_rejoined_across_cell_lines(self):
        spans = [make_span("an effect-"), make_span("\n"), make_span("parameterized type")]
        assert _render_cell_spans(spans) == "an effect-parameterized type"

    def test_adjacent_code_spans_merge(self):
        spans = [make_span("[", monospace=True), make_span("mutable", monospace=True),
                 make_span(" x]", monospace=True)]
        assert _render_cell_spans(spans) == "`[mutable x]`"

    def test_uncertain_table_is_marked_and_prompted(self):
        bad = [["Name", "Value"], ["alpha", "1"]]
        tomd = TestSelectTables()._tomd_section(bad)
        secs = select_tables([tomd], [_cand("rules", _GOOD)], [], [])
        md = emit_markdown({}, secs)
        assert "<!-- tomd:uncertain:" in md and "| Name | Value |" in md
        prompts = emit_prompts(secs)
        assert "Table from the rules extractor (emitted)" in prompts
        assert "Table from the tomd extractor (alternative)" in prompts

    def test_uncertain_table_not_counted_by_qa(self):
        md = ("# T\n\n<!-- tomd:uncertain:L3-L5 -->\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n\n"
              "| c | d |\n| --- | --- |\n| 3 | 4 |\n")
        assert compute_metrics(md).table_count == 1


class TestPollTables:
    """lib.pdf.poll on small generated PDFs."""

    def _page(self, lines):
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        for x, y, text in lines:
            page.insert_text((x, y), text, fontsize=10)
        return page

    def _polls(self, lines):
        from lib.pdf.poll import extract_poll_tables
        return [t.text_rows() for t in extract_poll_tables(self._page(lines), 0)]

    def _header(self, y=100):
        return [(72 + 30 * i, y, t) for i, t in enumerate(["SF", "F", "N", "A", "SA"])]

    _HEAD = ["SF", "F", "N", "A", "SA"]

    def test_header_and_counts(self):
        counts = [(72 + 30 * i, 114, t) for i, t in enumerate(["11", "3", "7", "24", "35"])]
        assert self._polls(self._header() + counts) == [[self._HEAD, ["11", "3", "7", "24", "35"]]]

    def test_suggested_poll_without_counts_is_header_only(self):
        polls = self._polls(self._header() + [(72, 160, "Poll: something else entirely")])
        assert polls == [[self._HEAD]]

    def test_inline_poll_in_prose_is_ignored(self):
        assert self._polls([(72, 100, "SF F N A SA: 4 5 1 0 0")]) == []

    def test_counts_must_sit_under_the_columns(self):
        counts = [(300 + 30 * i, 114, t) for i, t in enumerate(["1", "2", "3", "4", "5"])]
        assert self._polls(self._header() + counts) == [[self._HEAD]]


def test_standalone_dash_at_cell_line_break_keeps_the_break():
    spans = [make_span('recent churn" -'), make_span("\n"), make_span("remove for C++26")]
    assert _render_cell_spans(spans) == 'recent churn" -<br>remove for C++26'


def test_text_in_table_region_but_not_in_table_is_kept():
    """Words inside a table's area that no cell captured stay as text."""
    table = select_tables([], [_cand("grid", _GOOD)], [], [])
    stray = _line("Weak Consensus", 210, 121)
    captured = _line("alpha", 52, 121)
    out = remove_table_regions([Block(lines=[captured, stray], page_num=0)], table)
    assert [ln.text for b in out for ln in b.lines] == ["Weak Consensus"]
