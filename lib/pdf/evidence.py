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
