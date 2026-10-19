"""Shared computation for the two layout checks (computed once per area)."""


def layout_features(ctx) -> dict:
    if "layout" not in ctx.cache:
        from ..classify import region_features
        a = ctx.area
        srcs = [s for s in a["cues"] if s in ("tags", "poll", "grid", "rules", "tomd")]
        x, _ = region_features(ctx.page, a["bbox"], srcs, [], ctx.generator, ctx.doc_tagged)
        ctx.cache["layout"] = dict(x)
    return ctx.cache["layout"]


DRAWN = ("hrules", "vrules", "row_fills", "enclosing_fill")
