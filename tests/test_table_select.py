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

    def test_single_source_is_uncertain(self):
        out = select_tables([], [_cand("grid", _GOOD)], [], [])
        assert out[0].confidence == Confidence.UNCERTAIN
        assert "Only one table source" in out[0].metadata["table_note"]

    def test_lost_text_is_uncertain(self):
        # a page line inside the table area that no cell holds
        lost = Block(lines=[_line("delta", 52, 141)], page_num=0)
        cells = Block(lines=[ln for r in _cand("grid", _GOOD).rows for c in r for ln in c],
                      page_num=0)
        out = select_tables([self._tomd_section(_GOOD)], [_cand("rules", _GOOD)], [],
                            [cells, lost])
        assert out[0].confidence == Confidence.UNCERTAIN
        assert "conservation" in out[0].metadata["table_note"]

    def test_conserved_text_stays_high(self):
        cells = Block(lines=[ln for r in _cand("grid", _GOOD).rows for c in r for ln in c],
                      page_num=0)
        out = select_tables([self._tomd_section(_GOOD)], [_cand("rules", _GOOD)], [], [cells])
        assert out[0].confidence == Confidence.HIGH

    def test_disagreement_is_uncertain_with_all_versions(self):
        bad = [["Name", "Value"], ["alpha", "1"], ["gamma", "7"]]
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
        bad = [["Name", "Value"], ["alpha", "1"], ["gamma", "7"]]
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


class TestPartialReading:
    _ROWS = [["Name", "Kind"], ["alpha", "fast"], ["beta", "slow"], ["gamma", "slow"]]

    def _tomd_section(self, rows):
        return TestSelectTables()._tomd_section(rows)

    def test_tomd_subset_of_ruled_table_is_high(self):
        out = select_tables([self._tomd_section(self._ROWS[1:3])],
                            [_cand("rules", self._ROWS)], [], [])
        assert out[0].confidence == Confidence.HIGH

    def test_tomd_subset_with_wrong_cell_stays_uncertain(self):
        wrong = [["alpha", "fast"], ["beta", "quick"]]
        out = select_tables([self._tomd_section(wrong)], [_cand("rules", self._ROWS)], [], [])
        assert out[0].confidence == Confidence.UNCERTAIN

    def test_subset_rule_only_applies_to_ruled_tables(self):
        out = select_tables([self._tomd_section(self._ROWS[1:3])], [],
                            [_cand("tags", self._ROWS)], [])
        assert out[0].confidence == Confidence.UNCERTAIN


def test_damaged_text_layer_marks_table_uncertain_with_note():
    rows = [["Symbol", "Meaning"], ["ᵃ", "Marginal benefit"], ["ᵄ(ᵆ)", "Beneficiaries"]]
    out = select_tables([], [_cand("grid", rows)], [], [])
    assert out[0].confidence == Confidence.UNCERTAIN
    assert "damaged" in out[0].metadata["table_note"]
    assert "damaged" in emit_prompts(out)


