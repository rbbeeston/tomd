"""Paper-level summary: what tomd did with this paper's tables, how sure it is,
and how unlike the measured papers this one is.

The output feeds AI analysis of WG21 papers, where a trusted-but-wrong
conversion is the costly failure, so every conversion carries:
  - tables trusted (HIGH), flagged (UNCERTAIN) and marked (possible tables),
    with their pages; removed and skipped content; table types present;
  - an unfamiliarity score: how unlike the measured papers this one is
    (generator not seen in the measured sets, rare layout classes, the share
    of areas the scan left undecided, rotated text, no prose measure);
  - a paper-level confidence: the estimated chance that the paper's tables
    hold no silent error (a wrong table marked HIGH, or a table missed with
    no mark), from a model calibrated on the answer keys (paper_model.py).
    An unfamiliar paper never gets the familiar papers' figure: confidence
    is capped by unfamiliarity.

Machine-readable (result.summary, written as JSON beside the Markdown), a
short header comment in the Markdown, and a section in the prompts file.
"""
from __future__ import annotations

import math

# generators of the measured papers (dev, held-out, fresh .. fresh6)
KNOWN_GENERATORS = {"LaTeX", "Word", "Google Docs", "ReportLab", "macOS", "Typst", "pypdf", "Chrome/Skia",
                    "LibreOffice", "Ghostscript", "unknown"}
COMMON_LAYOUTS = {"poll", "grid", "rule-per-row", "tagged", "booktabs"}


def unfamiliarity(generator: str, layouts: list[str], undecided: int, areas: int,
                  rotated: bool, measured: bool, skipped: bool) -> tuple[float, list[str]]:
    """0 (like the measured papers) .. 1 (unlike them), with the reasons."""
    parts = []
    score = 0.0
    if generator not in KNOWN_GENERATORS:
        score += 0.4
        parts.append(f"generator {generator!r} not among the measured papers")
    rare = [x for x in layouts if x not in COMMON_LAYOUTS]
    if rare:
        score += min(0.2, 0.05 * len(rare))
        parts.append(f"rare layout classes: {sorted(set(rare))}")
    if areas:
        share = undecided / areas
        if share > 0.2:
            score += min(0.3, share)
            parts.append(f"{undecided} of {areas} candidate areas left undecided by the scan")
    if rotated:
        score += 0.1
        parts.append("rotated text")
    if not measured:
        score += 0.2
        parts.append("no prose measure (too little ordinary text)")
    if skipped:
        score += 0.3
        parts.append("document skipped (slide deck or standards draft)")
    return min(score, 1.0), parts


def features(s: dict) -> dict:
    """The paper-level model's inputs."""
    n = max(s["tables"]["total"], 1)
    return {"n_tables": float(s["tables"]["total"]), "share_trusted": s["tables"]["trusted"] / n,
            "share_flagged": s["tables"]["flagged"] / n, "marks": float(s["marks"]),
            "undecided": float(s["scan"]["undecided"]), "unfamiliar": s["unfamiliarity"]["score"],
            "relations": float(s["tables"]["with_violations"]), "low_scan": float(s["scan"]["low_tables"])}


def confidence(s: dict) -> dict | None:
    """The measured chance that this paper's tables hold no silent error: the
    rate on the answer keys for papers with a similar score, with its interval.
    An unfamiliar paper never gets the familiar papers' figure: it is capped
    by unfamiliarity, and the interval widens to match."""
    try:
        from .paper_model import BANDS, MODEL
    except ImportError:
        return None
    z = MODEL["bias"]
    f = features(s)
    for name, (mean, scale, w) in MODEL["weights"].items():
        z += w * ((f.get(name, 0.0) - mean) / scale)
    raw = 1.0 / (1.0 + math.exp(-max(min(z, 30), -30)))
    band = [b for b in BANDS if raw >= b["from"]][-1]
    cap = 1.0 - 0.5 * s["unfamiliarity"]["score"]
    return {"value": round(min(band["rate"], cap), 3), "low": round(min(band["low"], cap), 3),
            "high": band["high"], "band": band["rate"], "band_low": band["low"], "papers": band["n"],
            "raw": round(raw, 3), "capped": band["rate"] > cap}


