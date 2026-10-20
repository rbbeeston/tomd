"""Stage 2: a level per dimension from a table's metadata (dimensions.py)."""

from lib.pdf.dimensions import dimensions, weak_note


def test_weak_dimension_named_with_its_reason():
    d = dimensions({"relations": {"kinds": ["rows merged: a drawn rule inside one row"]},
                    "verified": "ok", "witness": {"props": {"rows": ["paths", "words"], "cols": ["words"]}}})
    assert d["rows"]["level"] == "weak"
    assert d["columns"]["level"] == "ok"
    assert "rows (rows merged" in weak_note(d)


def test_strong_needs_two_information_types():
    d = dimensions({"verified": "ok", "witness": {"props": {"rows": ["paths", "words"], "cols": ["paths", "words"],
                                                           "members": ["words"]}}})
    assert d["rows"]["level"] == "strong" and d["columns"]["level"] == "strong"
    assert d["cells"]["level"] == "ok"
    assert weak_note(d) == ""


def test_verify_reason_and_open_extent():
    d = dimensions({"verified": "page 3: word-outside-cells", "witness": {"extent": "open"}})
    assert d["cells"]["level"] == "weak"
    assert set(d["cells"]["why"]) == {"verify: word-outside-cells", "may continue on the next page"}
