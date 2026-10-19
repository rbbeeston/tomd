"""The region scan: check every piece that makes a table, then decide.

1. Areas: every place any scan nominated or excluded (the evidence record),
   merged per page. Nominating is not deciding; nothing nominated is lost.
2. Features per area, each with its information type (words, paths, tree,
   meaning, document): the classifier's layout features, which scans saw it
   and which rules excluded it, content checks on the best reading in the
   area (items per cell, fragments, header vs body, column shapes, first
   column as keys, shared code), and document cues (a caption nearby).
3. Likelihood that the area is a table: a logistic model fitted on the
   existing truth (scan_model.py), so it is fast and explainable; the top
   supporting and opposing features are recorded with the decision.
4. Bands: high (and two independent information types) -> may be trusted;
   middle -> build, UNCERTAIN; low -> possible-table mark; none -> recorded.
"""
from __future__ import annotations

import math
from collections import Counter



# information type of each feature family (stage 0: same-type features do not
# stack like independent witnesses)
def info_of(name: str) -> str:
    if name.startswith(("cue_paths", "excl_paths", "hrules", "vrules", "row_fills", "enclosing_fill")):
        return "paths"
    if name.startswith(("cue_tree", "excl_tree", "doc_tagged", "src_tags")):
        return "tree"
    if name.startswith(("c_", "cue_meaning", "excl_meaning", "poll_header", "same_code")):
        return "meaning"
    if name.startswith(("d_", "page0")):
        return "document"
    return "words"


_RULE_FAMILY = (("prose", "prose"), ("split-code", "split_code"), ("ragged", "ragged"), ("outranked", "outranked"),
                ("one column", "one_col"), ("too few", "too_few"), ("sections than rows", "box_words"),
                ("heading", "crosses"), ("share their code", "no_same_code"), ("comment", "comments"),
                ("furniture", "furniture"), ("sparse", "sparse"), ("toc", "toc"), ("list", "list"))
_SOURCE_INFO = {"rules": "paths", "grid": "paths", "tags": "tree", "poll": "meaning", "tomd": "words",
                "codepair": "words", "content": "words", "mark": "words"}


def _inter(a, b) -> float:
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return max(w, 0) * max(h, 0)


def _area(a) -> float:
    return max(a[2] - a[0], 0.1) * max(a[3] - a[1], 0.1)


def areas(record) -> list[dict]:
    """Nominated and excluded places, merged per page (half the smaller one overlapping)."""
    out: list[dict] = []
    for e in sorted((e for e in record.entries if e.kind in ("nominated", "excluded")),
                    key=lambda e: (e.page, e.bbox[1])):
        for a in out:
            if a["page"] == e.page and _inter(a["bbox"], e.bbox) >= 0.5 * min(_area(a["bbox"]), _area(e.bbox)):
                a["bbox"] = (min(a["bbox"][0], e.bbox[0]), min(a["bbox"][1], e.bbox[1]),
                             max(a["bbox"][2], e.bbox[2]), max(a["bbox"][3], e.bbox[3]))
                break
        else:
            a = {"page": e.page, "bbox": tuple(e.bbox), "cues": Counter(), "excl": Counter(), "scans": set()}
            out.append(a)
        if e.kind == "nominated":
            a["cues"][e.scan] += 1
            a["scans"].add(e.scan)
        else:
            fam = next((k for pat, k in _RULE_FAMILY if pat in e.rule), "other")
            a["excl"][(e.scan, fam)] += 1
    for a in out:
        a["readings"] = [r for r in record.readings if r[1] == a["page"]
                         and _inter(r[2], a["bbox"]) >= 0.5 * _area(r[2])]
        a["same_code"] = max((e.value for e in record.entries if e.kind == "feature" and e.rule == "same-code"
                              and e.page == a["page"] and _inter(e.bbox, a["bbox"]) > 0
                              and isinstance(e.value, (int, float))), default=0.0)
    return out


def area_features(page, a, generator: str, doc_tagged: bool, measure=None) -> dict:
    """Every enabled region-level check's evidence for one area (checks/)."""
    from .checks import AreaContext, run_region_checks
    return run_region_checks(AreaContext(page, a, generator, doc_tagged, measure))


def likelihood(x: dict, model: dict) -> tuple[float, list[tuple[str, float]]]:
    """P(table) and the features that pushed it most (signed contributions)."""
    z = model["bias"]
    contrib = []
    for name, (mean, scale, w) in model["weights"].items():
        v = (x.get(name, 0.0) - mean) / scale
        z += w * v
        contrib.append((name, w * v))
    contrib.sort(key=lambda t: -abs(t[1]))
    return 1.0 / (1.0 + math.exp(-max(min(z, 30), -30))), contrib[:6]


HIGH, LOW = 0.8, 0.3


def band(p: float, info_types: int) -> str:
    if p >= HIGH and info_types >= 2:
        return "trust"
    if p >= LOW + (HIGH - LOW) / 2 or (p >= HIGH):
        return "build"
    if p >= LOW:
        return "mark"
    return "none"



def run_scan(path, record, tables) -> list:
    """Score every area in the evidence record and decide by band.

    Emitted tables get their likelihood and top features in metadata; a HIGH
    table the scan rates below LOW is downgraded (reason recorded). Areas
    without a table come back as possible-table regions (page, bbox, reason,
    rows) for the build and mark bands; the rest are only recorded."""
    try:
        from .scan_model import MODEL
    except ImportError:
        return []
    import fitz
    from .types import Confidence
    out = []
    from .classify import generator as _generator
    with fitz.open(str(path)) as doc:
        generator = _generator(doc.metadata or {})
        doc_tagged = doc.xref_get_key(doc.pdf_catalog(), "StructTreeRoot")[0] != "null"
        for a in areas(record):
            page = doc[a["page"]]
            x = area_features(page, a, generator, doc_tagged, getattr(record, "doc_measure", None))
            p, top = likelihood(x, MODEL)
            info = len({info_of(n) for n, c in top if c > 0} | {_SOURCE_INFO.get(s_, "words") for s_ in a["cues"]})
            bnd = band(p, info)
            mine = [t for t in tables if t.metadata.get("region_bbox") and t.metadata["region_bbox"][0] == a["page"]
                    and _inter(t.metadata["region_bbox"][1], a["bbox"]) >= 0.3 * _area(a["bbox"])]
            record.feature("scan", a["page"], a["bbox"], "likelihood", "model", round(p, 3))
            why = ", ".join(f"{n}{'+' if c > 0 else '-'}" for n, c in top[:4])
            for t in mine:
                t.metadata["scan"] = {"p": round(p, 3), "band": bnd, "top": why}
                if t.confidence == Confidence.HIGH and p < LOW:
                    t.confidence = Confidence.UNCERTAIN
                    t.metadata.setdefault("uncertain_reasons", []).append("scan")
                    t.metadata["table_note"] = (t.metadata.get("table_note", "") +
                                                f" The region scan rates this area unlikely to be a table "
                                                f"(p={p:.2f}; {why}).").strip()
            if not mine and bnd in ("build", "mark"):
                out.append((a["page"], a["bbox"], f"the region scan rates this area a likely table "
                            f"(p={p:.2f}; {why})", max(int(x.get("nrows", 2)), 2)))
    return out
