"""Words: the area's text footprint against the prose measure: left and
right inset (cell padding), and how many lines end on the right measure
(justified prose does; cell text ends raggedly)."""
from . import Check
from .wordgap import run as _words


def run(ctx) -> dict:
    _words(ctx)                       # fills ctx.cache["words"]
    return {k: v for k, v in ctx.cache["words"].items() if k.startswith("f_")}


CHECK = Check("footprint", ("region", "document"), "words", 1, False, run, tier=2)
