"""LLM repair may not re-row code blocks (llmrepair.code_guard)."""
from tomd.lib.pdf.llmrepair import code_guard
from tomd.lib.pdf.types import Span


def code(*lines):
    out = []
    for i, ln in enumerate(lines):
        if i:
            out.append(Span(text="\n"))
        out.append(Span(text=ln, monospace=True))
    return out


def plain(t):
    return [Span(text=t)]


FIRST = [[plain("a.c"), plain("b.c")],
         [code("#include <x>", "int main() {", "}"), code("#include <y>", "int f() {", "}")]]


def test_one_row_per_code_line_alone_is_not_rejected():
    # a split without line numbers can be a correct repair of rows packed into one cell
    split = [[plain("a.c"), plain("b.c")]] + [[code(a), code(b)] for a, b in
                                              (("#include <x>", "#include <y>"), ("int main() {", "int f() {"), ("}", "}"))]
    assert code_guard(FIRST, split) == ""


def test_added_line_number_column_is_rejected():
    rows = [[plain("a.c"), plain(""), plain("b.c")]] + [[code(a), plain(str(i)), code(b)] for i, (a, b) in
                                                         enumerate((("x", "y"), ("p", "q"), ("r", "s")), 1)]
    assert code_guard(FIRST, rows) == "line-numbers-added"


def test_repair_keeping_code_blocks_passes():
    same = [[plain("a.c"), plain("b.c")], [code("#include <x>", "int main() {", "}"), code("#include <y>", "int f() {", "}")]]
    assert code_guard(FIRST, same) == ""


def test_prose_tables_are_not_affected():
    first = [[plain("x"), plain("y")], [plain("one"), plain("two")]]
    rep = [[plain("x"), plain("y")], [plain("one"), plain("t")], [plain(""), plain("wo")]]
    assert code_guard(first, rep) == ""
