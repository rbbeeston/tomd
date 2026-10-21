"""Content plausibility checks (checks/plausible.py)."""

from lib.pdf.checks.plausible import column_type, duplication, plausibility, poll_counts, sequence_order


def test_sequence_out_of_order_and_ordered():
    rows = [["Meeting", "Notes"], ["2022.3", "a"], ["2023.1", "b"], ["2022.1", "c"], ["2023.3", "d"], ["2024.1", "e"],
            ["2024.2", "f"]]
    assert sequence_order(rows)
    assert not sequence_order([["#", "x"]] + [[str(i), "y"] for i in range(1, 8)])


def test_poll_counts():
    assert poll_counts([["SF", "F", "N", "A", "SA"], ["3", "4", "Neutral", "1", "0"]])
    assert not poll_counts([["SF", "F", "N", "A", "SA"], ["3", "4", "2", "1", "0"]])


def test_column_type_prose_in_numbers():
    rows = [["n", "v"]] + [["a", str(i)] for i in range(5)] + [["b", "this cell is a whole sentence"]]
    assert column_type(rows)


def test_duplication_and_clean():
    assert duplication([["a", "the same long text here"], ["b", "the same long text here"]])
    assert plausibility([["Name", "Value"], ["alpha", "1"], ["beta", "2"]]) == []