class TestPossibleTables:
    """lib.pdf.flag: table-like text left after selection is marked, not changed."""

    def _rows(self, rows, y0=100, x0=50, col_w=120, page=0):
        return Block(lines=[_line(t, x0 + c * col_w, y0 + r * 14, page)
                            for r, row in enumerate(rows) for c, t in enumerate(row)],
                     page_num=page)

    def test_aligned_rows_are_a_region(self):
        from lib.pdf.flag import text_regions
        blk = self._rows([["Thread", "Chunks", "Output"], ["0", "0-1", "two buckets"],
                          ["1", "2-3", "one bucket"]], page=2)
        assert [r[2] for r in text_regions([blk])] == ["3 rows aligned in columns"]

    def test_contents_lines_are_not_a_region(self):
        from lib.pdf.flag import text_regions
        blk = self._rows([["Introduction", "3"], ["Design", "5"], ["Wording", "9"]], page=2)
        assert text_regions([blk]) == []

    def test_code_with_comment_column_is_not_a_region(self):
        from lib.pdf.flag import text_regions
        blk = self._rows([["int a;", "// first"], ["int b;", "// second"],
                          ["int c;", "// third"]], page=2)
        assert text_regions([blk]) == []

    def test_rejected_non_table_reading_is_not_a_region(self):
        from lib.pdf.flag import rejected_regions
        c = _cand("rules", [["1.", "first"], ["2.", "second"]])
        c.flags = ["numbered-list"]
        assert rejected_regions([c], []) == []
        c.flags = ["ragged-columns"]
        assert len(rejected_regions([c], [])) == 1

    def test_marked_section_keeps_text_and_gets_marker(self):
        from lib.pdf.flag import flag_possible_tables
        ln = _line("Thread Chunks Output", 50, 100)
        sec = Section(kind=SectionKind.PARAGRAPH, text="Thread Chunks Output", lines=[ln])
        assert flag_possible_tables([sec], [(0, (40, 90, 400, 130), "3 rows aligned", 3)]) == 1
        md = emit_markdown({}, [sec])
        assert "<!-- tomd:uncertain:" in md and "Thread Chunks Output" in md
        assert "may be a table" in emit_prompts([sec])

    def test_page_sized_box_is_not_marked(self):
        from lib.pdf.flag import flag_possible_tables
        secs = [Section(kind=SectionKind.PARAGRAPH, text=f"p{i}",
                        lines=[_line(f"p{i}", 50, 100 + 20 * i)]) for i in range(8)]
        assert flag_possible_tables(secs, [(0, (40, 90, 400, 300), "rules", 2)]) == 0


def test_lost_header_row_above_agreeing_sources_is_uncertain():
    # both sources start at "alpha"; the header sits one row above, split
    # into the table's columns, so it was lost by both
    body = [["alpha", "fast"], ["beta", "slow"], ["gamma", "slow"]]
    tomd = TestSelectTables()._tomd_section(body)
    header = Block(lines=[_line("Name", 50, 80), _line("Value", 200, 80)], page_num=0)
    cells = Block(lines=[ln for r in _cand("grid", body).rows for c in r for ln in c], page_num=0)
    out = select_tables([tomd], [_cand("rules", body)], [], [header, cells])
    assert out[0].confidence == Confidence.UNCERTAIN
    assert "lost" in out[0].metadata["table_note"]
    caption = Block(lines=[_line("Table 1 - Values", 50, 80)], page_num=0)
    out = select_tables([tomd], [_cand("rules", body)], [], [caption, cells])
    assert out[0].confidence == Confidence.HIGH


class TestBooktabsRows:
    """lib.pdf.ruled._join_wrapped_lines: booktabs rows from text lines."""

    def _rows(self, lines, mono=False, col_x=(50, 200), col_w=(120, 300)):
        # lines: list of rows of cell texts; a cell's line ends at its text width
        rows = []
        for i, r in enumerate(lines):
            row = []
            for c, t in enumerate(r):
                row.append([_line(t, col_x[c], 100 + 12 * i, mono=mono)] if t else [])
            rows.append(row)
        return rows

    def test_wrapped_cell_joins_the_row_above(self):
        from lib.pdf.ruled import _join_wrapped_lines
        long = "x" * 50                       # fills column 2 to its right edge
        rows = self._rows([["Paper", "Description"], ["P1", long], ["", "continued"],
                           ["P2", "short"]])
        out = _join_wrapped_lines(rows)
        assert [[" ".join(l.text for l in c) for c in r] for r in out] == [
            ["Paper", "Description"], ["P1", long + " continued"], ["P2", "short"]]

    def test_short_line_does_not_swallow_the_next_row(self):
        from lib.pdf.ruled import _join_wrapped_lines
        rows = self._rows([["Paper", "Description"], ["P1", "short"], ["", "next entry"],
                           ["P2", "x" * 50]])
        assert len(_join_wrapped_lines(rows)) == 4

    def test_code_body_is_one_row(self):
        from lib.pdf.ruled import _join_wrapped_lines
        rows = self._rows([["Before", "After"], ["int a;", "auto a = 0;"], ["f(a);", "f(a);"]],
                          mono=True)
        out = _join_wrapped_lines(rows)
        assert len(out) == 2 and [l.text for l in out[1][0]] == ["int a;", "f(a);"]


