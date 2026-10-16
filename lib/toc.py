"""Table of Contents detection.

Format-agnostic: operates on plain strings and returns indices.
No dependency on PDF or HTML converter types.
"""

import bisect
import logging
import re

from . import SECTION_NUM_PREFIX_RE
from .similarity import similar

_log = logging.getLogger(__name__)

_TRAILING_PAGE_NUM_RE = re.compile(r"\s+\d{1,4}\s*$")
_DOT_LEADER_RE = re.compile(r"\s*(?:[.·]\s*){2,}")

_TOC_LABELS = frozenset({
    "table of contents",
    "contents",
})

_WHITESPACE_RE = re.compile(r"\s+")

_MIN_TOC_RUN = 3
_MAX_GAP = 3
_MAX_FUZZY_HEADINGS = 200


def _first_line(text: str) -> str:
    """Extract and strip the first line of a multi-line string."""
    return text.split("\n")[0].strip()


def _normalize_toc_entry(text: str) -> str:
    """Normalize text for TOC comparison.

    Strips trailing page numbers, dot leaders, section number prefixes.
    Collapses whitespace, lowercases.
    """
    text = _first_line(text)
    text = _DOT_LEADER_RE.sub(" ", text)
    text = _TRAILING_PAGE_NUM_RE.sub("", text)
    text = SECTION_NUM_PREFIX_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text).strip().lower()
    return text


def _is_toc_label(text: str) -> bool:
    """Check if text is a TOC heading label."""
    normalized = text.strip().lower()
    normalized = _WHITESPACE_RE.sub(" ", normalized)
    return normalized in _TOC_LABELS


def find_toc_indices(
    texts: list[str],
    headings: set[str],
    structural_hints: list[bool] | None = None,
) -> set[int]:
    """Return indices of entries that form a Table of Contents.

    texts: ordered list of section texts from the document
    headings: set of known heading texts to match against
    structural_hints: optional per-section booleans marking entries that
        look like TOC entries by structure (standalone page number on the
        second line at a consistent x position). Used as a fallback when
        headings is empty, e.g. in headingless wording-only papers.

    Both texts and headings are normalized before comparison. An entry
    matches only if a heading it names occurs at a later index in texts.
    Detects runs of 3+ consecutive matches. Also includes any "Table of Contents" label
    immediately preceding a run.
    """
    if not texts:
        return set()
    if not headings and not structural_hints:
        return set()

    norm_headings = {_normalize_toc_entry(h) for h in headings}
    norm_headings.discard("")

    # Fast exact-match set covers the common case; fuzzy matching only
    # runs on the residual. Without this, O(sections * headings) calls
    # to similar() make large documents (2000+ pages) hang.
    _exact_set = frozenset(norm_headings)

    # A TOC entry points forward: the heading it names must appear again
    # later in the document. When headings are collected from the document
    # itself, every real heading trivially matches its own text, so without
    # this check a paper with no TOC has its leading sections stripped.
    norm_texts = [_normalize_toc_entry(t) for t in texts]
    positions: dict[str, list[int]] = {}
    for j, norm in enumerate(norm_texts):
        if norm in _exact_set:
            positions.setdefault(norm, []).append(j)

    def _next_after(norm: str, i: int) -> int:
        pos = positions.get(norm, ())
        k = bisect.bisect_right(pos, i)
        return pos[k] if k < len(pos) else -1

    def _target(i: int) -> int:
        """Index of the later heading that entry i names, or -1."""
        norm = norm_texts[i]
        if not norm:
            return -1
        j = _next_after(norm, i)
        if j >= 0:
            return j
        if len(norm_headings) > _MAX_FUZZY_HEADINGS:
            return -1
        best = -1
        for h in positions:
            if h != norm and similar(norm, h):
                j = _next_after(h, i)
                if j >= 0 and (best < 0 or j < best):
                    best = j
        return best

    targets = [-1] * len(texts)
    matches = []
    for i in range(len(texts)):
        if norm_headings:
            targets[i] = _target(i)
            matches.append(targets[i] >= 0)
        else:
            matches.append(
                bool(structural_hints
                     and i < len(structural_hints)
                     and structural_hints[i])
            )

    def _first_run() -> list[int]:
        # Everything before the first match is pre-TOC (title, metadata)
        first_match = next((i for i, m in enumerate(matches) if m), -1)
        if first_match < 0:
            return []
        run: list[int] = []
        seen_first_lines: set[str] = set()
        gap = 0
        for i in range(first_match, len(matches)):
            if matches[i]:
                first_line = _first_line(texts[i]).lower()
                if first_line in seen_first_lines:
                    break
                seen_first_lines.add(first_line)
                if gap > 0:
                    run.extend(range(i - gap, i))
                gap = 0
                run.append(i)
            else:
                gap += 1
                if gap > _MAX_GAP:
                    break
        return run

    run_indices = _first_run()
    if norm_headings:
        # A TOC names headings that come after it. Fuzzy matching can pair
        # a heading with a similarly named sibling inside the run itself
        # (e.g. "foo<T>" then "foo_in<T>"); such entries are body, not TOC.
        # Drop them and rebuild the run until it is stable.
        while run_indices:
            end = max(run_indices)
            inside = [i for i in run_indices if matches[i] and targets[i] <= end]
            if not inside:
                break
            for i in inside:
                matches[i] = False
            run_indices = _first_run()

    matched = [i for i in run_indices if matches[i]]
    if norm_headings and len(matched) >= _MIN_TOC_RUN:
        # A TOC is denser than the headings it lists, which have body text
        # between them. A run whose targets are no more spread out than the
        # run itself is a repeated block of content, not a TOC.
        hit = [targets[i] for i in matched]
        if max(hit) - min(hit) <= max(matched) - min(matched):
            _log.debug("TOC candidate rejected: targets not spread out")
            matched = []

    toc_indices: set[int] = set()
    if len(matched) >= _MIN_TOC_RUN:
        toc_indices = set(run_indices)
        _log.debug("TOC block: %d entries (%d matched)",
                    len(run_indices), len(matched))

    # Include "Table of Contents" / "Contents" label before the block
    if toc_indices:
        first = min(toc_indices)
        prev = first - 1
        if prev >= 0 and _is_toc_label(_first_line(texts[prev])):
            toc_indices.add(prev)
            _log.debug("TOC label at index %d", prev)

    if toc_indices:
        _log.info("Detected TOC: %d entries detected", len(toc_indices))

    return toc_indices
