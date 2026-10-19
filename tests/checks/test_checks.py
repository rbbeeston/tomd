"""Unit tests for the scan's checks, on synthetic inputs."""
from collections import Counter

import fitz

from lib.pdf.checks import AreaContext, Check, registry
from lib.pdf.checks import caption, coherence, footprint, nominations, same_code, wordgap
from lib.pdf.docmeasure import DocMeasure, area_word_features, gap_stats


def _area(**kw):
    a = {"page": 0, "bbox": (50, 100, 400, 200), "cues": Counter(), "excl": Counter(), "readings": [],
         "same_code": 0.0}
    a.update(kw)
    return a


def test_registry_is_ordered_and_switchable(monkeypatch):
    names = [c.name for c in registry()]
    assert names[0] == "nominations" and len(names) == len(set(names))
    assert all(isinstance(c, Check) and c.info for c in registry())
    monkeypatch.setenv("TOMD_CHECKS_OFF", "wordgap,caption")
    off = [c.name for c in registry()]
    assert "wordgap" not in off and "caption" not in off and len(off) == len(names) - 2


def test_nominations_counts_information_types():
    a = _area(cues=Counter({"rules": 1, "tomd": 2}), excl=Counter({("rules", "prose"): 1}))
    x = nominations.run(AreaContext(None, a, "LaTeX", False))
    assert x["cue_paths_rules"] == 1 and x["cue_words_tomd"] == 2
    assert x["excl_paths_prose"] == 1 and x["n_info_types"] == 2


def test_caption_matches_table_captions_only():
    assert caption.has_caption("Table 3: results", "")
    assert not caption.has_caption("as the table shows", "Figure 2")


def test_same_code_reports_the_area_value():
    assert same_code.run(AreaContext(None, _area(same_code=0.42), "", False)) == {"same_code": 0.42}


def test_coherence_items_per_cell_and_keys():
    good = [["Name", "Value"], ["alpha", "1"], ["beta", "2"], ["gamma", "3"]]
    merged = [["Name", "Value"], ["alpha beta gamma", "1 2 3"], ["delta epsilon zeta", "4 5 6"],
              ["eta theta iota", "7 8 9"]]
    assert coherence.merged_share(good) == 0.0
    assert coherence.merged_share(merged) == 1.0
    assert coherence.content_features(good)["c_first_col_keys"] == 1.0


def test_word_gaps_separate_cells_from_prose():
    m = DocMeasure(left=50, right=400, justified=0.8, space={10: 2.5}, known=True)
    prose = [(50 + i * 30, 100, 77.5 + i * 30, 110, "word") for i in range(8)]        # 2.5pt gaps
    table = [(50, 120, 80, 130, "alpha"), (82.5, 120, 110, 130, "one"), (200, 120, 230, 130, "2"),
             (300, 120, 330, 130, "3")]
    assert not gap_stats(prose, m)["bimodal"] and gap_stats(prose, m)["uniform"]
    assert gap_stats(table, m)["bimodal"]
    feats = area_word_features(table + [(w[0], w[1] + 20, w[2], w[3] + 20, w[4]) for w in table], m)
    assert feats["w_recurring_gap_share"] == 1.0 and feats["f_left_inset"] == 0


def test_page_checks_on_a_synthetic_page():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((60, 90), "Table 1: synthetic")
    for i, (a, b) in enumerate((("alpha", "1"), ("beta", "2"), ("gamma", "3"))):
        page.insert_text((60, 120 + 14 * i), a)
        page.insert_text((200, 120 + 14 * i), b)
    ctx = AreaContext(page, _area(bbox=(55, 105, 260, 160)), "LaTeX", False,
                      DocMeasure(left=55, right=500, space={11: 3.0}, known=True))
    assert caption.run(ctx)["d_caption_near"] == 1.0
    w = wordgap.run(ctx)
    assert w["w_known"] == 1.0 and w["w_bimodal_share"] == 0.0     # one word per cell: no in-cell spaces
    f = footprint.run(ctx)
    assert f["f_right_inset"] > 200


def test_data_or_format_features():
    from lib.pdf.checks.data_or_format import features, likelihood_data
    labels = [["Document number:", "P1234R0"], ["Date:", "2026-01-01"], ["Audience:", "LEWG"]]
    grid = [["Name", "Count", "Mean"], ["alpha", "3", "1.5"], ["beta", "4", "2.0"], ["gamma", "5", "2.5"]]
    fl, fg = features(labels, {}), features(grid, {})
    assert fl["d_label_colon"] == 1.0 and fg["d_label_colon"] == 0.0
    assert fg["d_cols"] == 3 and fl["d_cols"] == 2
    assert likelihood_data(grid, {"hrules": 3.0}) > likelihood_data(labels, {"page0": 1.0})
