"""Tables inside figures get a label line naming the figure (figures.py)."""

from lib.pdf.figures import figure_label

TABLE = (100, 100, 200, 160)


def blocks(*extra):
    return [((60, 40, 540, 90), "Ordinary prose above the figure, as wide as the text column on this page.")] + list(extra)


def test_sub_caption_names_the_sub_figure():
    b = blocks(((100, 170, 200, 180), "(a) Table of actors."),
               ((220, 170, 320, 180), "(b) Table of movies."),
               ((90, 200, 500, 210), "Figure 4: Illustrative simplification of IMDB data."))
    assert figure_label(b, TABLE, 480) == "Figure 4(a): Table of actors."


def test_whole_figure_when_no_or_several_sub_captions():
    b = blocks(((90, 200, 500, 210), "Figure 2.1 — Graph models of an airline route system."))
    assert figure_label(b, TABLE, 480) == "Figure 2.1: Graph models of an airline route system."
    wide = (60, 100, 540, 160)
    b = blocks(((100, 170, 200, 180), "(a) BGL"), ((300, 170, 400, 180), "(b) NWGraph"),
               ((90, 200, 500, 210), "Figure 1: Breadth-First Search Syntax Comparison"))
    assert figure_label(b, wide, 480) == "Figure 1: Breadth-First Search Syntax Comparison"


def test_prose_between_table_and_caption_means_not_in_the_figure():
    b = blocks(((60, 170, 540, 190), "A paragraph of ordinary text that runs the full width of the text column."),
               ((90, 300, 500, 310), "Figure 3: Something drawn further down."))
    assert figure_label(b, TABLE, 480) is None


def test_a_captioned_table_is_never_labelled():
    b = blocks(((100, 82, 300, 95), "Table 2: Results."),
               ((90, 200, 500, 210), "Figure 4: A figure below the table."))
    assert figure_label(b, TABLE, 480) is None