class TestClassCheck:
    def test_poll_with_counts(self):
        from lib.pdf.table import class_check
        assert class_check(_cand("poll", [["SF", "F", "N", "A", "SA"],
                                          ["1", "2", "3", "4", "5"]])) == "poll"

    def test_suggested_poll_with_empty_row(self):
        from lib.pdf.table import class_check
        assert class_check(_cand("poll", [["SF", "F", "N", "A", "SA"],
                                          ["", "", "", "", ""]])) == "poll"

    def test_poll_with_text_is_not_trusted(self):
        from lib.pdf.table import class_check
        assert class_check(_cand("poll", [["SF", "F", "N", "A", "SA"],
                                          ["1", "2", "3", "4", "many"]])) == ""


class TestGate:
    def test_predict_walks_the_tree(self):
        from lib.pdf.classify import predict
        tree = {"f": "vrules", "t": 1.5, "l": {"label": "not-a-table", "p": 0.8, "n": 10},
                "r": {"label": "table", "p": 0.95, "n": 40}}
        assert predict(tree, {"vrules": 3.0}) == ("table", 0.95)
        assert predict(tree, {}) == ("not-a-table", 0.8)

    def _sec(self, conf, source, reasons, check):
        sec = select_tables([], [_cand("grid", _GOOD)], [], [])[0]
        sec.confidence = conf
        sec.metadata.update(table_source=source, uncertain_reasons=reasons, class_check=check)
        return sec

    def _gate(self, monkeypatch, sec, kind, layout):
        import lib.pdf.classify as C
        monkeypatch.setattr(C, "region_features", lambda *a: ({}, []))
        from lib.pdf.classify_trees import LAYOUT_TREE
        monkeypatch.setattr(C, "predict", lambda tree, x: (layout, 0.97) if tree is LAYOUT_TREE
                            else (kind, 0.97))
        monkeypatch.delenv("TOMD_JEV", raising=False)

        class Doc:
            metadata = {}
            def xref_get_key(self, *a): return ("null", "")
            def pdf_catalog(self): return 0
        C.gate_tables(Doc(), {0: None}, [sec])

    def test_gate_makes_a_doubtful_high_table_uncertain(self, monkeypatch):
        sec = self._sec(Confidence.HIGH, "grid", [], "grid")
        self._gate(monkeypatch, sec, "not-a-table", "grid")
        assert sec.confidence == Confidence.UNCERTAIN
        assert "not a table" in sec.metadata["table_note"]

    def test_gate_trusts_a_checked_single_source_poll(self, monkeypatch):
        sec = self._sec(Confidence.UNCERTAIN, "poll", ["single-source"], "poll")
        self._gate(monkeypatch, sec, "table", "poll")
        assert sec.confidence == Confidence.HIGH
        assert sec.metadata["table_agreement"] == "class:poll"

    def test_gate_never_overrides_lost_text(self, monkeypatch):
        sec = self._sec(Confidence.UNCERTAIN, "poll", ["single-source", "conservation"], "poll")
        self._gate(monkeypatch, sec, "table", "poll")
        assert sec.confidence == Confidence.UNCERTAIN


class TestHyphenation:
    def test_paper_vocabulary_decides(self):
        import lib.pdf.emit as E
        E._LEXICON.clear()
        E._LEXICON.update({"automatically": 3, "tree-structured": 2})
        spans = [make_span("fixes it automati-"), make_span("\n"), make_span("cally")]
        assert _render_cell_spans(spans) == "fixes it automatically"
        spans = [make_span("a tree-"), make_span("\n"), make_span("structured view")]
        assert _render_cell_spans(spans) == "a tree-structured view"
        E._LEXICON.clear()

    def test_hyphen_chain_is_kept(self):
        spans = [make_span("warnings-as-"), make_span("\n"), make_span("errors")]
        assert _render_cell_spans(spans) == "warnings-as-errors"

    def test_code_is_never_dehyphenated(self):
        spans = [make_span("x = a -", monospace=True), make_span("\n"),
                 make_span("b;", monospace=True)]
        assert "<br>" in _render_cell_spans(spans)

    def test_angle_brackets_escaped_outside_code(self):
        assert _render_cell_spans([make_span("Wang <m@x.org>")]) == "Wang \\<m@x.org>"
        assert _render_cell_spans([make_span("vector<int>", monospace=True)]) == "`vector<int>`"
