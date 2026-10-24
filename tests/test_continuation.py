"""Notes on table pieces that may continue the previous page (continuation.py)."""
import fitz

from tomd.lib.pdf.continuation import annotate
from tomd.lib.pdf.types import Line, Section, SectionKind, Span


def _doc(rows_p0, rows_p1):
    doc = fitz.open()
    for rows in (rows_p0, rows_p1):
        pg = doc.new_page(width=600, height=800)
        pg.insert_text((50, 30), "Page header text", fontsize=9)      # furniture: same place each page
        for y, t in rows:
            pg.insert_text((50, y), t, fontsize=10)
    return doc


def _table(page, rows):
    cols = [[[Span(text=a, bbox=(50, y - 9, 90, y + 1))], [Span(text=b, bbox=(100, y - 9, 160, y + 1))]] for y, a, b in rows]
    lines = [Line(spans=[r[0][0], r[1][0]], bbox=(50, y - 9, 160, y + 1), page_num=page)
             for r, (y, _, _) in zip(cols, rows)]
    return Section(kind=SectionKind.TABLE, text="", lines=lines, columns=cols, page_num=page)


def test_piece_reaching_bottom_then_top_is_noted():
    doc = _doc([(60, "Intro"), (700, "US 019 x"), (760, "US 020 y")], [(60, "US 021 z"), (90, "US 022 w")])
    a = _table(0, [(700, "US 019", "x"), (760, "US 020", "y")])
    b = _table(1, [(60, "US 021", "z"), (90, "US 022", "w")])
    assert annotate(doc, [a, b]) == 1
    note = b.metadata["continues_from"]
    assert note["page"] == 1
    assert any(r.startswith("numbering continues") for r in note["reasons"])
    assert "continues_from" not in a.metadata
    assert [[s.text for c in r for s in c] for r in b.columns][0] == ["US 021", "z"]     # cells untouched


def test_piece_ending_mid_page_is_not_noted():
    doc = _doc([(60, "Intro"), (300, "A x"), (330, "B y"), (760, "Closing prose")], [(60, "C z"), (90, "D w")])
    a = _table(0, [(300, "A", "x"), (330, "B", "y")])
    b = _table(1, [(60, "C", "z"), (90, "D", "w")])
    assert annotate(doc, [a, b]) == 0
