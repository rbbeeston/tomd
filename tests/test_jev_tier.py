"""The scan's optional Jev tier: off by default; confident answers only (scan.py)."""

from lib.pdf import scan


def test_off_by_default(monkeypatch):
    monkeypatch.delenv("TOMD_JEV", raising=False)
    assert scan._jev_on() is False


def test_confident_answers_only(monkeypatch):
    import lib.pdf.classify as C
    from lib.pdf.evidence import Record

    class Page:
        pass

    monkeypatch.setattr(C, "region_features", lambda *a, **k: ({}, ["text"]))
    monkeypatch.setattr(C, "jev_table_or_not",
                        lambda paper, regions: ([("table", 0.95), ("not-a-table", 0.6), ("not-a-table", 0.97)], "jev-test"))
    area = {"page": 0, "bbox": (0, 0, 10, 10), "cues": {}}
    pending = [(area, 0.5, "", "mark", 2), (area, 0.5, "", "mark", 2), (area, 0.6, "", "build", 2),
               (area, 0.9, "", "trust", 2)]
    rec = Record()
    got = scan._jev_tier({0: Page()}, "p0000r0.pdf", pending, "LaTeX", False, rec)
    assert got == {0: "table", 2: "not-a-table"}           # 0.6 is not sure; the trusted area is not asked
    assert any(e.rule == "jev-version" and e.value == "jev-test" for e in rec.entries)
