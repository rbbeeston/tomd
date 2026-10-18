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

    def test_monospace_identifier_table_keeps_its_rows(self):
        from lib.pdf.ruled import _join_wrapped_lines
        rows = self._rows([["Alias", "Meaning"], ["vertex_t<G>", "vertex"],
                           ["edge_t<G>", "edge"], ["graph_t", "graph"]], mono=True)
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
        class Page:
            def get_text(self, *a, **k): return []
        C.gate_tables(Doc(), {0: Page()}, [sec])

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


def test_jev_calls_are_batched_and_failures_fall_back(monkeypatch):
    import lib.pdf.classify as C
    calls = []

    def fake(key, paper, regions, first):
        calls.append(len(regions))
        if first:                          # the second batch fails
            return [("", 0.0)] * len(regions), ""
        return [("table", 0.9)] * len(regions), "jev-x"
    monkeypatch.setattr(C, "_jev_key", lambda: "k")
    monkeypatch.setattr(C, "_jev_batch", fake)
    out, version = C.jev_table_or_not("p1", [(0, {}, "LaTeX", [])] * 45)
    assert calls == [30, 15] and version == "jev-x"
    assert out[:30] == [("table", 0.9)] * 30 and out[30:] == [("", 0.0)] * 15


class TestVerifyLayout:
    """lib.pdf.validate.verify_layout: the grid put back onto the page."""

    def _sec(self, rows):
        return select_tables([], [_cand("grid", rows)], [], [])[0]

    def _words(self, sec):
        # the page's words where the cells say they are
        out = []
        for row in sec.columns:
            for cell in row:
                for s in cell:
                    if s.text.strip() and s.text != "\n":
                        out.append((*s.bbox, s.text.strip(), 0, 0, 0))
        return out

    def test_consistent_grid_passes(self):
        sec = self._sec(_GOOD)
        from lib.pdf.validate import verify_layout
        assert verify_layout(sec, self._words(sec)) == ""

    def test_word_outside_every_cell_fails(self):
        sec = self._sec(_GOOD)
        from lib.pdf.validate import verify_layout
        stray = (400.0, 300.0, 430.0, 310.0, "stray", 0, 0, 0)
        assert verify_layout(sec, self._words(sec) + [stray]) == "word-outside-cells"

    def test_glued_words_fail_word_boundaries(self):
        sec = self._sec([["Name", "Value"], ["alpha beta", "1"], ["gamma", "2"]])
        from lib.pdf.validate import verify_layout
        words = self._words(sec)
        x0, y0, x1, y1 = words[2][:4]
        mid = (x0 + x1) / 2
        words[2:3] = [(x0, y0, mid, y1, "alpha", 0, 0, 0), (mid + 3, y0, x1, y1, "beta", 0, 0, 0)]
        assert verify_layout(sec, words) == ""                  # same boundaries: fine
        words[2:4] = [(x0, y0, x1, y1, "alphabeta", 0, 0, 0)]
        assert verify_layout(sec, words) == "word-boundaries"


class TestGutter:
    def _rows(self, rows, page=2):
        return Block(lines=[_line(t, 50 + 160 * c, 100 + 14 * r, page)
                            for r, row in enumerate(rows) for c, t in enumerate(row) if t],
                     page_num=page)

    def test_unruled_table_has_a_gutter(self):
        from lib.pdf.flag import gutter_regions
        blk = self._rows([["Rev.", "Date"], ["0", "2023-09-14"], ["1", "2024-01-02"],
                          ["2", "2024-05-06"]])
        assert len(gutter_regions([blk])) == 1

    def test_numbered_paragraphs_are_not_a_table(self):
        from lib.pdf.flag import gutter_regions
        blk = self._rows([["(1.1)", "Constraints: the type models the concept."],
                          ["(1.2)", "Effects: equivalent to calling the function."],
                          ["(1.3)", "Returns: a reference to the stored value."]])
        assert gutter_regions([blk]) == []

    def test_contents_with_leaders_are_not_a_table(self):
        from lib.pdf.flag import gutter_regions
        blk = self._rows([["Introduction . . . . .", "3"], ["Design . . . . . .", "5"],
                          ["Wording . . . . . .", "9"]])
        assert gutter_regions([blk]) == []


def test_ocr_tokens_short_must_match_long_may_be_fuzzy():
    from lib.pdf.ocrcheck import mismatched_tokens
    assert mismatched_tokens(["SF", "WF", "N"], "SF F N") == ["WF"]
    assert mismatched_tokens(["Description"], "Descriptlon") == []
    assert mismatched_tokens(["SF"], "") == []          # no OCR evidence, no verdict


def test_skipped_document_leaves_a_visible_trace():
    import fitz
    from lib.pdf import PipelineResult, _skip
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "SF F N A SA", fontsize=10)
    r = PipelineResult()
    _skip(r, doc, "slide deck", "# skipped\n")
    assert r.skipped and r.md.startswith("<!-- tomd:skipped:slide deck:")
    assert "1 page(s) with table candidates" in r.md and r.discards


