"""Record-pattern reader: line kinds and periodic runs (records.py)."""

from lib.pdf.records import line_kind, periodic_runs


def test_line_kinds():
    assert line_kind("P0843") == "id" and line_kind("[expr.add]") == "id"
    assert line_kind("18.8") == "num" and line_kind("2024-10-16") == "date"
    assert line_kind("Voters Room") == "word" and line_kind("std::move(x);") == "code"
    assert line_kind("P0843 32") == "mixed"


def test_periodic_run_is_records_with_the_period_as_columns():
    kinds = ["word"] * 3 + ["id", "num", "num"] * 4 + ["word"]
    start, k, n = periodic_runs(kinds)[0]
    assert (start, k, n) == (3, 3, 4)


def test_one_kind_is_not_records():
    assert periodic_runs(["word"] * 12) == []
