"""Alignment and shape of the text: rows, pieces per row, aligned starts,
monospace and digit shares, size and position (the classifier's features)."""
from . import Check
from ._layout import DRAWN, layout_features


def run(ctx) -> dict:
    x = layout_features(ctx)
    return {k: v for k, v in x.items() if not k.startswith(DRAWN) and isinstance(v, (int, float))}


CHECK = Check("text_alignment", ("region",), "words", 1, False, run)
