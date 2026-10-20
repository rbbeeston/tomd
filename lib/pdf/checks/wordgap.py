"""Words: gaps between neighbouring words in units of the document's normal
space. Prose has uniform gaps (one space, or uniformly stretched when
justified); table lines have bimodal gaps that recur at the same x."""
from . import Check


def run(ctx) -> dict:
    import fitz
    from ..docmeasure import area_word_features
    if "words" not in ctx.cache:
        ctx.cache["words"] = area_word_features(ctx.page.get_text("words", clip=fitz.Rect(ctx.area["bbox"])),
                                                ctx.measure) if ctx.measure is not None else {"w_known": 0.0}
    return {k: v for k, v in ctx.cache["words"].items() if k.startswith("w_")}


CHECK = Check("wordgap", ("region", "rows", "columns"), "words", 1, False, run, tier=2)
