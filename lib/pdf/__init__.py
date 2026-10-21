"""PDF to Markdown converter - pipeline entry point."""

import logging
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .cleanup import (get_edge_items, detect_repeating, strip_repeating,
                      cleanup_text, find_hidden_regions, strip_hidden_blocks)
from .extract import extract_mupdf, extract_spatial, collect_links, attach_links
from .mono import propagate_monospace
from .wording import classify_wording, collect_line_drawings
from .spans import normalize_spans
from .structure import compare_extractions, structure_sections
from .table import detect_tables, select_tables, remove_table_regions
from .flag import (text_regions, gutter_regions, rejected_regions, dropped_uncovered, flag_possible_tables,
                   outside_view_regions)
from .classify import gate_tables
from .codepair import find_code_pairs
from . import evidence
from .docmeasure import measure as doc_measure
from .content import content_candidates, page_hrules
from .ruled import extract_ruled_tables
from .tagged import extract_tagged_tables
from .poll import extract_poll_tables
from .wg21 import extract_metadata_from_blocks
from .emit import emit_markdown, emit_prompts
from .types import Block, Section, SectionKind, is_readable
from ..toc import find_toc_indices

__all__ = ["convert_pdf", "PipelineResult"]

_log = logging.getLogger(__name__)

_STANDALONE_PAGE_RE = re.compile(r'^\d{1,4}$')
_TOC_X_TOLERANCE = 5.0


