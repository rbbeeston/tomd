"""The evidence record: what every scan saw, nominated and rejected, and why.

Amendment E (no erasure) at the region level: a scan that looks at an area and
decides "not a table" records the area, the rule that decided, and the kind of
information the rule used. Later steps (the region scan, the prompts file, the
diagnosis) read the record instead of each scan's private verdict.

One record per conversion; reset() at the start of a pipeline run.

Information types (stage 0): "words" (text positions), "paths" (drawn lines,
boxes, shading), "tree" (tagged structure), "meaning" (content kinds, poll
vocabulary, code similarity), "document" (captions, counts, generator).
"""

from __future__ import annotations

from dataclasses import dataclass, field

Box = tuple[float, float, float, float]


@dataclass
class Entry:
    kind: str                  # "nominated" | "excluded" | "feature"
    scan: str                  # which scan or check wrote it
    page: int
    bbox: Box
    rule: str                  # the rule that decided (or the feature's name)
    info: str                  # information type the rule used
    value: object = None       # a feature's value, or extra detail
    observed: bool = True      # observed on the page, or inferred


@dataclass
class Record:
    entries: list[Entry] = field(default_factory=list)
    # every candidate reading: (source, page, bbox, rows of cell text)
    readings: list[tuple] = field(default_factory=list)
    doc_measure: object = None      # level 0 (docmeasure.DocMeasure)
    # readers, checks and specialists that raised: never swallowed silently
    errors: list[dict] = field(default_factory=list)

    def nominate(self, scan: str, page: int, bbox: Box, cue: str, info: str, value=None) -> None:
        self.entries.append(Entry("nominated", scan, page, tuple(bbox), cue, info, value))

    def exclude(self, scan: str, page: int, bbox: Box, rule: str, info: str, value=None) -> None:
        self.entries.append(Entry("excluded", scan, page, tuple(bbox), rule, info, value))

    def feature(self, scan: str, page: int, bbox: Box, name: str, info: str, value, observed=True) -> None:
        self.entries.append(Entry("feature", scan, page, tuple(bbox), name, info, value, observed))

    def on_page(self, page: int, kind: str | None = None) -> list[Entry]:
        return [e for e in self.entries if e.page == page and (kind is None or e.kind == kind)]


_current = Record()


def reset() -> Record:
    global _current
    _current = Record()
    return _current


def current() -> Record:
    return _current


# exceptions that mean the code is wrong, not the PDF: the gate fails on any of them
_CODE_ERRORS = (NameError, AttributeError, TypeError, ImportError, AssertionError, SyntaxError)


def reader_error(stage: str, page, exc: BaseException) -> None:
    """Record a reader, check or specialist that raised (stage, page or None for
    the whole paper, exception type and message). Tables the failure touched drop
    to UNCERTAIN ("reader error"); the prompts note and the paper summary list it.
    TOMD_STRICT=1 re-raises instead (tests)."""
    import logging
    import os
    kind = "code" if isinstance(exc, _CODE_ERRORS) else "data"
    _current.errors.append({"stage": stage, "page": page, "type": type(exc).__name__,
                            "message": str(exc)[:300], "kind": kind})
    logging.getLogger("tomd.lib.pdf").warning("Reader error in %s%s: %s: %s", stage,
                                             "" if page is None else f" (page {page + 1})", type(exc).__name__, exc)
    if os.environ.get("TOMD_STRICT") == "1":
        raise exc