class TestTableModel:
    def test_two_level_header_combines(self):
        from lib.pdf.tablemodel import flatten_text
        rows = [["Group", "GCC", "", "Clang", ""], ["", "v1", "v2", "v1", "v2"], ["a", "1", "2", "3", "4"]]
        spans = [{"r": 0, "c": 0, "rows": 2, "cols": 1, "kind": "header"},
                 {"r": 0, "c": 1, "rows": 1, "cols": 2, "kind": "header"},
                 {"r": 0, "c": 3, "rows": 1, "cols": 2, "kind": "header"}]
        assert flatten_text(rows, spans)[0] == ["Group", "GCC / v1", "GCC / v2", "Clang / v1", "Clang / v2"]

    def test_spanning_header_over_data_is_kept_once(self):
        from lib.pdf.tablemodel import flatten_text
        rows = [["Name", "Members", ""], ["v", "id", "value"]]
        assert flatten_text(rows, [{"r": 0, "c": 1, "rows": 1, "cols": 2, "kind": "header"}]) == rows

    def test_label_fills_down_data_kept_once(self):
        from lib.pdf.tablemodel import flatten_text
        rows = [["OS", "Ver", "Total"], ["Linux", "1", "9"], ["", "2", ""]]
        spans = [{"r": 1, "c": 0, "rows": 2, "cols": 1, "kind": "label"},
                 {"r": 1, "c": 2, "rows": 2, "cols": 1, "kind": "data"}]
        assert flatten_text(rows, spans)[2] == ["Linux", "2", ""]

    def test_marker(self):
        from lib.pdf.tablemodel import marker
        assert marker([{"r": 1, "c": 0, "rows": 3, "cols": 1, "kind": "label"}]) == \
            "<!-- tomd:merged label rows=2-4 col=1 -->"


def test_code_comparison_renders_as_fenced_blocks():
    from lib.pdf.emit import _render_code_comparison, _is_code_comparison
    nl = make_span("\n")
    before = [make_span("int f() {", monospace=True, bbox=(10, 0, 64, 10)), nl,
              make_span("return 1;", monospace=True, bbox=(22, 12, 76, 22)), nl,
              make_span("}", monospace=True, bbox=(10, 24, 16, 34))]
    after = [make_span("auto f() {", monospace=True, bbox=(110, 0, 170, 10)), nl,
             make_span("return 1;", monospace=True, bbox=(122, 12, 176, 22)), nl,
             make_span("}", monospace=True, bbox=(110, 24, 116, 34))]
    rows = [[[make_span("Before")], [make_span("After")]], [before, after]]
    assert _is_code_comparison(rows)
    md = _render_code_comparison(rows)
    assert md.startswith("<!-- tomd:table kind=code-comparison cols=2 -->")
    assert "**Before**" in md and "```cpp\nint f() {\n  return 1;\n}\n```" in md


class TestLLMRepair:
    """lib.pdf.llmrepair with the API mocked: structure only, verified."""

    WORDS = [(50, 100, 80, 110, "Name", 0, 0, 0), (200, 100, 230, 110, "Value", 0, 0, 1),
             (50, 120, 80, 130, "alpha", 0, 1, 0), (200, 120, 206, 130, "1", 0, 1, 1)]

    def _client(self, rows):
        import json as _json

        class Block:
            type = "text"
            text = _json.dumps({"rows": rows})

        class Resp:
            content = [Block()]
            stop_reason = "end_turn"
            model = "claude-opus-5-5"

            class usage:
                input_tokens, output_tokens = 1000, 50

        class Messages:
            def create(self, **kw):
                assert kw["model"] == "claude-opus-5-5"
                assert kw["messages"][0]["content"][0]["type"] == "image"
                return Resp()

        class Beta:
            messages = Messages()

        class Client:
            beta = Beta()
        return Client()

    def _sec(self):
        return select_tables([], [_cand("grid", _GOOD)], [], [])[0]

    def _run(self, rows, monkeypatch, verify=lambda s, w: ""):
        import lib.pdf.llmrepair as L
        monkeypatch.setattr(L, "_image", lambda page, bbox: "")
        sec = self._sec()
        return sec, L.repair(sec, None, (0, 0, 300, 200), self.WORDS, verify, self._client(rows))

    def test_verified_structure_is_kept(self, monkeypatch):
        sec, result = self._run([[[0], [1]], [[2], [3]]], monkeypatch)
        assert result == "verified" and sec.metadata["llm_repair"]["model"] == "claude-opus-5-5"
        assert [["".join(s.text for s in c) for c in r] for r in sec.columns] == [["Name", "Value"], ["alpha", "1"]]

    def test_left_out_or_duplicated_words_are_rejected(self, monkeypatch):
        sec, result = self._run([[[0], [1]], [[2], []]], monkeypatch)
        assert result == "rejected:word-left-out"
        sec, result = self._run([[[0], [1]], [[2], [2, 3]]], monkeypatch)
        assert result == "rejected:word-used-twice"

    def test_unknown_index_is_rejected(self, monkeypatch):
        sec, result = self._run([[[0], [1]], [[2], [9]]], monkeypatch)
        assert result.startswith("rejected:")

    def test_failed_verification_keeps_the_table(self, monkeypatch):
        sec, result = self._run([[[0], [1]], [[2], [3]]], monkeypatch, verify=lambda s, w: "cell-order")
        assert result == "rejected:cell-order" and sec.metadata["table_source"] == "grid"

    def test_disabled_without_key(self, monkeypatch):
        import lib.pdf.llmrepair as L
        monkeypatch.setenv("TOMD_LLM", "1")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert not L.llm_enabled()