def _toc_structural_hints(sections) -> list[bool]:
    """Mark sections that structurally resemble TOC entries.

    A section qualifies when its second non-empty text line is a bare page
    number AND its x coordinate clusters with other such candidates (the
    right-aligned page-number column). Used as a fallback for headingless
    wording papers where find_toc_indices would otherwise get an empty
    headings set.
    """
    from .types import Section as _Section  # local to avoid circular at module level

    candidates: list[tuple[int, float | None]] = []
    for i, sec in enumerate(sections):
        lines = [l.strip() for l in sec.text.split("\n") if l.strip()]
        if len(lines) >= 2 and _STANDALONE_PAGE_RE.match(lines[1]):
            x = None
            non_empty = [ln for ln in sec.lines if ln.text.strip()]
            if len(non_empty) >= 2 and non_empty[1].spans:
                x = non_empty[1].spans[0].bbox[0]
            candidates.append((i, x))

    if not candidates:
        return [False] * len(sections)

    xs = sorted(x for _, x in candidates if x is not None)
    med_x = xs[len(xs) // 2] if xs else None

    result = [False] * len(sections)
    for i, x in candidates:
        if med_x is None or x is None or abs(x - med_x) <= _TOC_X_TOLERANCE:
            result[i] = True
    return result


def _get_page0_text_colors(page) -> dict[float, float]:
    """Map y-positions to text lightness using texttrace space-color proxy.

    Type 3 fonts report black for all glyphs. Space characters (type=0)
    leak the true graphics-state fill color. Returns {rounded_y: lightness}
    where lightness is 0.0 (black) to 1.0 (white).
    """
    colors: dict[float, float] = {}
    for span in page.get_texttrace():
        if span.get("type") != 0:
            continue
        color = span.get("color")
        if color is None:
            continue
        chars = span.get("chars", [])
        if not chars:
            continue
        y = round(chars[0][2][1])
        if isinstance(color, (tuple, list)) and len(color) >= 3:
            lightness = sum(color[:3]) / 3.0
        elif isinstance(color, (int, float)):
            lightness = float(color)
        else:
            continue
        colors[y] = lightness
    return colors


_SLIDE_DECK_MAX_WIDTH = 600
_SLIDE_DECK_LANDSCAPE_FRACTION = 0.8
_STANDARDS_DRAFT_MIN_PAGES = 200


def _is_slide_deck(doc) -> bool:
    """Detect presentation / slide-deck PDFs from page geometry.

    A PDF is a slide deck when most pages are landscape and smaller
    than standard paper sizes (width < 600pt ≈ 8.3in).
    """
    if doc.page_count == 0:
        return False
    landscape_count = 0
    for pg_num in range(doc.page_count):
        r = doc[pg_num].rect
        if r.width > r.height and r.width < _SLIDE_DECK_MAX_WIDTH:
            landscape_count += 1
    return landscape_count / doc.page_count >= _SLIDE_DECK_LANDSCAPE_FRACTION


_DRAFT_TITLE = re.compile(r"\b(Working Draft|Committee Draft|Draft International Standard|"
                          r"Draft Technical Specification)\b", re.I)


def _is_standards_draft(doc) -> bool:
    """Detect standards drafts: long (>= 200 pages) and titled as a draft.

    Page count alone also skipped long papers (p4277r0, a 233-page
    implementation report, lost all 85 of its tables). A Working Draft says
    so on its first page.
    """
    if doc.page_count < _STANDARDS_DRAFT_MIN_PAGES:
        return False
    first = " ".join(doc[0].get_text().split())
    return bool(_DRAFT_TITLE.search(first))


@dataclass
class PipelineResult:
    """Full output of the PDF conversion pipeline, used for QA scoring."""
    md: str = ""
    prompts: str | None = None
    sections: list[Section] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    page_count: int = 0
    nesting_corrections: int = 0
    readable: bool = True
    skipped: bool = False
    skip_reason: str = ""
    # every content the pipeline decided to drop: (what, why, detail)
    discards: list = field(default_factory=list)


_SCAN_PAGES = 300
_POLL_LINE = re.compile(r"^\s*(SF\s+F\s+N\s+A\s+SA|F\s+N\s+A)\s*$", re.M)
_TABLE_CAPTION = re.compile(r"^\s*Table\s+\d+(\.\d+)?\b", re.M)


def _quick_table_scan(doc) -> list[int]:
    """Pages (0-based) with a poll header or a "Table N" caption; cheap."""
    pages = []
    for i in range(min(doc.page_count, _SCAN_PAGES)):
        text = doc[i].get_text()
        if _POLL_LINE.search(text) or _TABLE_CAPTION.search(text):
            pages.append(i)
    return pages


def _skip(result, doc, reason: str, prompt: str) -> None:
    """Skip converting a document, but never silently.

    The Markdown says the document was skipped and why, and a cheap scan
    reports how many pages look like they hold tables, so a wrong skip
    (p4277r0 was skipped as a Working Draft with 85 tables) is visible.
    """
    pages = _quick_table_scan(doc)
    scanned = min(doc.page_count, _SCAN_PAGES)
    where = (f"on pages {', '.join(str(p + 1) for p in pages[:20])}"
             f"{' ...' if len(pages) > 20 else ''}") if pages else ""
    note = (f"{len(pages)} page(s) with table candidates (poll headers or table captions) "
            f"in the first {scanned} of {doc.page_count} pages {where}").strip()
    _log.warning("Skipping %s (%d pages): %s", reason, doc.page_count, note)
    result.skipped = True
    result.skip_reason = reason
    result.md = f"<!-- tomd:skipped:{reason}: {note} -->\n"
    result.prompts = prompt + f"\nNot converted, so nothing below was checked: {note}.\n"
    result.discards.append(("document", reason, note))


_OWN_TABLE = re.compile(r"(?<![\w\]])Table\s+(\d+(?:\.\d+)?)\b")


def _own_table_numbers(blocks) -> int:
    """"Table N" numbers in the paper's text, not counting the standard's
    tables (lines with a [tab:...] stable name). A paper numbers its own
    tables from 1, so only the unbroken run 1..k counts (per chapter for
    "Table 2.3"); "see Table 30" alone is someone else's numbering."""
    nums = set()
    for b in blocks:
        for ln in b.lines:
            t = ln.text
            if "[tab:" in t or "tab." in t:
                continue
            nums |= set(_OWN_TABLE.findall(t))
    groups: dict[str, set[int]] = {}
    for n in nums:
        major, _, minor = n.rpartition(".")
        groups.setdefault(major, set()).add(int(minor))
    count = 0
    for got in groups.values():
        k = 1
        while k in got:
            k += 1
        count += k - 1
    return count


def _horizontal_share(page) -> float:
    lines = [ln for b in page.get_text("dict").get("blocks", []) for ln in b.get("lines", [])]
    return sum(1 for ln in lines if abs(ln["dir"][0] - 1.0) < 0.01) / max(len(lines), 1)


def _upright_page(doc, pg_num: int, keep_alive: list):
    """The page as a reader sees it.

    A page with /Rotate (LaTeX landscape tables, rotated appendices) is
    extracted in its unrotated coordinates, where its text runs vertically
    and no extractor finds lines or tables. Such a page is drawn upright
    onto a scratch page and that copy is used instead - when the copy's
    text is more horizontal than the original's. `keep_alive` holds the
    scratch documents until extraction is done.
    """
    page = doc[pg_num]
    if not page.rotation:
        return page
    import fitz
    tmp = fitz.open()
    up = tmp.new_page(width=page.rect.width, height=page.rect.height)
    up.show_pdf_page(up.rect, doc, pg_num, rotate=-page.rotation)
    if _horizontal_share(up) <= _horizontal_share(page):
        tmp.close()
        return page
    keep_alive.append(tmp)
    _log.info("Page %d is rotated %d degrees; extracting it upright", pg_num, page.rotation)
    return up


def _run_pipeline(path: Path) -> PipelineResult:
    """Run the full PDF conversion pipeline, returning all intermediate data."""
    import fitz

    path = Path(path)
    result = PipelineResult()
    result.evidence = evidence.reset()
    from .pagecache import clear as _clear_pages
    _clear_pages()
    from .llmrepair import reset_paper
    reset_paper()                       # this paper's LLM repair record (summary)
    doc = None
    try:
        doc = fitz.open(str(path))
        result.page_count = doc.page_count
        try:
            from .classify import generator as _gen
            result.generator = _gen(doc.metadata or {})
        except Exception:
            result.generator = "unknown"
        if result.page_count == 0:
            return result

        if _is_slide_deck(doc):
            _skip(result, doc, "slide deck", "# tomd - Slide Deck Detected\n\n"
                  "This PDF appears to be a presentation / slide deck. "
                  "tomd does not convert slide decks to Markdown.\n")
            return result

        if _is_standards_draft(doc):
            _skip(result, doc, "standards draft", "# tomd - Standards Draft Detected\n\n"
                  f"This PDF has {result.page_count} pages and appears to be "
                  "a standards draft. tomd is designed for technical papers.\n")
            return result

        all_mupdf_blocks = []
        all_spatial_blocks = []
        all_edge_items = []
        all_ruled_tables = []
        all_poll_tables = []

        keep_alive: list = []
        page_rules: dict = {}           # drawn horizontal rules per page, read once
        page_words: list = []
        pages = [_upright_page(doc, i, keep_alive) for i in range(result.page_count)]
        for pg_num in range(result.page_count):
            page = pages[pg_num]
            page_height = page.rect.height

            page_words.append(page.get_text("words"))
            mupdf_blocks = extract_mupdf(page, pg_num)
            spatial_blocks = extract_spatial(page, pg_num)

            edge_items = (
                get_edge_items(mupdf_blocks, pg_num, page_height)
                + get_edge_items(spatial_blocks, pg_num, page_height)
            )
            all_edge_items.append(edge_items)

            links = collect_links(doc[pg_num])
            attach_links(mupdf_blocks, links)
            attach_links(spatial_blocks, links)

            all_mupdf_blocks.extend(mupdf_blocks)
            all_spatial_blocks.extend(spatial_blocks)

            # Independent table sources, compared with detect_tables() below.
            try:
                drawings = page.get_drawings()
                page_rules[pg_num] = page_hrules(page, drawings)
                all_ruled_tables.extend(extract_ruled_tables(page, pg_num, drawings))
                all_poll_tables.extend(extract_poll_tables(page, pg_num, page_words[-1] if page_words else None))
            except Exception as e:  # never let a table source break conversion
                _log.warning("Table extraction failed on page %d: %s", pg_num, e)

        # level 0: what ordinary prose looks like in this document
        result.doc_measure = doc_measure(page_words)
        from .docmeasure import hyphenates
        result.hyphenates = hyphenates(page_words)
        result.evidence.doc_measure = result.doc_measure
        try:
            tagged_tables = extract_tagged_tables(doc)
        except Exception as e:
            _log.warning("Tagged table extraction failed: %s", e)
            tagged_tables = []

        font_counts: Counter[str] = Counter()
        for b in all_mupdf_blocks:
            for ln in b.lines:
                for s in ln.spans:
                    if s.text.strip():
                        font_counts[s.font_name.lower()] += len(s.text)
        body_fonts = {f for f, _ in font_counts.most_common(5)}

        all_hidden: set[tuple[float, float, float, float]] = set()
        for pg_num in range(result.page_count):
            all_hidden |= find_hidden_regions(pages[pg_num], body_fonts)

        page0_colors = _get_page0_text_colors(pages[0]) if result.page_count > 0 else {}

        page_drawings: dict[int, list] = {}
        for pg_num in range(result.page_count):
            drawings = collect_line_drawings(pages[pg_num])
            if drawings:
                page_drawings[pg_num] = drawings
    finally:
        if doc is not None:
            doc.close()

    if all_hidden:
        _log.info("Stripping text hidden by %d covered regions", len(all_hidden))
        result.discards.append(("hidden", f"text under {len(all_hidden)} covered region(s) "
                                "removed", ""))
        all_mupdf_blocks = strip_hidden_blocks(all_mupdf_blocks, all_hidden)
        all_spatial_blocks = strip_hidden_blocks(all_spatial_blocks, all_hidden)

    mupdf_text = "\n".join(b.text for b in all_mupdf_blocks)
    if not is_readable(mupdf_text):
        _log.warning("Extracted text is not readable (encrypted/scanned PDF?)")
        result.readable = False
        return result

    repeating = detect_repeating(all_edge_items, result.page_count)
    if repeating:
        _log.info("Stripping %d repeating header/footer patterns", len(repeating))
        result.discards.append(("headers", f"{len(repeating)} repeating header/footer "
                                "pattern(s) removed", ", ".join(sorted(map(str, repeating))[:3])[:120]))
        all_mupdf_blocks = strip_repeating(all_mupdf_blocks, repeating)
        all_spatial_blocks = strip_repeating(all_spatial_blocks, repeating)

    dominant_font = font_counts.most_common(1)[0][0] if font_counts else ""
    propagate_monospace(all_mupdf_blocks, all_spatial_blocks, dominant_font)

    wording_problems = classify_wording(all_mupdf_blocks, page_drawings)

    all_mupdf_blocks = cleanup_text(all_mupdf_blocks)
    all_spatial_blocks = cleanup_text(all_spatial_blocks)

    all_mupdf_blocks = normalize_spans(all_mupdf_blocks)
    all_spatial_blocks = normalize_spans(all_spatial_blocks)

    wg21_metadata, _ = extract_metadata_from_blocks(all_mupdf_blocks,
                                                     text_colors=page0_colors)

    tomd_tables, _ = detect_tables(all_mupdf_blocks)
    rejected_tables: list = []
    code_pairs = []
    if os.environ.get("TOMD_CODEPAIR") != "0":
        code_pairs = find_code_pairs(all_mupdf_blocks, lambda pg: page_rules.get(pg, []))
    # the shared content-first builder reads every region any reader located
    content_tables = []
    if os.environ.get("TOMD_CONTENT") != "0":
        try:
            regions = [(c.pages[0], c.bboxes[c.pages[0]])
                       for c in all_ruled_tables + tagged_tables + all_poll_tables + code_pairs
                       if len(c.pages) == 1]
            regions += [(s.page_num, (min(ln.bbox[0] for ln in s.lines), min(ln.bbox[1] for ln in s.lines),
                                      max(ln.bbox[2] for ln in s.lines), max(ln.bbox[3] for ln in s.lines)))
                        for s in tomd_tables if s.lines and len({ln.page_num for ln in s.lines}) == 1]
            import fitz
            with fitz.open(str(path)) as cdoc:
                keep: list = []
                cpages = {pg: _upright_page(cdoc, pg, keep) for pg in {pg for pg, _ in regions}}
                content_tables = content_candidates(cpages, regions, rules_by_page=page_rules)
                if os.environ.get("TOMD_RECORDS") != "0":
                    # the record-pattern reading of the same regions (records.py): an alternative only
                    from .records import records_candidates
                    content_tables += records_candidates(cpages, regions)
        except Exception as e:  # never let the builder break conversion
            _log.warning("Content builder failed: %s", e)
    table_sections = select_tables(tomd_tables, all_ruled_tables, tagged_tables,
                                   all_mupdf_blocks, all_poll_tables, rejected_tables, code_pairs,
                                   content_tables)
    if table_sections:
        _log.info("Selected %d table(s)", len(table_sections))
        try:
            import fitz
            with fitz.open(str(path)) as gdoc:
                keep_alive: list = []
                gpages = {pg: _upright_page(gdoc, pg, keep_alive)
                          for pg in {s.metadata["region_bbox"][0] for s in table_sections
                                     if "region_bbox" in s.metadata}
                          | {p for s in table_sections for p in (s.metadata.get("page_bboxes") or {})}}
                gate_tables(gdoc, gpages, table_sections, paper=Path(path).stem)
        except Exception as e:  # the gate only adjusts confidence; never fail on it
            _log.warning("Table classification failed: %s", e)
        all_mupdf_blocks = remove_table_regions(all_mupdf_blocks, table_sections)
        all_spatial_blocks = remove_table_regions(all_spatial_blocks, table_sections)
    # Table-like areas left in the text, marked uncertain once sections exist.
    dropped = dropped_uncovered(rejected_tables, table_sections)
    if dropped:
        result.discards.append(("dropped table candidates", f"{len(dropped)} reading(s) failed the "
                                "checks and no kept table covers them: " + "; ".join(dropped[:12])
                                + ("; ..." if len(dropped) > 12 else ""), ""))
    scan_regions = []
    if os.environ.get("TOMD_SCAN") != "0":
        try:
            from .scan import run_scan
            builds: list | None = [] if os.environ.get("TOMD_SCAN_BUILD") != "0" else None
            scan_regions = run_scan(path, result.evidence, table_sections, builds)
            if builds:
                built, unbuilt = _build_scan_tables(path, builds, all_mupdf_blocks)
                scan_regions += unbuilt
                if built:
                    table_sections += built
                    all_mupdf_blocks = remove_table_regions(all_mupdf_blocks, built)
                    all_spatial_blocks = remove_table_regions(all_spatial_blocks, built)
        except Exception as e:  # the scan only adds marks and doubts; never fail on it
            _log.warning("Region scan failed: %s", e)
    if os.environ.get("TOMD_FIGURES") != "0" and table_sections:
        # small tables drawn inside a figure: labelled with the figure (figures.py)
        try:
            from .figures import label_figure_tables
            with fitz.open(str(path)) as fdoc:
                label_figure_tables(fdoc, table_sections)
        except Exception as e:  # a label only; never fail on it
            _log.warning("Figure labels failed: %s", e)
    possible_tables = (scan_regions + rejected_regions(rejected_tables, table_sections)
                       + text_regions(all_mupdf_blocks) + gutter_regions(all_mupdf_blocks))

    sections = compare_extractions(all_mupdf_blocks, all_spatial_blocks)

    for ts in table_sections:
        inserted = False
        for i, sec in enumerate(sections):
            if sec.page_num > ts.page_num:
                sections.insert(i, ts)
                inserted = True
                break
            if (sec.page_num == ts.page_num and sec.lines
                    and ts.lines
                    and sec.lines[0].bbox[1] > ts.lines[0].bbox[1]):
                sections.insert(i, ts)
                inserted = True
                break
        if not inserted:
            sections.append(ts)
    flag_possible_tables(sections, possible_tables)
    if os.environ.get("TOMD_OUTSIDE") != "0":
        flag_possible_tables(sections, outside_view_regions(sections))

    has_title = "title" in wg21_metadata
    # Three metadata pathways, merged here in precedence order (last wins):
    #   1. structure._extract_metadata  - PDF section line scan (lowest precedence)
    #   2. wg21.extract_metadata_from_blocks - PDF block-level scan (wins on conflict)
    # HTML conversion uses a third pathway: html.extract.extract_metadata (DOM scan).
    structure_metadata, sections, nesting_corrections = structure_sections(
        sections, has_title=has_title)
    metadata = {**structure_metadata, **wg21_metadata}

    texts = [sec.text.split("\n")[0].strip() for sec in sections]
    heading_texts = {sec.text.split("\n")[0].strip()
                     for sec in sections if sec.kind == SectionKind.HEADING}
    structural_hints = _toc_structural_hints(sections) if not heading_texts else None
    toc_indices = find_toc_indices(texts, heading_texts, structural_hints)
    if toc_indices:
        # A selected table is never a contents entry: dropping it would lose
        # the table silently.
        removed = [s for i, s in enumerate(sections)
                   if i in toc_indices and s.kind != SectionKind.TABLE]
        if removed:
            result.discards.append(("contents", f"{len(removed)} section(s) taken for a table "
                                    "of contents", removed[0].text.split("\n")[0][:80]))
        sections = [s for i, s in enumerate(sections)
                    if i not in toc_indices or s.kind == SectionKind.TABLE]

    from . import emit as _emit
    # does this document hyphenate words at line ends? The document's own text
    # says (docmeasure.hyphenates); where it never does, a line-end hyphen in a
    # cell is the word's own ("Use-cases")
    _emit.set_hyphenating(getattr(result, "hyphenates", True))
    md = emit_markdown(metadata, sections)
    prompts = emit_prompts(sections)

    if wording_problems:
        wording_prompt = "\n\n".join(
            ["\n## Wording Detection Issues\n"] + wording_problems)
        if prompts:
            prompts += "\n" + wording_prompt
        else:
            prompts = "# tomd - Conversion Issues\n" + wording_prompt

    # what the paper's own text says about its tables: a floor, cheap to check
    expected = _own_table_numbers(all_mupdf_blocks + [Block(lines=ts.lines, page_num=ts.page_num)
                                                      for ts in table_sections if ts.lines])
    found = sum(1 for s in sections if s.kind == SectionKind.TABLE)
    if expected > found:
        result.discards.append(("tables", f"the paper numbers {expected} tables of its own "
                                f"(\"Table N\") but {found} were extracted", ""))
    if result.discards:
        lines = ["\n## Removed content\n",
                 "tomd removed this content on purpose; check it if something is missing."]
        lines += [f"- {what}: {why}" + (f" (e.g. \"{detail}\")" if detail else "")
                  for what, why, detail in result.discards]
        prompts = (prompts or "# tomd - Conversion Issues\n") + "\n".join(lines) + "\n"
    if os.environ.get("TOMD_SUMMARY") != "0":
        # the paper-level summary: what was done with the tables, how sure, how unfamiliar
        try:
            from .summary import build as build_summary, header_comment, prompts_section
            result.summary = build_summary(result, sections, result.evidence, getattr(result, "generator", "unknown"))
            comment = header_comment(result.summary)
            if md.startswith("---\n") and "\n---\n" in md[4:]:
                end = md.index("\n---\n", 4) + 5
            else:
                end, comment = 0, comment + "\n"
            at = md[:end].count("\n") + 1              # 1-based line where the comment goes
            md = md[:end] + comment + "\n" + md[end:]
            # the uncertainty markers point at line numbers: shift those after the comment
            added = comment.count("\n") + 1
            md = re.sub(r"tomd:uncertain:L(\d+)-L(\d+)",
                        lambda m: "tomd:uncertain:L%d-L%d" % tuple(int(x) + (added if int(x) >= at else 0)
                                                               for x in m.groups()), md)
            prompts = (prompts or "# tomd - Conversion Issues\n") + prompts_section(result.summary)
        except Exception as e:      # the summary describes the conversion; never fail it
            _log.warning("Paper summary failed: %s", e)
    result.md = md
    result.prompts = prompts
    result.sections = sections
    result.metadata = metadata
    result.nesting_corrections = nesting_corrections
    return result


def convert_pdf(path: Path) -> tuple[str, str | None]:
    """Convert a PDF file to Markdown.

    Returns (markdown_text, prompts_text_or_none).
    Returns ("", None) for empty or unreadable PDFs.
    Raises fitz exceptions for corrupt or inaccessible files.
    """
    r = _run_pipeline(path)
    return r.md, r.prompts


def convert_pdf_with_summary(path: Path) -> tuple[str, str | None, dict | None]:
    """convert_pdf plus the paper-level summary (summary.py): tables trusted,
    flagged and marked, confidence and unfamiliarity. Written as JSON beside
    the Markdown by the command line."""
    r = _run_pipeline(path)
    return r.md, r.prompts, getattr(r, "summary", None)


def _build_scan_tables(path, builds, blocks):
    """The scan's build band: an area likely to be a table that no reader kept
    is built by the shared content-first builder (pieces on consecutive pages
    joined by the same continuation step as every reader) and emitted
    UNCERTAIN, then gated like every table (verification, relations,
    dimensions). An area the builder cannot read as a grid, or reads as
    contents or label: value entries, stays a possible-table mark.
    Returns (sections, marks for the areas not built)."""
    import fitz
    from .emit import table_use
    from .table import _is_bad, _to_section, page_furniture, stitch_pages
    from .types import Confidence
    built, unbuilt, cands, info = [], [], [], {}
    with fitz.open(str(path)) as doc:
        keep: list = []
        pages = {pg: _upright_page(doc, pg, keep) for pg in {b[0] for b in builds}}
        for page, bbox, p, why, nrows in builds:
            reason = f"the region scan rates this area a likely table (p={p:.2f}; {why})"
            got = [c for c in content_candidates(pages, [(page, bbox)]) if not _is_bad(c)]
            if not got:
                unbuilt.append((page, bbox, reason, nrows))
                continue
            first = got[0].pages[0]
            info[(first, tuple(round(v) for v in got[0].bboxes[first]))] = (p, why, reason, bbox, nrows)
            cands.append(got[0])
        for cand in stitch_pages(cands, blocks, page_furniture(blocks)):
            first = cand.pages[0]
            p, why, reason, bbox, nrows = info[(first, tuple(round(v) for v in cand.bboxes[first]))]
            sec = _to_section(cand, Confidence.UNCERTAIN, [])
            if table_use(sec.columns) != "table":
                unbuilt.append((cand.pages[0], bbox, reason, nrows))  # contents, label: value: not tables (user)
                continue
            first = cand.pages[0]
            sec.metadata["region_bbox"] = (first, tuple(cand.bboxes[first]))
            if len(cand.pages) > 1:
                sec.metadata["page_bboxes"] = dict(cand.bboxes)
                if getattr(cand, "pieces", None):
                    sec.metadata["pieces"] = cand.pieces
            sec.metadata["uncertain_reasons"] = ["single-source", "scan-build"]
            sec.metadata["table_note"] = ("No reader kept a table here; the region scan rates the area a likely "
                                          f"table (p={p:.2f}) and the content-first builder read it.")
            sec.metadata["scan"] = {"p": p, "band": "build", "top": why}
            built.append(sec)
        if built:
            gpages = {pg: _upright_page(doc, pg, keep) for s in built
                      for pg in ([s.page_num] + list(s.metadata.get("page_bboxes") or {}))}
            gate_tables(doc, gpages, built, paper=Path(path).stem)
    return built, unbuilt
