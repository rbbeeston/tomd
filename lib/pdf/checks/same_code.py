"""Meaning: the largest code-pair similarity recorded in the area (weighted
by size where it was computed; one-line blocks abstain upstream)."""
from . import Check


def run(ctx) -> dict:
    return {"same_code": float(ctx.area.get("same_code") or 0.0)}


CHECK = Check("same_code", ("region", "content"), "meaning", 0, False, run)
