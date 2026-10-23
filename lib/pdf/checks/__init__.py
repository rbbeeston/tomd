"""The scan's checks: one file each, loaded in a fixed order.

Every check declares its name, the level(s) it serves, the kind of
information it reads (stage 0: same-type checks are not independent
witnesses), a cost tier and whether it is optional (network or money), and
a function from the level's input to evidence items (feature -> value).
Checks never change a grid; what they return goes into the evidence record
and the scan's decision through the core.

The registry is explicit and ordered (cheapest and most decisive first, as
the effectiveness ledger ranks them), not filesystem order. Checks the ledger
rates least effective (word gaps, footprint, caption: little unique
contribution, about 30 of the scan's 78 ms per paper) form a last-resort
tier, run only while an area is undecided; TOMD_SCAN_FULL=1 runs everything
(training data and the ledger). Any check can be
switched off: TOMD_CHECKS_OFF=name,name - the same switch the ledger uses to
measure what each check contributes.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable

LEVELS = ("document", "region", "rows", "columns", "cells", "content")
INFO = ("words", "paths", "tree", "meaning", "pixels", "document", "record")


@dataclass(frozen=True)
class Check:
    name: str
    levels: tuple[str, ...]
    info: str
    cost: int                       # 0 = microseconds .. 3 = network / model call
    optional: bool
    run: Callable[["AreaContext"], dict]
    tier: int = 1                   # 1 = effective (ledger); 2 = last resort, run only while undecided


@dataclass
class AreaContext:
    """What a region-level check may look at."""
    page: object                    # the fitz page
    area: dict                      # scan.areas() entry: page, bbox, cues, excl, readings, same_code
    generator: str
    doc_tagged: bool
    measure: object = None          # docmeasure.DocMeasure (level 0)
    cache: dict = field(default_factory=dict)


def disabled() -> set[str]:
    return {n.strip() for n in os.environ.get("TOMD_CHECKS_OFF", "").split(",") if n.strip()}


def registry() -> list[Check]:
    from . import caption, coherence, data_or_format, drawn_lines, nominations, same_code, text_alignment, wordgap, footprint
    ordered = [nominations.CHECK, drawn_lines.CHECK, text_alignment.CHECK, wordgap.CHECK, footprint.CHECK,
               caption.CHECK, coherence.CHECK, same_code.CHECK, data_or_format.CHECK]
    off = disabled()
    return [c for c in ordered if c.name not in off]


def full_mode() -> bool:
    """Every check on every area (training data, the ledger): TOMD_SCAN_FULL=1."""
    return os.environ.get("TOMD_SCAN_FULL") == "1"


# Per-generator tiers (the ledger computed within each generator family on the development
# sets, work/ledger_gen_*.txt): a last-resort check is effective for a family - unique AUC
# >= 0.005 and more decisions fixed than harmed, in a family of 200+ areas - and runs in
# tier 1 there. Families not listed use the global tiers.
GENERATOR_TIER = {
    "LibreOffice": {"wordgap": 1},          # unique +0.0218, fixes 3 / harms 0 (225 areas)
    "ReportLab": {"wordgap": 1},            # unique +0.0141, fixes 10 / harms 4 (789 areas)
    "Chrome/Skia": {"wordgap": 1},          # unique +0.0062, fixes 2 / harms 0 (210 areas)
    "other": {"footprint": 1},              # unique +0.0083, fixes 4 / harms 2 (908 areas)
}


def _tier(check: Check, generator: str) -> int:
    if os.environ.get("TOMD_GEN_TIERS") == "0":
        return check.tier
    g = generator or "unknown"
    fam = "other" if g.startswith("other") or g in ("unknown", "pypdf") else g
    return GENERATOR_TIER.get(fam, {}).get(check.name, check.tier)


def run_region_checks(ctx: AreaContext, decided: Callable[[dict], bool] | None = None) -> dict:
    """Tier 1 first; the last-resort tier only while decided(features) is False
    (or in full mode). Tiers per generator family where the family's ledger says so.
    Returns the features; "_skipped" lists the checks not run."""
    out: dict = {}
    checks = [c for c in registry() if "region" in c.levels]
    gen = getattr(ctx, "generator", "unknown")
    for check in (c for c in checks if _tier(c, gen) == 1):
        out.update(check.run(ctx))
    rest = [c for c in checks if _tier(c, gen) > 1]
    if rest and decided is not None and not full_mode() and decided(out):
        out["_skipped"] = [c.name for c in rest]
        return out
    for check in rest:
        out.update(check.run(ctx))
    return out
