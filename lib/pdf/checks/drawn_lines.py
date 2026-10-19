"""Drawing: rules, vertical lines, row shading and enclosing boxes in the area."""
from . import Check
from ._layout import DRAWN, layout_features


def run(ctx) -> dict:
    x = layout_features(ctx)
    return {k: v for k, v in x.items() if k.startswith(DRAWN)}


CHECK = Check("drawn_lines", ("region",), "paths", 1, False, run)