def build(result, sections, evidence, generator: str) -> dict:
    tables = [s for s in sections if s.kind.value == "table"]
    trusted = [s for s in tables if s.confidence.value == "high"]
    flagged = [s for s in tables if s.confidence.value != "high"]
    marks = [s for s in sections if (s.metadata or {}).get("possible_table")]
    layouts = [((s.metadata or {}).get("gate") or {}).get("layout", "?") for s in tables]
    scan_ps = [e.value for e in (evidence.entries if evidence else []) if e.kind == "feature" and e.rule == "likelihood"]
    undecided = sum(1 for p in scan_ps if 0.3 <= p < 0.8)
    rotated = any("rotated_header" in str((s.metadata or {}).get("table_source", "")) or
                  "rotated" in str((s.metadata or {}).get("relations", "")) for s in tables)
    dm = getattr(evidence, "doc_measure", None) if evidence else None
    skipped = any(d[0] == "document" for d in (result.discards or []))
    uf, why = unfamiliarity(generator, layouts, undecided, len(scan_ps), rotated,
                            bool(dm and getattr(dm, "known", False)), skipped)
    s = {
        "tables": {"total": len(tables), "trusted": len(trusted), "flagged": len(flagged),
                   "trusted_pages": sorted({t.page_num + 1 for t in trusted}),
                   "flagged_pages": sorted({t.page_num + 1 for t in flagged}),
                   "types": dict(sorted({x: layouts.count(x) for x in set(layouts)}.items())),
                   "with_violations": sum(1 for t in tables if sum(((t.metadata or {}).get("relations") or {})
                                                                    .get("by_dimension", {}).values()))},
        "marks": len(marks), "marked_pages": sorted({m.page_num + 1 for m in marks}),
        "removed": [{"what": w, "why": y} for w, y, _ in (result.discards or [])],
        "scan": {"areas": len(scan_ps), "undecided": undecided,
                 "low_tables": sum(1 for t in tables if ((t.metadata or {}).get("scan") or {}).get("p", 1) < 0.3)},
        "unfamiliarity": {"score": round(uf, 2), "reasons": why},
        "generator": generator,
    }
    s["confidence"] = confidence(s)
    return s


def header_comment(s: dict) -> str:
    t = s["tables"]
    c = s["confidence"]
    conf = "n/a" if c is None else f"{c['value']:.2f}"
    return (f"<!-- tomd:summary tables={t['total']} trusted={t['trusted']} flagged={t['flagged']} "
            f"marked={s['marks']} confidence={conf} unfamiliarity={s['unfamiliarity']['score']:.2f} -->")


def prompts_section(s: dict) -> str:
    t = s["tables"]
    lines = ["", "## Paper summary", "",
             f"- Tables: {t['total']} ({t['trusted']} trusted on pages {t['trusted_pages'] or '-'}, "
             f"{t['flagged']} flagged on pages {t['flagged_pages'] or '-'}); possible tables marked: {s['marks']}"
             + (f" (pages {s['marked_pages']})" if s["marked_pages"] else ""),
             f"- Table types: {t['types'] or '-'}",
             "- Confidence that no table error is silent: "
             + ("not estimated" if s["confidence"] is None else
                f"{s['confidence']['value']:.2f} ("
                + ("capped for unfamiliarity; " if s["confidence"]["capped"] else "")
                + f"papers like it on the answer keys: {s['confidence']['band']:.2f}, 95% interval "
                f"{s['confidence']['band_low']:.2f}-{s['confidence']['high']:.2f}, "
                f"{s['confidence']['papers']} papers)"),
             f"- Unfamiliarity: {s['unfamiliarity']['score']:.2f}"
             + (f" ({'; '.join(s['unfamiliarity']['reasons'])})" if s["unfamiliarity"]["reasons"] else "")]
    return "\n".join(lines) + "\n"
