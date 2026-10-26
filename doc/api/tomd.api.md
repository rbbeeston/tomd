# tomd API surface

68 modules, 18 classes, 215 functions, 17 methods, 119 fields.

## Contents

- [`__init__.py`](#init-py)
- [`lib/__init__.py`](#lib-init-py): ascii_escape, format_front_matter, parse_author_lines, strip_format_chars, ALLOWED_LINK_SCHEMES, DATE_RE, DOC_NUM_PATTERN, DOC_NUM_RE, EMAIL_RE, FORMAT_CHARS, FRONT_MATTER_ORDER, SECTION_NUM_PATTERN, ...
- [`lib/html/__init__.py`](#lib-html-init-py): convert_html
- [`lib/html/extract.py`](#lib-html-extract-py): detect_generator, extract_metadata, parse_html, strip_boilerplate
- [`lib/html/render.py`](#lib-html-render-py): render_body
- [`lib/pdf/__init__.py`](#lib-pdf-init-py): PipelineResult, convert_pdf, convert_pdf_with_summary, dropped_nomination_regions
- [`lib/pdf/checks/__init__.py`](#lib-pdf-checks-init-py): AreaContext, Check, disabled, full_mode, registry, run_region_checks, GENERATOR_TIER, INFO, LEVELS
- [`lib/pdf/checks/_layout.py`](#lib-pdf-checks-layout-py): layout_features, DRAWN
- [`lib/pdf/checks/caption.py`](#lib-pdf-checks-caption-py): has_caption, run, CHECK
- [`lib/pdf/checks/codereader.py`](#lib-pdf-checks-codereader-py): CodeStream, looks_like_cpp, read_lines
- [`lib/pdf/checks/coherence.py`](#lib-pdf-checks-coherence-py): column_coherence, content_features, fragment_share, header_contrast, merged_share, run, shape, table_coherence, CHECK
- [`lib/pdf/checks/data_or_format.py`](#lib-pdf-checks-data-or-format-py): features, likelihood_data, run, CHECK
- [`lib/pdf/checks/drawn_lines.py`](#lib-pdf-checks-drawn-lines-py): run, CHECK
- [`lib/pdf/checks/footprint.py`](#lib-pdf-checks-footprint-py): run, CHECK
- [`lib/pdf/checks/nominations.py`](#lib-pdf-checks-nominations-py): run, CHECK, SOURCE_INFO
- [`lib/pdf/checks/plausible.py`](#lib-pdf-checks-plausible-py): column_type, duplication, plausibility, poll_counts, sequence_order
- [`lib/pdf/checks/same_code.py`](#lib-pdf-checks-same-code-py): run, CHECK
- [`lib/pdf/checks/text_alignment.py`](#lib-pdf-checks-text-alignment-py): run, CHECK
- [`lib/pdf/checks/wordgap.py`](#lib-pdf-checks-wordgap-py): run, CHECK
- [`lib/pdf/classify.py`](#lib-pdf-classify-py): gate_tables, generator, image_share, jev_enabled, jev_table_or_not, predict, region_features, text_rows, FLAGS, GENERATORS, IMAGE_GRID_SHARE, SOURCES
- [`lib/pdf/classify_trees.py`](#lib-pdf-classify-trees-py): LAYOUT_TREE, TABLE_TREE
- [`lib/pdf/cleanup.py`](#lib-pdf-cleanup-py): cleanup_text, detect_repeating, find_hidden_regions, get_edge_items, normalize_whitespace, strip_hidden_blocks, strip_repeating
- [`lib/pdf/codepair.py`](#lib-pdf-codepair-py): find_code_pairs, same_code
- [`lib/pdf/content.py`](#lib-pdf-content-py): build, build_text, content_candidates, gutters, page_hrules, page_text, page_words, pieces_of, visual_lines, SPECIALISTS
- [`lib/pdf/continuation.py`](#lib-pdf-continuation-py): annotate, NEAR
- [`lib/pdf/dimensions.py`](#lib-pdf-dimensions-py): dimensions, weak_note
- [`lib/pdf/docmeasure.py`](#lib-pdf-docmeasure-py): DocMeasure, area_word_features, gap_stats, hyphenates, measure, visual_lines
- [`lib/pdf/dvf_model.py`](#lib-pdf-dvf-model-py): MODEL
- [`lib/pdf/emit.py`](#lib-pdf-emit-py): emit_markdown, emit_prompts, is_likely, set_hyphenating, table_use, HYPHEN_STATS
- [`lib/pdf/evidence.py`](#lib-pdf-evidence-py): Entry, Record, current, reader_error, reset
- [`lib/pdf/extent.py`](#lib-pdf-extent-py): extend, EXTENT_RULE
- [`lib/pdf/extract.py`](#lib-pdf-extract-py): attach_links, collect_links, extract_mupdf, extract_spatial
- [`lib/pdf/figures.py`](#lib-pdf-figures-py): figure_label, label_figure_tables
- [`lib/pdf/fit.py`](#lib-pdf-fit-py): fit, fit_rows, grid_of
- [`lib/pdf/flag.py`](#lib-pdf-flag-py): aligned_regions, dropped_uncovered, flag_possible_tables, gutter_regions, outside_view_regions, rejected_regions, text_regions
- [`lib/pdf/fullwidth.py`](#lib-pdf-fullwidth-py): apply, full_width_rows
- [`lib/pdf/levels.py`](#lib-pdf-levels-py): assign, cell_markers, comment, NAMES
- [`lib/pdf/llmcheck.py`](#lib-pdf-llmcheck-py): check, enabled, reset, state, CHECK_MODEL, PROMPT_VERSION
- [`lib/pdf/llmrepair.py`](#lib-pdf-llmrepair-py): ask, build_columns, code_guard, llm_enabled, paper_record, repair, reset_paper, MODEL
- [`lib/pdf/mono.py`](#lib-pdf-mono-py): classify_monospace, propagate_monospace
- [`lib/pdf/ocrcheck.py`](#lib-pdf-ocrcheck-py): check_table, mismatched_tokens, ocr_enabled
- [`lib/pdf/pagecache.py`](#lib-pdf-pagecache-py): clear, hidden_chars, rawdict, remove_covered_text, words_in
- [`lib/pdf/paper_model.py`](#lib-pdf-paper-model-py): BANDS, MODEL
- [`lib/pdf/poll.py`](#lib-pdf-poll-py): extract_poll_tables, vote_header, VOTE_LABELS
- [`lib/pdf/qa.py`](#lib-pdf-qa-py): QAMetrics, compute_metrics, run_qa_report
- [`lib/pdf/records.py`](#lib-pdf-records-py): line_kind, periodic_runs, read_region, records_candidates
- [`lib/pdf/relations.py`](#lib-pdf-relations-py): RelationRecord, Violation, check, record_for
- [`lib/pdf/repair.py`](#lib-pdf-repair-py): place_stray_words
- [`lib/pdf/rowbands.py`](#lib-pdf-rowbands-py): merge_rule_bands, MAX_FILL, MIN_RULES, MIN_SEGMENT
- [`lib/pdf/ruled.py`](#lib-pdf-ruled-py): closed_exempt, drawn_spans, extract_ruled_tables, sparse_mapping, take_excluded_grids, CLOSED_GRID_EXEMPT
- [`lib/pdf/scan.py`](#lib-pdf-scan-py): area_features, areas, band, info_of, likelihood, run_scan, DOC_PRIOR, EARLY_NONE, JEV_SURE
- [`lib/pdf/scan_model.py`](#lib-pdf-scan-model-py): MODEL
- [`lib/pdf/spans.py`](#lib-pdf-spans-py): normalize_spans
- [`lib/pdf/stacked.py`](#lib-pdf-stacked-py): apply, split_stacked
- [`lib/pdf/structure.py`](#lib-pdf-structure-py): compare_extractions, heading_confidence, structure_sections
- [`lib/pdf/summary.py`](#lib-pdf-summary-py): build, confidence, features, header_comment, prompts_section, unfamiliarity, COMMON_LAYOUTS, KNOWN_GENERATORS
- [`lib/pdf/table.py`](#lib-pdf-table-py): candidate_from_section, candidates_agree, class_check, conservation_error, cross_reader_continuation, detect_tables, diagram_boxes, join_split_words, mark_matrix, page_furniture, partial_reading, remove_table_regions, ...
- [`lib/pdf/tablemodel.py`](#lib-pdf-tablemodel-py): detect_spans, flatten, flatten_text, marker, SEP
- [`lib/pdf/tagged.py`](#lib-pdf-tagged-py): extract_tagged_tables
- [`lib/pdf/types.py`](#lib-pdf-types-py): Block, Confidence, Line, PageEdgeItem, Section, SectionKind, Span, TableCandidate, compute_bbox, is_readable, AUDIENCE_RE, BULLET_CHARS, ...
- [`lib/pdf/validate.py`](#lib-pdf-validate-py): add_header_above, cell_text, escalate, resegment_rows, split_hidden_column, split_stacked_rows, switch_reader, verify_layout, verify_pieces
- [`lib/pdf/visibility.py`](#lib-pdf-visibility-py): check_page, classify, discards, markdown, regions_of, remove_hidden_text, summary, WHY_TEXT
- [`lib/pdf/wg21.py`](#lib-pdf-wg21-py): extract_metadata_from_blocks, REPLY_TO_CONTINUATION_CAP
- [`lib/pdf/worddict.py`](#lib-pdf-worddict-py): available, is_word, words, DICT_PATH, DICT_SHA256
- [`lib/pdf/wording.py`](#lib-pdf-wording-py): classify_wording, collect_line_drawings, is_green_ins, is_red_del
- [`lib/similarity.py`](#lib-similarity-py): similar
- [`lib/toc.py`](#lib-toc-py): find_toc_indices
- [`main.py`](#main-py): main, CORPUS_LLM_BUDGET, CORPUS_LLM_PAPER_BUDGET

<a id="init-py"></a>

## `__init__.py` ([source](../../__init__.py))

```python
"""tomd - PDF and HTML to Markdown converter for WG21 papers."""
```

<a id="lib-init-py"></a>

## `lib/__init__.py` ([source](../../lib/__init__.py))

```python
"""Shared text utilities and constants for PDF and HTML converters."""

def ascii_escape(text: str) -> str:
    """Encode non-ASCII characters as HTML character references.

    Uses named entities for common diacritics (e.g. &uuml; for u-umlaut),
    falls back to numeric references (e.g. &#8212;) for others.
    """

def format_front_matter(metadata: dict) -> str:
    """Format metadata dict as YAML front matter.

    Field order: title, document, date, audience, reply-to.
    Title and values containing YAML-special characters are double-quoted
    with backslash-escaping for embedded quotes, backslashes, and newlines.
    Reply-to is a YAML list of double-quoted strings.
    Returns empty string if metadata is empty.
    """
    # calls: _yaml_value
    # called by: html.convert_html, emit.emit_markdown

def parse_author_lines(lines, clean_line=None, skip_line=None):
    """Parse author name + email pairs from an iterable of raw line strings.

    Each entry in the returned list is either 'Name <email>' when a name
    and email are found together, or a bare name string when no email
    follows. `clean_line` normalizes each line before processing (default:
    str.strip). `skip_line` returns True for lines that are not author
    content, such as metadata labels (default: never skip).
    """
    # called by: extract._extract_wg21_metadata, extract._parse_mpark_authors, wg21._parse_authors

def strip_format_chars(text: str) -> str:
    """Remove Unicode format characters (category Cf)."""
    # called by: render._collapse_whitespace, cleanup.cleanup_text, cleanup.normalize_whitespace, structure._detect_lang_label, structure._join_bullet_marker_lines, wg21._clean

ALLOWED_LINK_SCHEMES = frozenset({'http', 'https', 'mailto'})

DATE_RE = re.compile('\\b(\\d{4}-\\d{2}-\\d{2})\\b')

# Core pattern shapes (no anchors, no label context) reused across modules
# so every document- and section-number pattern has a single source of truth.
# `lib/pdf/types.py` builds the labeled PDF variants (DOC_FIELD_RE,
# SECTION_NUM_RE) on top of these.
DOC_NUM_PATTERN = '[DPN]\\d{3,5}R\\d+|[DPN]\\d{3,5}|N\\d{3,5}|SD-\\d+'

# Broad document-number match used for header stripping and HTML metadata.
# For line-anchored field extraction in PDF blocks, see DOC_FIELD_RE in
# lib/pdf/types.py, which targets "Document Number: PXXXXrN" line prefixes.
DOC_NUM_RE = re.compile(f'\\b({DOC_NUM_PATTERN})\\b', re.IGNORECASE)

EMAIL_RE = re.compile('[\\w.+-]+@[\\w.-]+\\.\\w+')

FORMAT_CHARS = ...

FRONT_MATTER_ORDER = ('title', 'document', 'date', 'audience', 'reply-to')

SECTION_NUM_PATTERN = '\\d+(?:\\.\\d+)*'

# Leading section-number prefix used by the HTML renderer to strip a number
# (e.g. "2.1.3 " or "1. ") from heading text.
SECTION_NUM_PREFIX_RE = re.compile(f'^{SECTION_NUM_PATTERN}\\.?\\s+')

# + 2 private module-level names
```

<a id="lib-html-init-py"></a>

## `lib/html/__init__.py` ([source](../../lib/html/__init__.py))

```python
"""HTML to Markdown converter for WG21 papers."""

def convert_html(path: Path | os.PathLike[str]) -> tuple[str, str | None]:
    """Convert an HTML file to Markdown.

    Reads the file as UTF-8 (with replacement for decode errors).
    Returns (markdown_text, prompts_text_or_none).
    HTML conversion produces a prompts file only when sections
    cannot be converted cleanly.
    """
    # calls: extract.parse_html, extract.detect_generator, extract.extract_metadata, extract.strip_boilerplate, render.render_body, lib.format_front_matter
    # called by: qa._qa_one, main.main
```

<a id="lib-html-extract-py"></a>

## `lib/html/extract.py` ([source](../../lib/html/extract.py))

```python
"""HTML parsing, generator detection, metadata extraction, and boilerplate stripping."""

def detect_generator(soup: BeautifulSoup) -> str:
    """Identify which tool generated this HTML paper.

    Returns one of: "mpark", "bikeshed", "hackmd", "wg21", "hand-written", "unknown".
    Checks meta generator tag first, then structural heuristics.
    """
    # called by: html.convert_html

def extract_metadata(soup: BeautifulSoup, generator: str) -> dict:
    """Extract WG21 metadata fields from the HTML.

    HTML DOM scan (pathway 3 of 3). Dispatches to a generator-specific
    extractor based on the detected generator family.

    Returns a dict with possible keys: title, document, date,
    audience, reply-to.
    """
    # calls: _extract_mpark_metadata, _extract_bikeshed_metadata, _extract_handwritten_metadata, _extract_wg21_metadata, _extract_generic_metadata
    # called by: html.convert_html

def parse_html(text: str) -> BeautifulSoup:
    """Parse HTML with the built-in parser (forgiving of malformed HTML)."""
    # called by: html.convert_html

def strip_boilerplate(soup: BeautifulSoup, generator: str) -> list[str]:
    """Remove non-content elements from `soup` in-place.

    Returns list of problem descriptions.
    """
    # called by: html.convert_html

# + 9 private module-level names
```

<a id="lib-html-render-py"></a>

## `lib/html/render.py` ([source](../../lib/html/render.py))

```python
"""DOM-to-Markdown rendering for WG21 HTML papers."""

def render_body(soup: BeautifulSoup, generator: str) -> str:
    """Render the HTML body to Markdown.

    Warning: this function may mutate the soup tree (extracting nested
    list elements). Do not reuse the soup object after calling this.
    """
    # calls: _render_children
    # called by: html.convert_html

# + 16 private module-level names
```

<a id="lib-pdf-init-py"></a>

## `lib/pdf/__init__.py` ([source](../../lib/pdf/__init__.py))

```python
"""PDF to Markdown converter - pipeline entry point."""

@dataclass
class PipelineResult:
    """Full output of the PDF conversion pipeline, used for QA scoring."""
    md: str = ''
    prompts: str | None = None
    sections: list[Section] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    page_count: int = 0
    nesting_corrections: int = 0
    readable: bool = True
    skipped: bool = False
    skip_reason: str = ''
    # every content the pipeline decided to drop: (what, why, detail)
    discards: list = field(default_factory=list)

def convert_pdf(path: Path) -> tuple[str, str | None]:
    """Convert a PDF file to Markdown.

    Returns (markdown_text, prompts_text_or_none).
    Returns ("", None) for empty or unreadable PDFs.
    Raises fitz exceptions for corrupt or inaccessible files.
    """
    # calls: _run_pipeline

def convert_pdf_with_summary(path: Path) -> tuple[str, str | None, dict | None]:
    """convert_pdf plus the paper-level summary (summary.py): tables trusted,
    flagged and marked, confidence and unfamiliarity. Written as JSON beside
    the Markdown by the command line.
    """
    # calls: _run_pipeline
    # called by: main.main

def dropped_nomination_regions(record, tables) -> list:
    """Every area a reader or scan nominated and a rule then excluded, where no kept table
    covers it, as a possible-table region - a drop never leaves the text silent - except the
    rules above. (page, bbox, reason, rows) like every mark region.
    """
    # calls: _overlap
    # called by: _run_pipeline

# + 14 private module-level names
```

<a id="lib-pdf-checks-init-py"></a>

## `lib/pdf/checks/__init__.py` ([source](../../lib/pdf/checks/__init__.py))

```python
"""The scan's checks: one file each, loaded in a fixed order.

Every check declares its name, the level(s) it serves, the kind of
information it reads (stage 0: same-type checks are not independent
witnesses), a cost tier and whether it is optional (network or money), and
a function from the level's input to evidence items (feature -> value).
Checks never change a grid; what they return goes into the evidence record
and the scan's decision through the core.

The registry is explicit and ordered (cheapest and most decisive first, as
the effectiveness ledger ranks them), not filesystem order. Checks the ledger
rates least effective (word gaps, footprint, caption: little unique
contribution, about 30 of the scan's 78 ms per paper) form a last-resort
tier, run only while an area is undecided; TOMD_SCAN_FULL=1 runs everything
(training data and the ledger). Any check can be
switched off: TOMD_CHECKS_OFF=name,name - the same switch the ledger uses to
measure what each check contributes.
"""

@dataclass
class AreaContext:
    """What a region-level check may look at."""
    page: object  # the fitz page
    area: dict  # scan.areas() entry: page, bbox, cues, excl, readings, same_code
    generator: str
    doc_tagged: bool
    measure: object = None  # docmeasure.DocMeasure (level 0)
    cache: dict = field(default_factory=dict)

@dataclass(frozen=True)
class Check:
    name: str
    levels: tuple[str, ...]
    info: str
    cost: int  # 0 = microseconds .. 3 = network / model call
    optional: bool
    run: Callable[['AreaContext'], dict]
    tier: int = 1  # 1 = effective (ledger); 2 = last resort, run only while undecided

def disabled() -> set[str]:
    # called by: registry

def full_mode() -> bool:
    """Every check on every area (training data, the ledger): TOMD_SCAN_FULL=1."""
    # called by: run_region_checks

def registry() -> list[Check]:
    # calls: disabled
    # called by: run_region_checks

def run_region_checks(ctx: AreaContext, decided: Callable[[dict], bool] | None = None) -> dict:
    """Tier 1 first; the last-resort tier only while decided(features) is False
    (or in full mode). Tiers per generator family where the family's ledger says so.
    Returns the features; "_skipped" lists the checks not run.
    """
    # calls: registry, _tier, full_mode
    # called by: scan.area_features

# Per-generator tiers (the ledger computed within each generator family on the development
# sets, work/ledger_gen_*.txt): a last-resort check is effective for a family - unique AUC
# >= 0.005 and more decisions fixed than harmed, in a family of 200+ areas - and runs in
# tier 1 there. Families not listed use the global tiers.
GENERATOR_TIER = ...

INFO = ...

LEVELS = ...

# + 1 private module-level name
```

<a id="lib-pdf-checks-layout-py"></a>

## `lib/pdf/checks/_layout.py` ([source](../../lib/pdf/checks/_layout.py))

```python
"""Shared computation for the two layout checks (computed once per area)."""

def layout_features(ctx) -> dict:
    # calls: classify.region_features
    # called by: drawn_lines.run, text_alignment.run

DRAWN = ('hrules', 'vrules', 'row_fills', 'enclosing_fill')
```

<a id="lib-pdf-checks-caption-py"></a>

## `lib/pdf/checks/caption.py` ([source](../../lib/pdf/checks/caption.py))

```python
"""Document: a "Table N" caption just above or below the area."""

def has_caption(text_above: str, text_below: str) -> bool:
    # called by: run

def run(ctx) -> dict:
    # calls: has_caption

CHECK = ...
```

<a id="lib-pdf-checks-codereader-py"></a>

## `lib/pdf/checks/codereader.py` ([source](../../lib/pdf/checks/codereader.py))

```python
"""A lightweight reader for C++-like code lines (user, 2026-10-21): not a parser.

Fed one line at a time per text stream (a column of code), it says for each line:

  depth_before / depth_after   bracket depth ({}, and () [] for open constructs)
  unit_start                   the line starts a top-level unit: a function, struct,
                               class, union, enum, namespace or template block,
                               concept, or a top-level declaration at depth 0
  unit_name                    the unit's declared name (identifier), if any
  unit_end                     a closing brace brings the depth back to 0
  label                        a comment-only line ("// This paper:")
  stmt_end                     the line ends a statement at depth 0 (';')
  continues                    an open construct carries on: unbalanced brackets, or a
                               trailing operator, comma or backslash
  preproc                      a preprocessor line (#include, #define, ...)
  not_cpp                      the line reads as another language or notation (Rust, Swift,
                               assembly, grammar productions): the reader then keeps only the
                               bracket balance and claims no unit (it never vetoes anything)

C++ only (user): declarations, templates, attributes, requires-clauses, lambdas,
contracts syntax (pre / post / contract_assert), preprocessor lines and comments.

String and character literals and comments are stripped before counting.
Deterministic, no dependency. Used as features of the line-boundary decision.
"""

class CodeStream:
    """the state of one column of code"""
    self.depth = 0  # braces
    self.paren = 0  # () and []
    self.in_block = False
    self.pending_template = False
    def __init__(self): ...
    def feed(self, line: str) -> dict:
        # calls: _strip

def looks_like_cpp(text: str) -> bool:
    """C++ by its content (any font): a token pattern only code has - scope '::', member
    '->', a template argument list, a call, braces or semicolons, C++ operators, or a
    leading C++ keyword. Abstains (False) on plain words, numbers and math.
    """
    # called by: content.page_text

def read_lines(lines: list[str]) -> list[dict]:
    """per-line facts for one stream of code lines"""
    # calls: CodeStream

# + 1 private module-level name
```

<a id="lib-pdf-checks-coherence-py"></a>

## `lib/pdf/checks/coherence.py` ([source](../../lib/pdf/checks/coherence.py))

```python
"""Meaning: column coherence of the area's best reading - items per cell,
fragments, header vs body, the weakest column's shape uniformity, and the
first column as a list of keys (local shape tier; no Jev).
"""

def column_coherence(rows, skip_header=True):
    """Per column: share of the dominant shape among filled body cells, or None (abstain)."""
    # calls: shape
    # called by: table_coherence

def content_features(rows) -> dict:
    # calls: shape
    # called by: run

def fragment_share(rows):
    """Fragments: body cells that start as a continuation (lowercase first word
    after a cell above that ended mid-phrase) or end mid-phrase.
    """
    # calls: shape

def header_contrast(rows):
    """Header vs body: share of columns whose header cell is a different kind
    from the column's body (a category over instances).
    """
    # calls: shape

def merged_share(rows):
    """Items per cell: the worst column's share of body cells holding several
    items of the column's own single-item kind (identifiers, numbers, marks),
    or several sentences. High means rows were merged.
    """
    # calls: shape

def run(ctx) -> dict:
    # calls: content_features, _best_reading

def shape(cell: str) -> str:
    # called by: column_coherence, content_features, fragment_share, header_contrast, merged_share

def table_coherence(rows):
    # calls: column_coherence

CHECK = ...

# + 1 private module-level name
```

<a id="lib-pdf-checks-data-or-format-py"></a>

## `lib/pdf/checks/data_or_format.py` ([source](../../lib/pdf/checks/data_or_format.py))

```python
"""Meaning: tabular data or formatting? In data a cell's meaning depends on its
row and its column (look a value up by row key and column header); in
formatting the grid only places content (front matter, label: value
entries, callouts, slide layouts). Features follow the web-table literature
(cell length and type consistency down columns, rows x columns, single
record, label: value pattern, large prose cells, borders), measured on the
existing keys before use (train_dvf.py: cross-validated AUC 0.99).
"""

def features(rows, f) -> dict | None:
    # called by: likelihood_data

def likelihood_data(rows, f) -> float | None:
    """P(tabular data) for a reading, or None without one."""
    # calls: features, scan.likelihood
    # called by: scan.run_scan

def run(ctx) -> dict: ...

CHECK = ...
```

<a id="lib-pdf-checks-drawn-lines-py"></a>

## `lib/pdf/checks/drawn_lines.py` ([source](../../lib/pdf/checks/drawn_lines.py))

```python
"""Drawing: rules, vertical lines, row shading and enclosing boxes in the area."""

def run(ctx) -> dict:
    # calls: _layout.layout_features

CHECK = Check('drawn_lines', ('region',), 'paths', 1, False, run)
```

<a id="lib-pdf-checks-footprint-py"></a>

## `lib/pdf/checks/footprint.py` ([source](../../lib/pdf/checks/footprint.py))

```python
"""Words: the area's text footprint against the prose measure: left and
right inset (cell padding), and how many lines end on the right measure
(justified prose does; cell text ends raggedly).
"""

def run(ctx) -> dict:
    # calls: wordgap.run

CHECK = ...
```

<a id="lib-pdf-checks-nominations-py"></a>

## `lib/pdf/checks/nominations.py` ([source](../../lib/pdf/checks/nominations.py))

```python
"""Which scans nominated the area and which rules excluded it (the evidence
record), with the number of independent information types among them.
"""

def run(ctx) -> dict: ...

CHECK = Check('nominations', ('region',), 'record', 0, False, run)

SOURCE_INFO = ...
```

<a id="lib-pdf-checks-plausible-py"></a>

## `lib/pdf/checks/plausible.py` ([source](../../lib/pdf/checks/plausible.py))

```python
"""Content plausibility: does the reading make sense as data? A meaning-based
witness, independent of geometry: it reads only the cells' text.

  sequence order   a key column that is mostly ordered (dates "2022.3",
                   "2024-01-05", section numbers, versions, paper numbers,
                   row numbers) with one or two values out of place
  poll counts      a poll (SF F N A SA header) whose count cells hold words
                   or non-integers
  column type      a column of numbers, marks or code with a cell of prose
                   (four or more words) in it
  duplication      identical non-trivial cell text in adjacent rows (a
                   misread or a doubled text layer)

plausibility(rows) -> list of (check, detail) violations; an empty list is
"no violation". Measured on the keys before it may count for anything
(plausible_measure.py).
"""

def column_type(rows) -> list:
    # called by: plausibility

def duplication(rows) -> list:
    # called by: plausibility

def plausibility(rows) -> list:
    """Every violation of the content checks for a reading (rows of cell strings)."""
    # calls: sequence_order, poll_counts, column_type, duplication
    # called by: classify.gate_tables

def poll_counts(rows) -> list:
    # called by: plausibility

def sequence_order(rows) -> list:
    # calls: _key
    # called by: plausibility

# + 1 private module-level name
```

<a id="lib-pdf-checks-same-code-py"></a>

## `lib/pdf/checks/same_code.py` ([source](../../lib/pdf/checks/same_code.py))

```python
"""Meaning: the largest code-pair similarity recorded in the area (weighted
by size where it was computed; one-line blocks abstain upstream).
"""

def run(ctx) -> dict: ...

CHECK = ...
```

<a id="lib-pdf-checks-text-alignment-py"></a>

## `lib/pdf/checks/text_alignment.py` ([source](../../lib/pdf/checks/text_alignment.py))

```python
"""Alignment and shape of the text: rows, pieces per row, aligned starts,
monospace and digit shares, size and position (the classifier's features).
"""

def run(ctx) -> dict:
    # calls: _layout.layout_features

CHECK = Check('text_alignment', ('region',), 'words', 1, False, run)
```

<a id="lib-pdf-checks-wordgap-py"></a>

## `lib/pdf/checks/wordgap.py` ([source](../../lib/pdf/checks/wordgap.py))

```python
"""Words: gaps between neighbouring words in units of the document's normal
space. Prose has uniform gaps (one space, or uniformly stretched when
justified); table lines have bimodal gaps that recur at the same x.
"""

def run(ctx) -> dict:
    # calls: docmeasure.area_word_features
    # called by: footprint.run

CHECK = ...
```

<a id="lib-pdf-classify-py"></a>

## `lib/pdf/classify.py` ([source](../../lib/pdf/classify.py))

```python
"""Stage-2 gate: is a selected table really a table, and how is it built?

Every selected table is described by cheap geometric and font features of
its area (rules drawn, shaded bands, column-split text rows, monospace and
digit shares, which table sources found it, the generator) and passed to
two small decision trees learned from the hand-checked truth tables
(classify_trees.py, generated by the PoC's train script):

  - table or not: "table", "front-matter" or "not-a-table";
  - layout class: poll, grid, rule-per-row, booktabs, boxed, tagged, ...

Optionally (TOMD_JEV=1 and a key), Jev answers the same table-or-not
question from the area's text and a summary of its geometry. Measured on
papers never used for tuning, the tree and Jev each get about 90% right;
where they agree they are right about 99% of the time. So:

  - with Jev: the gate is sure only when the tree and Jev agree;
  - without Jev: the gate is sure only when the tree's leaf is pure
    enough (_TREE_SURE).

The gate never removes text. It can make a HIGH table UNCERTAIN (the
classifiers do not think it is a table), and it can make a single-source
table HIGH when the gate is sure it is a table, the layout class matches
the source that read it, and that class's own check passed
(table.class_check) - and nothing else (lost text, damaged text layer)
made it uncertain.

Only text of the paper (table areas) is sent to Jev, and only when asked.
"""

def gate_tables(doc, pages, sections: list[Section], paper: str = '') -> dict:
    """Classify every selected table and adjust its confidence (see module doc).

    `pages` are the pages the tables were read from (upright copies of
    rotated pages). Returns a summary for logging and the prompts file.
    """
    # calls: generator, region_features, jev_table_or_not, jev_enabled, pagecache.words_in, validate.verify_layout, validate.verify_pieces, fullwidth.apply, evidence.reader_error, fit.fit, fit.fit_rows, content.page_hrules, +15 more
    # called by: pdf._build_scan_tables, pdf._run_pipeline

def generator(meta: dict) -> str:
    # called by: pdf._run_pipeline, gate_tables, scan.run_scan

def image_share(page, bbox) -> float:
    """The share of bbox covered by images drawn on the page (union approximated by the sum,
    capped at 1; overlapping images are rare inside a table).
    """
    # called by: gate_tables

def jev_enabled() -> bool:
    # called by: gate_tables, scan._jev_on

def jev_table_or_not(paper: str, regions: list) -> tuple[list, str]:
    """[(label, probability)] for every table area, and the Jev version(s).

    The areas go in batches of _JEV_BATCH per call. An area whose batch
    fails gets ("", 0.0), and the gate falls back to the tree for it.
    """
    # calls: _jev_key, _jev_batch
    # called by: gate_tables, scan._jev_tier

def predict(tree: dict, x: dict):
    """(label, confidence) from a tree exported by cart.Tree.export()."""
    # called by: gate_tables

def region_features(page, bbox, sources, flags, gen: str, doc_tagged: bool):
    """(features, text lines) of one table area. Shared with the PoC's training."""
    # calls: text_rows
    # called by: _layout.layout_features, gate_tables, scan._jev_tier

def text_rows(page, rect):
    """Text rows in rect: [(top, bottom, [(x0, x1, text, mono)])], pieces split at wide gaps."""
    # called by: region_features

FLAGS = ...

GENERATORS = ...

IMAGE_GRID_SHARE = 0.5  # images covering half a table's area: a figure grid, not data

SOURCES = ['tags', 'poll', 'grid', 'rules', 'tomd', 'text']

# + 4 private module-level names
```

<a id="lib-pdf-classify-trees-py"></a>

## `lib/pdf/classify_trees.py` ([source](../../lib/pdf/classify_trees.py))

```python
"""Decision trees for the table gate (lib/pdf/classify.py).

GENERATED by the PoC's train_gate.py from hand-checked truth tables
(901 table regions of 153 papers). Do not edit by hand:
retrain instead. Each node is {"f": feature, "t": threshold, "l", "r"}
(go left when feature <= threshold) or a leaf {"label", "p": share of
its training regions with that label, "n": how many}.
"""

LAYOUT_TREE = ...

TABLE_TREE = ...
```

<a id="lib-pdf-cleanup-py"></a>

## `lib/pdf/cleanup.py` ([source](../../lib/pdf/cleanup.py))

```python
"""Header/footer detection and text cleanup for PDF extraction."""

def cleanup_text(blocks: list[Block]) -> list[Block]:
    """Apply all text cleanup operations to extracted blocks."""
    # calls: lib.strip_format_chars, _collapse_spaces, types.Line, types.Block, _join_cross_page
    # called by: pdf._run_pipeline

def detect_repeating(all_edge_items: list[list[PageEdgeItem]], total_pages: int) -> set[tuple[float, str]]:
    """Identify header/footer items that repeat across pages.

    For each page, captures the top and bottom EDGE_ITEMS_PER_PAGE items
    by y-coordinate. Items appearing at the same y-position on at least
    half the pages are classified as repeating.

    Returns a set of (y_region, text_or_pattern) tuples to strip.
    """
    # calls: _y_bucket
    # called by: pdf._run_pipeline

def find_hidden_regions(page, body_fonts: set[str] | None = None) -> set[tuple[float, float, float, float]]:
    """Find regions of hidden text on a page.

    Detects Google Docs widget artifacts: non-document font with
    non-black color (e.g. Roboto/Material UI framework text rendered
    as dropdown values).

    Rendering mode 3 (invisible text) is intentionally ignored.
    MuPDF's dict/rawdict APIs already exclude mode 3 text from
    extraction output. Collecting mode 3 bboxes would only match
    against the visible text at the same coordinates, causing
    false-positive stripping on Chrome "Save as PDF" output where
    an invisible accessibility overlay covers every page.
    """
    # called by: pdf._run_pipeline

def get_edge_items(blocks: list[Block], page_num: int, page_height: float) -> list[PageEdgeItem]:
    """Get the top N and bottom N text items from a page by y-coordinate.

    Deduplicates by (text, rounded y-position) to avoid counting the
    same visual item twice when blocks overlap edge regions.
    """
    # calls: types.PageEdgeItem
    # called by: pdf._run_pipeline

def normalize_whitespace(text: str) -> str:
    """Collapse runs of spaces, replace non-breaking spaces, strip trailing."""
    # calls: lib.strip_format_chars, _collapse_spaces
    # called by: emit._render_paragraph_spans, emit._render_wording_section

def strip_hidden_blocks(blocks: list[Block], hidden_bboxes: set[tuple[float, float, float, float]]) -> list[Block]:
    """Remove blocks whose text is entirely within hidden regions."""
    # called by: pdf._run_pipeline

def strip_repeating(blocks: list[Block], repeating: set[tuple[float, str]]) -> list[Block]:
    """Remove lines (or individual spans) matching repeating header/footer
    patterns from blocks.

    Spatial-path lines merge left/center/right header columns (one span
    per column). The whole-line text then won't match any single pattern,
    but each column-span will; per-span stripping handles that while
    preserving non-header content that shares the header y-coordinate
    (e.g. a one-off appendix title).
    """
    # calls: _y_bucket
    # called by: pdf._run_pipeline

# + 3 private module-level names
```

<a id="lib-pdf-codepair-py"></a>

## `lib/pdf/codepair.py` ([source](../../lib/pdf/codepair.py))

```python
"""Side-by-side code comparisons, found from geometry and confirmed by content.

  observation  two blocks of monospace lines on one page whose vertical
               extents overlap (by half the shorter one) with a gutter
               between them - whatever draws them: boxes, shading, rules or
               white space only;
  hypothesis   the two blocks do roughly the same thing: they share much of
               their code (whitespace-free character trigrams, since text
               layers often drop spaces in code), and the right one is not
               a column of comments beside the left one;
  validation   short labels aligned above both blocks become the header row;
               pairs stacked down the page with the same column starts are
               rows of one table.
Measured on the truth sets (cmp_measure.py) before use. A pair is a table
candidate like any other ("codepair"); it renders with the code-comparison
convention.
"""

def find_code_pairs(blocks: list[Block], rules_for=None) -> list[TableCandidate]:
    """Code-comparison candidates on every page. rules_for(page) gives the
    page's drawn horizontal rules (y, x0, x1): a rule between two lines
    separates them (rows of a ruled comparison are not one block).
    """
    # calls: _pieces, _mono, _blocks, _box, evidence.current, _comment_share, _code_like, same_code, _label, _spaced
    # called by: pdf._run_pipeline

def same_code(left: list[Line], right: list[Line]) -> float:
    """Share of the smaller block's trigrams that the other block has too."""
    # calls: _grams
    # called by: find_code_pairs

# + 10 private module-level names
```

<a id="lib-pdf-content-py"></a>

## `lib/pdf/content.py` ([source](../../lib/pdf/content.py))

```python
"""One content-first row/column builder for every table class.

The layout class only locates the region; inside it, rows and columns come
from the words themselves, top down:

  lines    words sharing a baseline (vertical overlap) form a visual line
  pieces   words in a line closer than a word gap form a piece (a phrase)
  columns  gutters: x ranges that (almost) no piece crosses, over all lines;
           columns are the spans between gutters that hold pieces. A piece
           crossing a gutter in at most _SPAN_LINES lines is a spanning cell
           (a header over several columns), not evidence against the gutter.
  rows     a line starts a new row when the vertical gap above it is a row
           gap (the region's own natural break between line leading and row
           spacing), or - when gaps do not separate rows (LaTeX booktabs,
           p{} wraps with row spacing equal to leading) - when it has text in
           the key column (the leftmost column filled in most rows) and the
           line above was not a lone wrap of that column. A line that fills
           only some columns, continuing cells from above, joins the row
           above (wrap continuation).
  cells    the pieces of each row and column, joined in reading order.

Every decision is recorded (`trace`) so a specialist's evidence can be
compared against it: drawn rules, box edges and tags confirm or contradict
this grid; they do not build it.
"""

def build(words, hrules=(), specialists=None):
    """-> (rows of cell strings, trace).

    hrules: y positions of drawn horizontal separators that cross most of the
    region (a specialist's evidence at the row level: a drawn line between
    two text lines separates rows; no line is not evidence of anything).
    """
    # calls: visual_lines, pieces_of, gutters, _per_unit_relation
    # called by: build_text, content_candidates

def build_text(words, hrules=(), specialists=None):
    """Rows of cell strings (for measurement)."""
    # calls: build

def content_candidates(pages, regions, specialists=None, rules_by_page=None) -> list[TableCandidate]:
    """For every located region (page, bbox) - from any reader, kept or not -
    the content-first grid of the words inside it.
    """
    # calls: page_text, page_hrules, build, _region_rules, _rotated_header, _cell_lines, types.TableCandidate
    # called by: pdf._build_scan_tables, pdf._run_pipeline

def gutters(lines_pieces, x_lo, x_hi):
    """x intervals crossed by at most _SPAN_LINES lines' pieces."""
    # called by: build

def page_hrules(page, drawings=None) -> list[tuple[float, float, float]]:
    """Drawn horizontal separators on the page: (y, x0, x1)."""
    # called by: pdf._run_pipeline, classify.gate_tables, content_candidates

def page_text(page) -> tuple[list[tuple], list[tuple]]:
    """Horizontal words (x0, y0, x1, y1, text, monospace), and rotated lines
    (x0, y0, x1, y1, text) - labels set at 90 degrees, as table headers often
    are. Rotated text is kept out of line, row and column building.
    """
    # calls: pagecache._dedup_words, codereader.looks_like_cpp
    # called by: content_candidates, page_words, _Page.__init__

def page_words(page) -> list[tuple]:
    """(x0, y0, x1, y1, text, monospace) for every horizontal word on the page."""
    # calls: page_text

def pieces_of(line):
    # called by: build

def visual_lines(words):
    """words: (x0, y0, x1, y1, text) -> lines of words sorted left to right."""
    # called by: _rotated_header, build, extent._row_from

SPECIALISTS = {'code_rows': True, 'separators': True}

# + 4 private module-level names
```

<a id="lib-pdf-continuation-py"></a>

## `lib/pdf/continuation.py` ([source](../../lib/pdf/continuation.py))

```python
"""A note on table pieces that may continue the previous page's table (2026-10-24).

When a table piece reaches the bottom of its page's content area and the next page's first table
piece starts at the top of that page's content area, the next piece is noted as possibly
continuing the previous one. The note names the evidence seen: reaches the bottom, starts at the
top, and, when present, the same header row and the first column's numbering continuing.

Since 2026-10-24 the note is written only when the first column's numbering also continues across
the break (US 019 → US 020): with the page-edge signals alone it was right 55 of 150 times on the
tuning sets (TOMD_CONTINUES_ALL=1 restores that). It never joins pieces, changes cells or changes
levels, so the note says "may", and the pieces stay separate.

The content area of a page excludes page furniture: lines whose text (digits ignored) repeats
within 3 pt of the same position on an adjacent page.
"""

def annotate(doc, tables) -> int:
    """Set metadata["continues_from"] = {"page": N, "reasons": [...]} (N 1-based, the previous
    page) on table pieces that may continue the previous page's table. Returns the count.
    """
    # calls: _extent, _Areas, _text, _number
    # called by: pdf._run_pipeline

NEAR = 0.06  # within 6% of the page height of the content edge

# + 5 private module-level names
```

<a id="lib-pdf-dimensions-py"></a>

## `lib/pdf/dimensions.py` ([source](../../lib/pdf/dimensions.py))

```python
"""Stage 2 (relationship plan): confidence per dimension.

A table can be right in some respects and wrong in others. Each dimension
gets a level from what tomd recorded about the table:

  rows     row boundaries        weak: a drawn rule with text on both sides
                                 inside one row, one baseline in several
                                 rows, stacked or overlapping rows
  columns  column boundaries     weak: a recurring gutter inside one cell,
                                 a hidden or overlapping column
  header   the header row        weak: an aligned row just above the table
                                 may be its header
  cells    membership, extent    weak: a page word in no cell or in two,
                                 overlapping cells, a table that may
                                 continue on the next page, too small

strong: at least two independent information types back the dimension
(words, paths, tree) and nothing marks it weak; ok otherwise.

Measured on the answer keys (dims_measure.py): each signal goes to the
dimension it describes, and signals that fire mostly on correct tables
(cell order, conservation) are left out. Switching a flagged table to
another reading by its weak dimension fixed none and broke 15 on the
tuning sets, so the levels are diagnosis: metadata, and the prompts name
the weak dimension so a reader checks that first. They never change a
table's confidence.
"""

def dimensions(meta: dict) -> dict:
    """{dimension: {"level": strong|ok|weak, "why": [...]}} from a table's metadata."""
    # called by: classify.gate_tables

def weak_note(dims: dict) -> str:
    """One line for the prompts: the weak dimensions and why, or ""."""
    # called by: emit.emit_prompts
```

<a id="lib-pdf-docmeasure-py"></a>

## `lib/pdf/docmeasure.py` ([source](../../lib/pdf/docmeasure.py))

```python
"""Level 0: what ordinary prose looks like in this document.

Measured once per paper from the body text (lines of multi-line blocks with
several words): the prose measure (left and right text edges, robust
percentiles), whether the prose is justified (right edges pile up on the
measure), and the normal space between words per text height. Everything
below compares against it: a table's text is inset from the measure (cell
padding) and ends raggedly per column; its lines have bimodal word gaps
(one space inside cells, several between cells, recurring at the same x),
where prose has uniform gaps (one space, or uniformly stretched when
justified).
"""

@dataclass
class DocMeasure:
    left: float = 0.0
    right: float = 0.0
    justified: float = 0.0  # share of prose lines ending on the right measure
    space: dict = field(default_factory=dict)  # text height (pt, rounded) -> normal word space
    known: bool = False
    def word_space(self, height: float) -> float: ...

def area_word_features(words, m: DocMeasure) -> dict:
    """Word-gap and footprint features of the words in one area."""
    # calls: visual_lines, gap_stats
    # called by: wordgap.run

def gap_stats(line, m: DocMeasure) -> dict | None:
    """One visual line's word gaps in units of the document's normal space."""
    # called by: area_word_features

def hyphenates(page_words: list[list]) -> bool:
    """Does the document break words with a hyphen at line ends? Evidence: a
    line ending in "word-" whose join with the next line's first word appears
    elsewhere in the document unhyphenated ("compari-" + "son", "comparison"
    seen elsewhere). Two or more such breaks: it hyphenates. None: a line-end
    hyphen is the word's own ("Use-" + "cases"). One: undecided, treated as
    hyphenating (the earlier behaviour). Measured on the keys: 4 to 223 such
    breaks in hyphenating papers (LaTeX, and Word with hyphenation on), 0 in
    papers that never hyphenate. The maker alone does not tell (Word can do
    either).
    """
    # called by: pdf._run_pipeline

def measure(page_words: list[list]) -> DocMeasure:
    """page_words: per page, fitz "words" tuples (x0, y0, x1, y1, text, block, line, n)."""
    # calls: visual_lines, DocMeasure
    # called by: pdf._run_pipeline

def visual_lines(words):
    """Words (x0, y0, x1, y1, text, ...) sharing a baseline, left to right."""
    # called by: area_word_features, measure
```

<a id="lib-pdf-dvf-model-py"></a>

## `lib/pdf/dvf_model.py` ([source](../../lib/pdf/dvf_model.py))

```python
"""Data-vs-formatting model, fitted by train_dvf.py on the existing keys."""

MODEL = ...
```

<a id="lib-pdf-emit-py"></a>

## `lib/pdf/emit.py` ([source](../../lib/pdf/emit.py))

```python
"""Markdown and companion prompts file generation."""

def emit_markdown(metadata: dict, sections: list[Section]) -> str:
    """Generate the output Markdown from structured sections.

    Confident sections are clean Markdown. Uncertain sections emit
    the MuPDF version marked with an HTML comment.
    """
    # calls: _set_lexicon, lib.format_front_matter, _render_section_md, is_likely, levels.comment, _is_uncertain_table
    # called by: pdf._run_pipeline

def emit_prompts(sections: list[Section]) -> str | None:
    """Generate the companion prompts file for uncertain regions.

    Returns None if there are no uncertain regions.
    """
    # calls: _is_flagged, _render_section_md, _is_uncertain_table, is_likely, dimensions.weak_note
    # called by: pdf._run_pipeline

def is_likely(sec: Section) -> bool:
    """A flagged table whose words fit its drawn cells evenly (fit.py): 'likely
    correct', between trusted (HIGH) and flagged. Never HIGH until a fresh
    sample proves the fit about 99% precise out of sample.
    """
    # called by: emit_markdown, emit_prompts

def set_hyphenating(value: bool) -> None:
    # called by: pdf._run_pipeline

def table_use(rows) -> str:
    """What a grid is used for, by the user's decisions (2026-10-19):
    "label-value" - repeated per-item "label: value" entries (not a table);
    "contents" - a contents page or reference list laid out in a grid (not a table);
    "table" - everything else.
    """
    # called by: pdf._build_scan_tables, _render_table_inner

HYPHEN_STATS: Counter = Counter()  # which rule decided each hyphen (measurement)

# + 30 private module-level names
```

<a id="lib-pdf-evidence-py"></a>

## `lib/pdf/evidence.py` ([source](../../lib/pdf/evidence.py))

```python
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

@dataclass
class Entry:
    kind: str  # "nominated" | "excluded" | "feature"
    scan: str  # which scan or check wrote it
    page: int
    bbox: Box
    rule: str  # the rule that decided (or the feature's name)
    info: str  # information type the rule used
    value: object = None  # a feature's value, or extra detail
    observed: bool = True  # observed on the page, or inferred

@dataclass
class Record:
    entries: list[Entry] = field(default_factory=list)
    # every candidate reading: (source, page, bbox, rows of cell text)
    readings: list[tuple] = field(default_factory=list)
    doc_measure: object = None  # level 0 (docmeasure.DocMeasure)
    # readers, checks and specialists that raised: never swallowed silently
    errors: list[dict] = field(default_factory=list)
    def exclude(self, scan: str, page: int, bbox: Box, rule: str, info: str, value=None) -> None:
        # calls: Entry
    def feature(self, scan: str, page: int, bbox: Box, name: str, info: str, value, observed=True) -> None:
        # calls: Entry
    def nominate(self, scan: str, page: int, bbox: Box, cue: str, info: str, value=None) -> None:
        # calls: Entry
    def on_page(self, page: int, kind: str | None = None) -> list[Entry]: ...

def current() -> Record:
    # called by: codepair.find_code_pairs, extent.extend, flag.flag_possible_tables, llmrepair.repair, ruled._bands_to_table, ruled._column_ruled_tables, ruled.extract_ruled_tables, table._continuation_votes, table.cross_reader_continuation, table.select_tables, table.stitch_pages

def reader_error(stage: str, page, exc: BaseException, table=None) -> None:
    """Record a reader, check or specialist that raised (stage, page or None for
    the whole paper, exception type and message). Tables the failure touched drop
    to UNCERTAIN ("reader error"); the prompts note and the paper summary list it.
    TOMD_STRICT=1 re-raises instead (tests).
    """
    # called by: pdf._graphic_text_page, pdf._run_pipeline, pdf._upright_page, classify.gate_tables, llmcheck.check, llmrepair.repair, pagecache.hidden_chars, pagecache.remove_covered_text, ruled._mark_icon_cells, tagged.extract_tagged_tables, visibility.check_page, wording.collect_line_drawings

def reset() -> Record:
    # calls: Record
    # called by: pdf._run_pipeline
```

<a id="lib-pdf-extent-py"></a>

## `lib/pdf/extent.py` ([source](../../lib/pdf/extent.py))

```python
"""The extent step: where each reader's table stops, and the rows just outside it.

Runs after every reader, before selection, with the pages at hand.

Stop reason (evidence): for every candidate, at its top and bottom, the
reader's own extent rule and what lies just beyond (page edge, a drawn rule,
the gap to the next text, that text). Readers do not record why they stop;
this is the one place that does.

Rows just outside a reading (user, from the cut-short diagnosis: "Alignment
of text over the columns is a common reason"; background colour; rules that
keep separating the columns; a header placed under its columns):
  alignment   a short label row directly above (or below) the body whose
              pieces each start at, or are centred over, a body column, and
              that covers at least two columns
  dividers    the body's vertical column dividers continue through the row
              (the row is inside the drawn table even above its first
              horizontal rule)
  shading     a filled band spanning the table's width directly above or
              below the body holds the row (a header or title band)
Dividers and shading are drawn paths - the same information type as rules -
so they set extent; they are not an independent witness. A row above becomes
the first row; a label row below the body (short labels, unlike the body's
cells) is the table's header, placed first and marked as found under the
columns. Tagged and poll readings are left alone (the tag tree and the poll
vocabulary state their own extent).
"""

def extend(cands: list[TableCandidate], pages: dict) -> None:
    # calls: evidence.current, _Page, _beyond, _row_height, _overlaps, _block, _kind, _pieces, _row_from
    # called by: pdf._run_pipeline

EXTENT_RULE = ...

# + 19 private module-level names
```

<a id="lib-pdf-extract-py"></a>

## `lib/pdf/extract.py` ([source](../../lib/pdf/extract.py))

```python
"""Dual-path PDF text extraction: MuPDF grouping and spatial rules."""

def attach_links(blocks: list[Block], links: list[dict]) -> None:
    """Match link annotations to text spans by bounding rect overlap.

    Mutates spans in-place (sets `link_url`). If multiple links
    overlap the same span, the best-overlap link wins.
    """
    # called by: pdf._run_pipeline

def collect_links(page) -> list[dict]:
    """Collect hyperlink annotations from a page.

    Returns a list of dicts with 'uri' and 'bbox' keys.
    Only http, https, and mailto schemes are kept.
    """
    # called by: pdf._run_pipeline

def extract_mupdf(page, page_num: int) -> list[Block]:
    """Extract text using MuPDF's built-in block/line/span hierarchy.

    Uses page.get_text("dict"). Returns MuPDF's interpretation of
    paragraphs, lines, and word groupings with font metadata preserved.
    """
    # calls: types.Span, mono.classify_monospace, types.Line, types.Block
    # called by: pdf._run_pipeline

def extract_spatial(page, page_num: int) -> list[Block]:
    """Extract text using raw character coordinates and spatial rules.

    Uses page.get_text("rawdict") for per-character bounding boxes.
    Classifies each consecutive character pair via four elif branches,
    using font-size-relative named constants from types.py:

      dy > PARA_SPACING_RATIO * avg_fs  -> flush block (paragraph break)
      dy > LINE_SPACING_RATIO * avg_fs  -> flush line (new line, same block)
      dy > WORD_GAP_RATIO    * avg_fs  -> flush line (large vertical gap)
      dx > WORD_GAP_RATIO    * avg_fs  -> flush word + insert space span
    """
    # calls: types.Span, mono.classify_monospace, types.compute_bbox, types.Line, types.Block
    # called by: pdf._run_pipeline
```

<a id="lib-pdf-figures-py"></a>

## `lib/pdf/figures.py` ([source](../../lib/pdf/figures.py))

```python
"""Tables inside figures: label them with the figure they belong to.

Convention (user decision): small tables drawn inside a figure are converted
as tables, labelled with the figure they belong to, e.g. "Figure 4(a)". The
label line goes before the table and is taken from the sub-caption under the
table ("(a) Table of actors.") and the figure caption below the figure
("Figure 4: ...").

A table belongs to a figure when a figure caption lies below it on the same
page and nothing between them is ordinary prose (a wide text block that is
not a sub-caption). A table with its own "Table N" caption close by is a
table in its own right, never labelled.
"""

def figure_label(blocks, bbox, text_width: float) -> str | None:
    """blocks: (bbox, text) of the page's text blocks; bbox: the table's box."""
    # called by: label_figure_tables

def label_figure_tables(doc, table_sections) -> int:
    """Set metadata["figure_label"] on single-page tables drawn inside a figure."""
    # calls: _blocks, figure_label
    # called by: pdf._run_pipeline

# + 1 private module-level name
```

<a id="lib-pdf-fit-py"></a>

## `lib/pdf/fit.py` ([source](../../lib/pdf/fit.py))

```python
"""The fit witness: does the word layout fit the drawn cells evenly?

A drawn grid and the words on the page are two independent sources (paths
and words). When a reading is right, the words fit the drawn cells the way
a typesetter put them there: every word lies fully inside one cell, no word
crosses or touches a rule, and the padding is even - in each column the
text keeps the same inset from the cell edge it is aligned to (left, right
or centre), and in each row band the same inset from the top (or centre).
A misread grid - merged or split cells, a shifted column, a lost row -
breaks the even padding somewhere, or maps one cell of the reading onto two
drawn cells.

Content irregularities (a first column mixing "2022.3 Kona" with "2024.1",
many blank cells) do not count against a tight fit: the fit is what settles
them (user, 2026-10-20).

fit(...) returns a record: whether a drawn grid was found, whether the
fit passes, and why not. It passes only for a fully lined grid that
matches the reading one-to-one (rows and columns), whose drawn frame ends
where the reading ends, and whose cells hold the same characters as the
text layer in each drawn cell (a misread text is not a structure error, so
the fit checks it too).
"""

def fit(page, bbox, words, columns) -> dict:
    """Does the reading `columns` (rows of cells of spans) fit the drawn grid?"""
    # calls: grid_of, _frame_continues, _spread, _squash
    # called by: classify.gate_tables

def fit_rows(page, bbox, words, columns) -> dict:
    """The partial fit for ruled-row tables (horizontal rules, no vertical ones):
    row bands come from the drawn rules, columns from the reading's own gutters.
    Every word lies inside one band and one column with a clear gutter on both
    sides, the bands holding words match the reading's rows one to one, no
    band holds stacked entries, and each cell's characters equal the text
    layer's in its band and column. Measured apart from the grid fit; it never
    counts as a witness unless it separates as well.
    """
    # calls: _segments, _clusters, _squash
    # called by: classify.gate_tables

def grid_of(page, bbox):
    """(xs, ys, has_v, has_h) of the drawn grid, or None: at least 3 column
    lines and 3 row lines that span the region.
    """
    # calls: _segments, _clusters, _covers
    # called by: fit

# + 6 private module-level names
```

<a id="lib-pdf-flag-py"></a>

## `lib/pdf/flag.py` ([source](../../lib/pdf/flag.py))

```python
"""Mark text that is probably a table but was not extracted as one.

The table sources only emit what passes their checks, so a real table can
reach the output as plain paragraphs or code with no warning. This module
looks at what is left after table selection and marks the sections in
table-like areas uncertain (their text is kept as it is), so a reader or an
LLM pass knows to rebuild them. Two kinds of evidence:

  - a drawing or tag source found a table there, but the rule checks
    rejected its reading (select_tables' `rejected` list);
  - the text itself is laid out like a table: a run of rows split into
    columns by wide gaps, with the columns starting at the same x positions
    from row to row, or a vote line ("SF F N A SA", "Favor: 8 ...").

Nothing here decides cell boundaries; it only says "look here".
"""

def aligned_regions(blocks: list[Block]) -> list[Region]:
    """Tables without rules found by their columns, as the vision readers find
    them: text in three or more columns whose starts line up down consecutive
    rows (left-aligned cells), with no line running across a column start.
    A header row just above (centred labels) joins the region. Code listings,
    contents pages and front matter are left out; what remains is read by the
    content reader and checked like any other reading.
    """
    # calls: _rows, _is_not_table
    # called by: pdf._run_pipeline

def dropped_uncovered(rejected: list[TableCandidate], tables: list[Section]) -> list[str]:
    """Every dropped candidate (any source, any reason) that no kept table
    covers, for the prompts file: nothing a reader found is erased, but only
    misread-looking ones are marked in the Markdown (rejected_regions).
    """
    # called by: pdf._run_pipeline

def flag_possible_tables(sections: list[Section], regions: list[Region]) -> int:
    """Mark sections inside a region; returns how many. Locality: a section is cut at page
    breaks, so its lines on other pages never inherit a mark (variant 5b).
    """
    # calls: _line_in, evidence.current, _split_at_region, _mostly_in
    # called by: pdf._run_pipeline

def gutter_regions(blocks: list[Block]) -> list[Region]:
    """Tables found by their negative space: a vertical whitespace gutter.

    A table without rules still leaves an empty vertical strip between its
    columns that runs down consecutive lines, with text on both sides.
    Running text has none (it fills the measure and wraps), and neither do
    lists or headings. Each run of at least _GUTTER_ROWS lines with text on
    both sides of one gutter is a region, unless it is two-column prose
    (sentences on both sides), code with aligned comments, a contents page
    or title-page metadata.
    """
    # calls: _rows, _prose, _is_not_table
    # called by: pdf._run_pipeline

def outside_view_regions(sections: list[Section]) -> list[Region]:
    """Tables seen from the outside, against the paper's own prose: a block
    that is set apart (its rows fill much less than the prose measure) AND
    two-dimensional (most rows hold 2+ pieces whose positions recur on other
    rows). A block that is set apart but one-dimensional is a quote or a
    list; prose fills the measure. Measured on the tuning sets before use.
    """
    # calls: _visual_rows, _pieces
    # called by: pdf._run_pipeline

def rejected_regions(rejected: list[TableCandidate], tables: list[Section]) -> list[Region]:
    """Areas of rejected drawing/tag tables that no selected table covers."""
    # called by: pdf._run_pipeline

def text_regions(blocks: list[Block]) -> list[Region]:
    """Table-like areas in the remaining text."""
    # calls: _rows, _is_not_table, _is_table_row, _shared_starts
    # called by: pdf._run_pipeline

# + 11 private module-level names
```

<a id="lib-pdf-fullwidth-py"></a>

## `lib/pdf/fullwidth.py` ([source](../../lib/pdf/fullwidth.py))

```python
"""Full-width rows in drawn tables: titles and spanning rows read as spans.

A boxed table often has rows that run across every column: a title over the
table ("[comma.value-category]", set right-aligned), a link or an
explanation under the code. The page shows it directly: the internal vertical
rules that separate the columns elsewhere do not cross that row. A reader
that follows the structure tree or the cell grid puts the row's text in
whichever column it happens to start in; under the span convention a cell
spanning several columns holds its text in the first column, with empty
cells after it.

So: in a table with internal vertical rules, a row that none of them
crosses and that has exactly one non-empty cell is a full-width row; its
text moves to the first column and the row is recorded in the metadata
(full_width_rows: title for the first row, data otherwise). Tables without
internal rules are left alone - no rule is not evidence of a span.
"""

def apply(sec, page, bbox) -> list[int]:
    """Move each full-width row's text to its first cell; record the spans."""
    # calls: full_width_rows
    # called by: classify.gate_tables

def full_width_rows(columns, page, bbox) -> list[int]:
    # calls: _vertical_rules, _row_band
    # called by: apply

# + 2 private module-level names
```

<a id="lib-pdf-levels-py"></a>

## `lib/pdf/levels.py` ([source](../../lib/pdf/levels.py))

```python
"""Graded table levels (L0-L5) and cell markers, from tomd's own evidence.

The binary HIGH / UNCERTAIN says only whether to trust a table; a reader of the
output (an AI evaluating the paper) also needs to know how a flagged table may be
wrong, so it can tell a nearly-right reading from a misattributed one:

  L0 trusted               HIGH: independent sources agree
  L1 likely                flagged, but the words fit the drawn cells evenly
  L2 minor                 flagged on one source only; every check on content passed
  L3 structure uncertain   readers disagree, the fit or layout check failed, relational
                           violations, the extent is open (a table may continue)
  L4 content at risk       text duplicated or misattributed (conservation surplus),
                           damaged text, cells read out of order, a reader error, repaired
     L4 incomplete         text of the area missing from the cells, nothing duplicated or
                           out of order: content missing, what is there is not contradicted
  L5 mark only             a possible table that was not produced (a mark, not a table)

The most severe level that applies is the table's level. Cell markers list the cells
where the table's alternative readings (same shape) disagree. Levels are metadata: the
table's content is unchanged.
"""

def assign(sec) -> dict:
    """{"level", "name", "why", "incomplete", "cells"} for a table section"""
    # calls: cell_markers
    # called by: pdf._run_pipeline, classify.gate_tables

def cell_markers(sec) -> list[tuple[int, int]]:
    """cells where an alternative reading of the same shape disagrees with the table"""
    # calls: _rows
    # called by: assign

def comment(info: dict) -> str:
    # called by: emit.emit_markdown

NAMES = ...

# + 1 private module-level name
```

<a id="lib-pdf-llmcheck-py"></a>

## `lib/pdf/llmcheck.py` ([source](../../lib/pdf/llmcheck.py))

```python
"""Opt-in LLM second look at questionable tables: a narrow check, asked twice.

For a table at L3 (structure uncertain) or L4 (content at risk) - never L0-L2 - a
vision model gets the page crop and tomd's reading, and answers one narrow question:
do these rows and columns match the table on the page (yes / no, and which rows are
wrong). The question is asked twice; only identical answers count (user, 2026-10-23).
Answers are cached by PDF hash, region, model and prompt version; the model is pinned.

What an answer can do: a "match" confirmed twice raises the table at most to LIKELY
(L1), never HIGH, and only when an independent reader already agrees with the reading
(the witness record); a "no" names the rows to check in the table's note. The text of
the table is never changed here (repair is llmrepair.py, measured apart).

On only with TOMD_LLM_CHECK=1 (the --corpus profile); credentials as llmrepair.py
resolves them (the SDK reads them; tomd never reads, logs or prints a key or token).
A budget per paper (TOMD_LLM_CHECK_BUDGET, questions; default 12) caps the cost.
"""

def check(client, page, bbox, rows, pdf_hash: str) -> dict | None:
    """{"match", "wrong_rows", "consistent"} from two identical answers, or None (the
    answers differed, an error, or the budget is spent)
    """
    # calls: _cache_path, _budget, llmrepair._image, _ask_once, evidence.reader_error
    # called by: pdf._run_pipeline, llmrepair.repair

def enabled() -> bool:
    # calls: llmrepair._has_credentials
    # called by: pdf._run_pipeline

def reset() -> None:
    # called by: pdf._run_pipeline

def state() -> dict:
    # called by: pdf._run_pipeline

CHECK_MODEL = 'claude-sonnet-5-5'

PROMPT_VERSION = 'check-v1'

# + 3 private module-level names
```

<a id="lib-pdf-llmrepair-py"></a>

## `lib/pdf/llmrepair.py` ([source](../../lib/pdf/llmrepair.py))

```python
"""Opt-in LLM repair of flagged tables: structure only, never content.

A table that is still UNCERTAIN after every deterministic reader and the
escalation moves may be sent to a vision model - only when TOMD_LLM=1 and
credentials exist: ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, or an
`ant auth login` profile (the Anthropic SDK resolves them; tomd never reads,
logs or prints a key or token). The model gets the rendered
table region and the page's own words, each with an index and position,
and returns rows of cells as lists of word indices. It cannot write text:
tomd builds every cell from the indexed page words.

The result is kept only if every word of the region is used exactly once
(nothing added, nothing lost) and the rebuilt table passes the same
geometric verification as any other table (validate.verify_layout).
Otherwise it is discarded and the table stays flagged. Any API error,
refusal or malformed answer leaves the table as it was.

Confident tables are never sent. Only paper text (public WG21 papers) and
the page image of the table are sent.
"""

def ask(client, page, bbox, words):
    """(rows of index lists, model id, seconds, usage) or None."""
    # calls: _image, _prompt, _note
    # called by: repair

def build_columns(rows, words):
    """Cells of spans from word indices, or (None, reason) if the answer is unusable:
    an index out of range, used twice, or a word left out.
    """
    # calls: types.Span
    # called by: repair

def code_guard(first, repaired) -> str:
    """A repair may not add a column of bare line numbers to code (2026-10-24). Returns the failed
    check or "". Measured on fresh10's cached answers: it turns the two breaks LLM repair caused
    in side-by-side code (p2318r1, one row per code line plus a line-number column) into no
    change. A wider rule, rejecting any repair that cuts a multi-line code cell into rows, also
    undid two of the seven fixes (p2329r0-t2, p1985r3-t2), whose first readings had packed
    several rows into one code cell; it is not used.
    """
    # called by: repair

def llm_enabled() -> bool:
    # calls: _has_credentials, _budget
    # called by: classify.gate_tables

def paper_record() -> dict:
    """What LLM repair did for this paper, for the paper summary: whether it
    was asked for and available, the model(s), calls, results, tokens, seconds,
    and the run's budget. With no credentials, no network or no budget left the
    run goes on without repair, and the status says so.
    """
    # calls: _has_credentials, _budget
    # called by: summary.build, main.main

def repair(sec, page, bbox, words, verify, client=None) -> str:
    """Try to repair one flagged table in place. Returns what happened."""
    # calls: _note, _paper_budget, _client, ask, build_columns, code_guard, llmcheck.check, evidence.current, evidence.reader_error
    # called by: classify.gate_tables

def reset_paper() -> None:
    # called by: pdf._run_pipeline, _note

MODEL = 'claude-opus-5-5'

# + 7 private module-level names
```

<a id="lib-pdf-mono-py"></a>

## `lib/pdf/mono.py` ([source](../../lib/pdf/mono.py))

```python
"""Triple-signal monospace font detection.

Three independent signals:
  1. Font name decomposition (strip modifiers, split camelCase, check keywords)
  2. Glyph bounding box widths are uniform (low coefficient of variation)
  3. Glyph x-origin spacing is uniform (measures advance width directly)

Acceptance rules:
  - Two or more signals agreeing: accept (high confidence)
  - Signal 3 alone: accept (measures the defining property of monospace)
  - Signal 1 alone: accept (fallback when no glyph data is available)
  - Signal 2 alone: reject (weakest signal, bbox widths are noisy)

The spatial extraction path (rawdict) provides per-character data for signals
2 and 3. The MuPDF dict path does not. The pipeline orchestrator propagates
spatial glyph-width decisions to MuPDF spans of the same font after extraction.
"""

def classify_monospace(font_name: str, char_widths: list[float] | None = None, char_x_origins: list[float] | None = None, chars: list[str] | None = None) -> bool:
    """Accept or reject monospace classification from available signals.

    Called during extraction when raw character data is available
    (all three signals), or later with just font_name (signal 1 only).
    When chars and char_x_origins are provided, compares advance widths
    (x-origin spacings) of fat characters (M, W) against thin characters
    (i, l) to reject proportional fonts early. Advance widths are uniform
    in monospace fonts regardless of glyph body width, so the ratio of fat
    to thin advance widths is close to 1.0 for monospace and much larger
    for proportional fonts.
    """
    # calls: _font_name_is_monospace, _glyph_widths_uniform, _glyph_spacing_uniform
    # called by: extract.extract_mupdf, extract.extract_spatial, propagate_monospace, ruled._chars_to_lines, ruled._page_words, tagged._lines_of

def propagate_monospace(mupdf_blocks: list[Block], spatial_blocks: list[Block], dominant_font: str) -> None:
    """Apply spatial path's glyph-width monospace decisions to MuPDF spans.

    Only propagates fonts whose spatial spans are mostly classified
    monospace (by character count). Short spans of digits or thin
    characters can false-positive the per-glyph signal, so requiring a
    majority keeps proportional fonts (e.g. a regular text font with a
    handful of "1" or "3.1" spans) out of the mono set.

    The dominant_font is still discarded unless it passes a
    name-based mono check, to avoid body text leaking into code blocks
    when metrics happen to agree across a majority.
    """
    # calls: classify_monospace
    # called by: pdf._run_pipeline

# + 6 private module-level names
```

<a id="lib-pdf-ocrcheck-py"></a>

## `lib/pdf/ocrcheck.py` ([source](../../lib/pdf/ocrcheck.py))

```python
"""Check a HIGH table's text layer against the picture of the page.

Table sources agree because they all read the same text layer, so a text
layer that differs from what is printed fools them all at once (p3830r0:
the text layer says "WF" where the page shows "F", and all three sources
agreed). This check uses a different modality: it renders the table's
header row - and a poll's vote row - and reads it with OCR (Tesseract),
then compares tokens. A short token (a vote label, a count) must appear in
the OCR exactly; a longer word may differ a little (OCR noise). Any token of
the text layer that the picture does not show makes the table UNCERTAIN.

Opt-in (TOMD_OCR=1) and only when the tesseract command is installed.
"""

def check_table(page, sec) -> str:
    """"" if the header (and a poll's votes) read the same in the picture, else a note."""
    # calls: _row_box, mismatched_tokens, _ocr
    # called by: classify.gate_tables

def mismatched_tokens(text_tokens: list[str], ocr_text: str) -> list[str]:
    """Text-layer tokens the OCR does not show."""
    # called by: check_table

def ocr_enabled() -> bool:
    # called by: classify.gate_tables

# + 2 private module-level names
```

<a id="lib-pdf-pagecache-py"></a>

## `lib/pdf/pagecache.py` ([source](../../lib/pdf/pagecache.py))

```python
"""One rawdict extraction per page, shared by the readers that need characters
(the rule-band reader and the poll reader each extracted it on their own).
The cache lives on the document object, so it goes away with it (keying a
global cache by id() returned another document's text once ids were reused).
"""

def clear() -> None:
    """Kept for callers; the cache is per document and needs no clearing."""
    # called by: pdf._run_pipeline

def hidden_chars(page, drawings=None) -> list:
    """bboxes of characters an opaque box drawn after them covers (slide decks hide
    the rows of a build under a white box): text the page does not show
    """
    # calls: evidence.reader_error
    # called by: remove_covered_text

def rawdict(page):
    # calls: _dedup_raw
    # called by: words_in, poll.extract_poll_tables, ruled._grid_tables_in, ruled.extract_ruled_tables

def remove_covered_text(pages) -> int:
    """redact (in memory) the characters hidden_chars finds; pages changed"""
    # calls: hidden_chars, evidence.reader_error
    # called by: pdf._upright_page

def words_in(page, bbox):
    """The page's words whose centre lies in bbox. Words are taken whole from the
    whole page: a clipped extraction drops glyphs whose ink falls outside the clip
    (a period on the baseline below a region's edge) and splits the word there.
    """
    # calls: _dedup_words, rawdict
    # called by: classify.gate_tables

# + 2 private module-level names
```

<a id="lib-pdf-paper-model-py"></a>

## `lib/pdf/paper_model.py` ([source](../../lib/pdf/paper_model.py))

```python
"""Paper-level confidence model (P(no silent table error)), fitted by paper_calibration.py on the existing keys
(2026-10-23, after the determinism and locality commits: corrected page-restricted labels, tuning sets
only; calibrated base rate, weak discrimination, cross-validated AUC 0.59).

MODEL gives a raw score; BANDS maps it to the rate measured on the keys
(cross-validated, adjacent bands pooled where the order breaks), with its
95% Wilson interval and the number of papers behind it.
"""

BANDS = ...

MODEL = ...
```

<a id="lib-pdf-poll-py"></a>

## `lib/pdf/poll.py` ([source](../../lib/pdf/poll.py))

```python
"""WG21 poll result tables.

WG21 papers and minutes record straw polls in a fixed shape: a header line
"SF F N A SA" (Strongly For, For, Neutral, Against, Strongly Against) with
the vote counts in the line below, one count under each header. Authors draw
it in many ways - ruled, unruled, inside a coloured box, tab-aligned - and
the other table sources miss most of them (too few rules, no tags), so this
source looks for the shape itself.

A poll is recognised when a text line consists of exactly the five header
tokens in order. Rows of numbers directly below whose numbers sit under the
header columns are its counts (up to _MAX_ROWS). A suggested poll with no
counts yet is emitted with an empty vote row when one is drawn under the
header, otherwise as a header-only table. A header followed by text on
the same line ("SF F N A SA: 4 5 1 0 0") is inline prose and is left alone.
"""

def extract_poll_tables(page, page_num: int, words_hint=None) -> list[TableCandidate]:
    """Poll result tables on one page. `words_hint` (the page's words, already
    extracted) lets a page with no vote label skip the character extraction.
    """
    # calls: _clean, _split_pipes, pagecache.rawdict, ruled._page_words, _baseline_lines, vote_header, _label_cells, _header_prefix, _row_cells, _strip_zero_width, ruled._chars_to_lines, ruled._word_chars, +1 more
    # called by: pdf._run_pipeline

def vote_header(labels: list[str]) -> bool:
    """These cell texts form a poll header (see VOTE_LABELS)."""
    # called by: _header_prefix, extract_poll_tables, table.class_check

# Vote labels and their side: +1 for, 0 neutral, -1 against. A header is a
# line made only of these, in that order (for ... neutral ... against):
# "SF F N A SA", "SF WF N WA SA", "F N A", "Strongly Favor ... Strongly Against".
VOTE_LABELS = ...

# + 7 private module-level names
```

<a id="lib-pdf-qa-py"></a>

## `lib/pdf/qa.py` ([source](../../lib/pdf/qa.py))

```python
"""Quality assurance metrics and scoring for Markdown conversion output.

Parses the Markdown output with mistune to validate structure from
the reader's perspective, not from pipeline internals.

DESIGN CONSTRAINT: compute_metrics() takes only a Markdown string.
No page count, no file format, no pipeline internals. Every signal
must be derivable from the Markdown text alone. This keeps scoring
format-agnostic (works on PDF output, HTML output, or any Markdown)
and prevents coupling between the scorer and the converter.
"""

@dataclass
class QAMetrics:
    """Per-document quality metrics computed purely from Markdown text."""
    file: str = ''
    total_chars: int = 0
    heading_count: int = 0
    max_heading_level: int = 0
    code_block_count: int = 0
    list_count: int = 0
    table_count: int = 0
    front_matter_count: int = 0
    has_doc_number: bool = False
    uncertain_count: int = 0
    unfenced_code_lines: int = 0
    paragraph_count: int = 0
    empty_output: bool = False
    score: int = 100
    issues: list[str] = field(default_factory=list)

def compute_metrics(md_text: str, file: str = '') -> QAMetrics:
    """Compute QA metrics by parsing the Markdown output with mistune.

    Takes only the Markdown text. No page count, no format hints.
    Everything is derived from the text itself.
    """
    # calls: QAMetrics, _parse_front_matter, _count_unfenced_code, _score
    # called by: _qa_one

def run_qa_report(paths: list[Path], json_path: Path | None = None, workers: int = 1, timeout: int = 120) -> None:
    """Run QA scoring on a list of PDF/HTML files and print a ranked report.

    Uses *workers* parallel processes (default 1 = sequential).
    *timeout* is seconds of no progress before aborting remaining files.
    """
    # calls: _qa_metrics_from_dict, QAMetrics, _qa_one
    # called by: main.main

# + 8 private module-level names
```

<a id="lib-pdf-records-py"></a>

## `lib/pdf/records.py` ([source](../../lib/pdf/records.py))

```python
"""Content record-pattern reader: a table seen as runs of records that share a
schema of kinds, with no geometry.

The text layer gives a region's lines in reading order. Each line has a kind
(an identifier such as P1234R0 or [expr.add], a date, a number, a check mark,
code, words). In most PDFs a table's cells come out one per line, so a table
reads as a sequence whose kinds repeat with a period: name, number, number,
name, number, number, ... A run of at least three periods with at least two
kinds in a period is a run of records; the period is the column count and
each period a row. The k lines just before the run become the header when
they are short labels.

Rows and columns come from the text's own pattern (meaning), not from
positions, so this is a different way to see a table from every other
reader. Measured on the answer keys first: alone it is noisy (code listings
repeat too), so it reads only regions other cues nominated, never votes for
HIGH, and is an alternative that escalation may switch to when the emitted
reading fails verification and this one passes.
"""

def line_kind(text: str) -> str:
    """One kind for a line: its tokens' kind when they all share one, else 'mixed'."""
    # calls: _token_kind
    # called by: read_region

def periodic_runs(kinds: list[str]) -> list[tuple[int, int, int]]:
    """(start, period, records) for runs whose kinds repeat with a period, longest first."""
    # called by: read_region

def read_region(page, page_num: int, bbox) -> list[TableCandidate]:
    """Every run of records in the region (longest first, not overlapping), each
    with its header and its own box; none unless together they cover most of
    the region's lines (a region holding two stacked tables reads as two).
    """
    # calls: _lines_in, line_kind, _text, periodic_runs, types.TableCandidate
    # called by: records_candidates

def records_candidates(pages, regions) -> list[TableCandidate]:
    """The record-pattern reading of every located region (page, bbox)."""
    # calls: read_region
    # called by: pdf._run_pipeline

# + 3 private module-level names
```

<a id="lib-pdf-relations-py"></a>

## `lib/pdf/relations.py` ([source](../../lib/pdf/relations.py))

```python
"""Stage 1: the relationship record and the relational checker.

A table asserts relationships between the words of its region: two words
share a row, share a column, share a cell. The page shows others, observed
from the word positions and drawings: two words sit on one baseline, two
lines start at the same x, a drawn rule or a row gap lies between two lines,
a gutter lies between two words. Each record keeps where it came from
(observed on the page, or inferred by a reader) - never mixed.

The checker lists every contradiction between the two as a violated
relationship, by dimension, instead of stopping at the first failure:

  rows     words on one baseline put in different rows (a row split), or a
           drawn rule / row gap inside one row (rows merged)
  columns  words across a gutter put in one cell (a column merged), or one
           line's words split across cells with no gutter between (a column
           split)
  cells    a page word in no cell, or in two (extent: cut short / swallowed)

No output change: the record goes into the table's metadata and the evidence
record, and drives per-dimension confidence (stage 2) and diagnosis.
"""

@dataclass
class RelationRecord:
    observed: list = field(default_factory=list)  # (kind, a, b, source)
    asserted: list = field(default_factory=list)  # (kind, a, b, reader)
    violations: list = field(default_factory=list)
    def by_dimension(self) -> dict: ...

@dataclass
class Violation:
    dimension: str  # rows | columns | cells
    kind: str  # row split, rows merged, column merged, column split, word outside, word in two cells
    where: tuple  # (row, col) or a word's text and position
    evidence: str  # the observed relationship it contradicts and where it came from

def check(rows_boxes: dict, words: list, hrules=(), reader: str = '?', mono=frozenset()) -> RelationRecord:
    """rows_boxes: {(row, col): bbox of the cell's text}; words: fitz word tuples in the
    table's region; hrules: (y, x0, x1) of drawn horizontal rules - only those
    crossing most of the table are row boundaries (an underline, a strike-through
    or one cell's own rule is not).
    """
    # calls: RelationRecord, _cell_of, Violation, _recurs
    # called by: record_for

def record_for(sec, words, hrules=()) -> RelationRecord:
    """The relationship record of an emitted table section (cells from its spans)."""
    # calls: check
    # called by: classify._repair_stray_words, classify.gate_tables

# + 2 private module-level names
```

<a id="lib-pdf-repair-py"></a>

## `lib/pdf/repair.py` ([source](../../lib/pdf/repair.py))

```python
"""Stage 3 (relationship plan): blind smallest-set repair and inferred cells.

A flagged table whose region holds page words that lie in no cell (the
relational checker's "word outside every cell") lost text. The smallest
correction that explains it, made without the answer key (amendment D):

  - a stray word inside a column's span and a row's span belongs to that
    cell: it is placed there, in reading order;
  - stray words outside every row (above the first, between two, below the
    last) form an inferred row, one cell per column;
  - a stray word in no column means the column structure itself does not
    explain it: no smallest repair, the table is left as it was.

The repair is kept only when the relational check of the result has fewer
violations and no kind it did not have before. Inferred cells are marked in
the output (a comment after the table) and the table stays UNCERTAIN; the
first reading, the stray words and the repair go in the metadata
(amendment E: no erasure).
"""

def place_stray_words(columns: list, words: list, nl: Span):
    """(new columns, inferred [(row, col)], stray words) or None when the stray
    words are not explained by the table's own rows and columns.
    """
    # calls: _box, _lines, _place, _span_for, _join
    # called by: classify._repair_stray_words

# + 5 private module-level names
```

<a id="lib-pdf-rowbands-py"></a>

## `lib/pdf/rowbands.py` ([source](../../lib/pdf/rowbands.py))

```python
"""Rows bounded by drawn rules (2026-10-24).

In a drawn grid whose records are separated by horizontal rules (comment forms such as national-
body ballots), every text line between the same pair of rules belongs to one record. A reader
that cuts a multi-line record into several rows leaves the continuation lines as rows whose key
(first) column is empty. Such a row is joined to the row above when it lies wholly below that
row and no drawn rule crosses the two rows' combined extent; the joined cell keeps its lines
("
" span between them).

Only joins, never splits. Applies to single-page readings inside a ruled grid: at least
MIN_RULES horizontal rules each covering 60% of the table's width (segments at one height
merged). Measured on the tuning sets (REPORT.md, rule-bounded rows, version 4b): 14 tables
changed, all better, none worse; a version without the empty-key condition broke tables whose
grids rule only the header and border, and one testing only the gap between rows merged across
a rule running through a reading's rows.
"""

def merge_rule_bands(sec, rules) -> int:
    """Join empty-key continuation rows into the record above within one rule band; returns the
    number of rows joined. rules: the page's horizontal rule segments (y, x0, x1).
    """
    # calls: _full_rules, _text, types.Span
    # called by: pdf._run_pipeline

# a row filling this share of its other (non-key) columns is a record of its own, never a
# continuation (user, 2026-10-24): in a grouped grid the first column is blank on every row of a
# group after the first, and those rows are full. 0.67 is the strictest value that keeps every
# tuning-set gain (0.5 keeps 7 of 14).
MAX_FILL = 0.67

MIN_RULES = 4

MIN_SEGMENT = 15.0  # pt: shorter strokes are not row separators

# + 2 private module-level names
```

<a id="lib-pdf-ruled-py"></a>

## `lib/pdf/ruled.py` ([source](../../lib/pdf/ruled.py))

```python
"""Table detection from ruling lines (vector drawings).

An extractor independent of the MuPDF text blocks that table.py uses: it
looks only at the lines and thin rectangles a page draws, and at character
positions to fill cells.

Two techniques:
  Grid tables: PyMuPDF's page.find_tables(strategy="lines") for tables
    ruled in both directions (Word, Google Docs, LibreOffice exports).
  Rule-band tables: LaTeX/booktabs and ReportLab tables draw only
    horizontal rules. Rules sharing an x-extent form a group; rows come
    from the bands between rules, columns from x positions where a column
    starts in most rows, plus x ranges that no word covers.

Cell text is rebuilt from the page's characters (rawdict), grouped into
Lines and Spans the same way extract.py builds them, so fonts, bold,
italic and monospace survive. Words are assigned to a cell whole, by
their starting x, so text that overruns into the next column stays in its
own cell.

Known gaps: a booktabs table split by a page break is not detected (each
part has too few rules); column boundaries are ambiguous for tables with
very few rows. Both are caught downstream by the rule checks or by
disagreement with the other extractors.
"""

def closed_exempt(t) -> bool:
    """a closed grid's own layout explains its empty cells, unless a whole column is
    empty (a doubled rule read as a column of its own)
    """
    # called by: _bad_flags, sparse_mapping, table._is_bad

def drawn_spans(page, columns, spans) -> list[dict]:
    """the spans a closed grid's own lines allow: a span inferred from the text's
    position is dropped when a drawn line separates the cells it would join (the
    grid draws every cell it has; an empty drawn cell is not part of its neighbour)
    """
    # calls: _segments
    # called by: classify.gate_tables

def extract_ruled_tables(page, page_num: int, drawings=None) -> list[TableCandidate]:
    """All tables on one page that ruling lines reveal."""
    # calls: _unrotate, pagecache.rawdict, _page_chars, _page_words, _grid_tables, _column_ruled_tables, _bad_flags, evidence.current, table.table_flags, _horizontal_rules, _rule_groups, _overlaps, +2 more
    # called by: pdf._run_pipeline

def sparse_mapping(t) -> bool:
    """a closed grid of two or more drawn columns whose rows mostly fill only their first
    cell with a short label (a mapping where most entries have no counterpart): a table,
    not a framed paragraph under a lead-in line (whose single cells are prose)
    """
    # calls: closed_exempt
    # called by: _bad_flags, table._is_bad

def take_excluded_grids() -> list[TableCandidate]:
    """Grids the reader excluded since the last call (for the drop marks)."""
    # called by: pdf._run_pipeline

# a closed drawn grid's lines fix its cells: empty, merged and full-width cells are the
# author's layout there, not a misread (the content checks still apply)
CLOSED_GRID_EXEMPT = ...

# + 37 private module-level names
```

<a id="lib-pdf-scan-py"></a>

## `lib/pdf/scan.py` ([source](../../lib/pdf/scan.py))

```python
"""The region scan: check every piece that makes a table, then decide.

1. Areas: every place any scan nominated or excluded (the evidence record),
   merged per page. Nominating is not deciding; nothing nominated is lost.
2. Features per area, each with its information type (words, paths, tree,
   meaning, document): the classifier's layout features, which scans saw it
   and which rules excluded it, content checks on the best reading in the
   area (items per cell, fragments, header vs body, column shapes, first
   column as keys, shared code), and document cues (a caption nearby).
3. Likelihood that the area is a table: a logistic model fitted on the
   existing truth (scan_model.py), so it is fast and explainable; the top
   supporting and opposing features are recorded with the decision.
4. Bands: high (and two independent information types) -> may be trusted;
   middle -> build, UNCERTAIN; low -> possible-table mark; none -> recorded.
"""

def area_features(page, a, generator: str, doc_tagged: bool, measure=None, decided=None) -> dict:
    """Every enabled region-level check's evidence for one area (checks/); the
    last-resort tier only while decided(features) is False.
    """
    # calls: checks.run_region_checks, checks.AreaContext
    # called by: run_scan

def areas(record) -> list[dict]:
    """Nominated and excluded places, merged per page (half the smaller one overlapping)."""
    # calls: _inter, _area
    # called by: run_scan

def band(p: float, info_types: int) -> str:
    # called by: run_scan

def info_of(name: str) -> str:
    # called by: run_scan

def likelihood(x: dict, model: dict) -> tuple[float, list[tuple[str, float]]]:
    """P(table) and the features that pushed it most (signed contributions)."""
    # called by: data_or_format.likelihood_data, run_scan

def run_scan(path, record, tables, builds: list | None = None) -> list:
    """Score every area in the evidence record and decide by band.

    Emitted tables get their likelihood and top features in metadata; a HIGH
    table the scan rates below LOW is downgraded (reason recorded). Areas
    without a table come back as possible-table regions (page, bbox, reason,
    rows) for the build and mark bands; the rest are only recorded.
    """
    # calls: classify.generator, areas, _inter, _area, _table_boxes, likelihood, _at_mean, area_features, info_of, band, data_or_format.likelihood_data, _jev_tier, +1 more
    # called by: pdf._run_pipeline

# information type of each feature family (stage 0: same-type features do not
# stack like independent witnesses)
# document priors (2026-10-23): what the whole document is (tagged at all, which generator made
# it, how its prose is set) describes the document, not this area; they shape the likelihood
# but never count as an independent witness for an area (TOMD_DOC_PRIOR=0: the earlier count)
DOC_PRIOR = 'document prior'

# early stop (ledger ordering): an area whose likelihood without the last-resort
# tier is below this is not a table whatever that tier says. Measured on the
# 4991 tuning areas: below 0.02 (24% of areas) the full likelihood never
# exceeded 0.043 (LOW is 0.3); at 0.05 one area reached 0.26, too close.
EARLY_NONE = 0.02

# --------------------------------------------------------------- Jev tier
# Locality (2026-10-23): the tier batches up to TOMD_JEV_BUDGET areas into one prompt, so one
# area's answer can see other areas' text. It stays off; before it is ever switched on it must
# ask about one table per prompt (per-table evidence only).
# Off by default (TOMD_JEV=1 turns it on, with JEV_API_KEY or the keychain
# entry; the key is never printed or logged). Only areas the scan left
# undecided go, batched per paper (classify.jev_table_or_not), at most
# TOMD_JEV_BUDGET areas per paper; an answer counts only at JEV_SURE or more.
# Every answer and the Jev version go into the evidence record (and from
# there the paper summary).
JEV_SURE = 0.9

# + 6 private module-level names
```

<a id="lib-pdf-scan-model-py"></a>

## `lib/pdf/scan_model.py` ([source](../../lib/pdf/scan_model.py))

```python
"""Region scan model, fitted by train_scan.py on the existing truth sets."""

MODEL = ...
```

<a id="lib-pdf-spans-py"></a>

## `lib/pdf/spans.py` ([source](../../lib/pdf/spans.py))

```python
"""Span normalization - snap style boundaries to word edges.

When a bold or italic boundary falls inside a word (no whitespace
between adjacent spans with different styles), extend the styled
region to the word boundary. Monospace boundaries are exempt
because code boundaries are intentional.
"""

def normalize_spans(blocks: list[Block]) -> list[Block]:
    """Snap bold/italic style boundaries to word edges across all blocks.

    Monospace boundaries are exempt (code boundaries are intentional).
    """
    # calls: _normalize_line_spans, types.Line, types.Block
    # called by: pdf._run_pipeline

# + 7 private module-level names
```

<a id="lib-pdf-stacked-py"></a>

## `lib/pdf/stacked.py` ([source](../../lib/pdf/stacked.py))

```python
"""Stacked entries are one row each (table convention, "Rows: one row per entry").

Several entries stacked in one drawn band, on baselines shared across columns
("Linux / QNX / NetBSD" beside three function names), are one row each; a cell
whose text wraps is still one row (a wrap breaks at a space, so a line of one
token followed by another line is a new entry). Learned from the vision readers (Table
Transformer, Docling): a line is its own row unless something shows it wraps.

A row is split between two baselines when the lower baseline holds lines in
two or more columns, one of them the row's first column (where an entry's key
sits), and, in every column with a line on both baselines, the
upper line did not run to the column's edge (the next line's first word would
have fitted after it) and the lower line is not a word joined to the upper
one. Rows of C++ statements (a line ending in ; { or }, a preprocessor line, a
comment) are code blocks and are
never split, nor are rows holding a listing (monospace lines with words on them,
such as assembly); the header row and all-bold rows are left as they are.
"""

def apply(cands: list[TableCandidate]) -> list[TableCandidate]:
    # calls: split_stacked
    # called by: table.select_tables

def split_stacked(cand: TableCandidate) -> TableCandidate:
    # calls: _code_block, _height, _baseline, types.TableCandidate
    # called by: apply

# + 4 private module-level names
```

<a id="lib-pdf-structure-py"></a>

## `lib/pdf/structure.py` ([source](../../lib/pdf/structure.py))

```python
"""Dual-path comparison, heading intelligence, and document structuring."""

def compare_extractions(mupdf_blocks: list[Block], spatial_blocks: list[Block]) -> list[Section]:
    """Compare two extraction paths using per-page word-level multiset similarity.

    Groups blocks by page and computes a word-count overlap ratio for each
    page. High similarity = confident (PARAGRAPH). Low similarity = uncertain.
    Small uncertain regions below MIN_UNCERTAIN_WORDS are promoted to confident.
    """
    # calls: _block_words, _word_similarity, _make_paragraph_section, types.Section
    # called by: pdf._run_pipeline

def heading_confidence(has_number: bool, number_level: int, font_level: int | None, is_bold: bool, is_known: bool) -> tuple[int, Confidence]:
    """Determine heading level and confidence from multiple signals.

    Bold never determines heading level, but as a confirming signal
    it raises confidence by one tier.
    """
    # called by: structure_sections

def structure_sections(sections: list[Section], has_title: bool = False) -> tuple[dict, list[Section], int]:
    """Apply heading intelligence, paragraph grouping, and list detection.

    If has_title is True, the title was already extracted from front matter
    and no title detection is performed.

    Returns (metadata_dict, structured_sections, nesting_corrections).
    """
    # calls: _extract_metadata, _detect_body_size, _rank_font_sizes, _heading_level_from_number, heading_confidence, _detect_lists_by_position, _merge_paragraphs, _detect_code_blocks, _detect_lang_label, _classify_wording_sections, _demote_repeated_low_confidence_numbers, _validate_nesting
    # called by: pdf._run_pipeline

# + 22 private module-level names
```

<a id="lib-pdf-summary-py"></a>

## `lib/pdf/summary.py` ([source](../../lib/pdf/summary.py))

```python
"""Paper-level summary: what tomd did with this paper's tables, how sure it is,
and how unlike the measured papers this one is.

The output feeds AI analysis of WG21 papers, where a trusted-but-wrong
conversion is the costly failure, so every conversion carries:
  - tables trusted (HIGH), flagged (UNCERTAIN; of those, "likely correct":
    the words fit the drawn cells evenly) and marked (possible tables), with
    their pages; removed and skipped content; table types present;
  - an unfamiliarity score: how unlike the measured papers this one is
    (generator not seen in the measured sets, rare layout classes, the share
    of areas the scan left undecided, rotated text, no prose measure);
  - a paper-level confidence: the estimated chance that the paper's tables
    hold no silent error (a wrong table marked HIGH, or a table missed with
    no mark), from a model calibrated on the answer keys (paper_model.py).
    An unfamiliar paper never gets the familiar papers' figure: confidence
    is capped by unfamiliarity.
    Calibrated base rate, weak discrimination: refitted 2026-10-23 on the
    corrected (page-restricted) labels of the tuning sets, the stated figure
    matches the observed rate within its interval, but the score barely tells
    papers apart (cross-validated AUC 0.59): most papers get 0.80-0.90. Read
    it as the rate for papers like this one, not as a judgement of this
    paper's tables.

Machine-readable (result.summary, written as JSON beside the Markdown), a
short header comment in the Markdown, and a section in the prompts file.
"""

def build(result, sections, evidence, generator: str) -> dict:
    # calls: unfamiliarity, llmrepair.paper_record, confidence
    # called by: pdf._run_pipeline

def confidence(s: dict) -> dict | None:
    """The measured chance that this paper's tables hold no silent error: the
    rate on the answer keys for papers with a similar score, with its interval.
    An unfamiliar paper never gets the familiar papers' figure: it is capped
    by unfamiliarity, and the interval widens to match.
    """
    # calls: features
    # called by: build

def features(s: dict) -> dict:
    """The paper-level model's inputs."""
    # called by: confidence

def header_comment(s: dict) -> str:
    # called by: pdf._run_pipeline

def prompts_section(s: dict) -> str:
    # called by: pdf._run_pipeline

def unfamiliarity(generator: str, layouts: list[str], undecided: int, areas: int, rotated: bool, measured: bool, skipped: bool) -> tuple[float, list[str]]:
    """0 (like the measured papers) .. 1 (unlike them), with the reasons."""
    # called by: build

COMMON_LAYOUTS = {'poll', 'grid', 'rule-per-row', 'tagged', 'booktabs'}

# generators of the measured papers (dev, held-out, fresh .. fresh6)
KNOWN_GENERATORS = ...
```

<a id="lib-pdf-table-py"></a>

## `lib/pdf/table.py` ([source](../../lib/pdf/table.py))

```python
"""Table detection: the text-position detector, and selection across sources.

This module has two parts.

detect_tables() proposes tables from MuPDF text positions alone. It is one
of three independent table sources; the others are ruling lines (ruled.py)
and PDF accessibility tags (tagged.py). select_tables() compares all three
per region, picks one version, and sets its confidence (see the second half
of this file).

Text-position detection, two signals:
  Signal 1 (block structure): a block is columnar when it has 2+ lines whose
    x-starts have gaps > _COLUMN_GAP_THRESHOLD. Consecutive matching-column
    blocks form a table run.
  Signal 2 (geometric column profile): x positions that co-occur with other
    x positions in the same y-band across 2+ rows are confirmed table columns.
    Body text is always alone in its y-band and never qualifies.

Orphan absorption: single-line blocks whose x0 matches a confirmed column are
"orphans" - the first physical line of a wrapped table cell. They are absorbed
into the table run when the block following them is a confirmed table row
(one-block lookahead). Absorbed orphans are merged into the next row's first
cell so multi-line cells produce a single cell string.

Known gap: absorption is same-page only. A wrapped cell whose continuation
line is the first block on the next page is not absorbed - the table stops
at the last same-page row and the orphan appears in an uncertain region.
"""

def candidate_from_section(sec: Section) -> TableCandidate:
    """Wrap a detect_tables() section (cells are span lists) as a candidate."""
    # calls: types.Line, types.TableCandidate
    # called by: select_tables

def candidates_agree(a: TableCandidate, b: TableCandidate) -> bool:
    """Same grid shape and every cell matching."""
    # calls: _cells_agree
    # called by: select_tables

def class_check(cand: TableCandidate) -> str:
    """Why this table can be trusted from one source, or "".

    Each check is specific to how the table was built, and only used when
    the classifier puts the region in the matching layout class:
      - poll: exactly the SF F N A SA (or F N A) header, then rows that are
        all vote counts, or one all-empty row (a suggested poll);
      - grid: read from drawn cell boundaries, rectangular, no column or
        row left empty;
      - tags: from a well-formed structure tree, every row as wide as the
        table, no empty column.
    """
    # calls: _is_bad, poll.vote_header
    # called by: select_tables

def conservation_error(cand: TableCandidate, blocks: list[Block]) -> str:
    """Check that the text in the table's area went into its cells exactly once.

    The area is where the cells' own lines sit on each page. Every letter and
    digit of the page lines centred in that area must appear in the cells as
    often as on the page: a deficit is text the table lost (a dropped row,
    an overprinted word), a surplus is text it duplicated. Compared as
    character counts, so line breaks, hyphenation and spacing do not matter.
    Returns "" when conserved, else a note for the prompt.
    """
    # calls: _aligned_neighbour_row
    # called by: select_tables

def cross_reader_continuation(cands: list[TableCandidate], blocks: list[Block], furniture: frozenset = frozenset()) -> list[TableCandidate]:
    """A table continuing across a page is the same table whichever reader read
    each piece (user: preserve meaningful spatial relationships regardless of
    mechanism). After every reader's own stitching, a piece ending low on page N
    joins a piece from a different reader starting high on page N+1 under the
    same conditions as same-reader stitching: the same column count and column
    starts (or extent), no different header, nothing between them (page
    furniture aside). Polls are never joined this way. The joined table keeps
    the first piece's reader, is flagged 'cross-reader' and records both.
    """
    # calls: _page_span, _new_header, _same_columns, _text_outside, _overlap, _same_header, types.TableCandidate, evidence.current
    # called by: select_tables

def detect_tables(blocks: list[Block]) -> tuple[list[Section], list[Block]]:
    """Detect table regions from MuPDF block structure.

    Returns (table_sections, remaining_blocks).
    Table sections have kind=TABLE with high confidence.
    Remaining blocks are the non-table blocks for normal processing.
    """
    # calls: _find_column_xs, _block_column_positions, _columns_match, _is_column_aligned_orphan, types.Section
    # called by: pdf._run_pipeline

def diagram_boxes(page, page_num: int) -> list:
    """Areas of a page drawn as a diagram: a graph or flowchart draws edges as diagonal
    lines and arrowheads; a table uses horizontal and vertical rules only (tables inside
    figures too). Returned as the drawn shapes' bounding boxes, merged per drawing cluster.
    """
    # called by: pdf._run_pipeline

def join_split_words(cands: list[TableCandidate], blocks: list[Block]) -> None:
    """A word split by a narrow cell is still one word (user, 2026-10-21): a cell line
    that runs to the cell's right edge ending mid-token, followed by a line that
    continues the token, is joined without a space - when the joined token occurs
    elsewhere in the document and one of the pieces never occurs on its own there, or
    when the break splits one identifier (underscores in both pieces, the second piece not
    a name used on its own elsewhere) or one long number
    or paper name (a run of 5+ characters ending in a digit, broken before a remainder
    of at most two digits: "P0876R1" / "1", "20210" / "6") and a piece never occurs on
    its own. A name followed by a number ("SC 22") and a year followed by a version
    ("2022" / "17.14") are never joined.
    The next line is marked (joins_prev); cell text and spans honour the mark.
    """
    # called by: select_tables

def mark_matrix(cand: TableCandidate) -> bool:
    """A check-mark matrix (status, feature or compliance tables): row keys in
    the first column, and the filled cells beside them are marks. Sparse by
    design, so empty cells and sparse or ragged columns are not misreadings.
    """
    # called by: _is_bad, select_tables

def page_furniture(blocks: list[Block], min_pages: int = 3) -> frozenset:
    """Lines repeated at the same height on several pages once digits are
    normalised: running headers and footers with page numbers that header
    stripping missed (a header block holding the page number).
    """
    # calls: _furniture_key
    # called by: pdf._build_scan_tables, select_tables

def partial_reading(primary: TableCandidate, other: TableCandidate) -> bool:
    """True when `other` is tomd's text-position reading of part of a fully
    ruled table: same columns, and every one of its rows matches, cell for
    cell, a row of the ruled table in the same order. The text-position
    detector often stops early or starts late on ruled tables; a correct
    subset confirms the rows it saw rather than contradicting the rest.
    """
    # calls: _cells_agree, _all_bold
    # called by: select_tables

def remove_table_regions(blocks: list[Block], tables: list[Section]) -> list[Block]:
    """Drop the lines that fall inside any chosen table's region.

    A line inside the region whose text is not in the table is kept, so it
    stays in the document as ordinary text: never lose words to a table whose
    cells missed them.
    """
    # calls: types.Block
    # called by: pdf._run_pipeline

def select_tables(tomd_sections: list[Section], ruled: list[TableCandidate], tagged: list[TableCandidate], blocks: list[Block], polls: list[TableCandidate] = (), rejected: list[TableCandidate] | None = None, codepairs: list[TableCandidate] = (), content: list[TableCandidate] = (), generator: str = 'unknown') -> list[Section]:
    """Choose one table per region from the three extractors.

    Primary version by source priority (tags, polls, ruling lines, text positions),
    skipping versions that fail the rule checks. Confidence:
      - another source agrees cell for cell, or tomd's
        reading is a correct subset of a ruled table -> HIGH
      - only one source found the table            -> UNCERTAIN
      - other sources found it but disagree        -> UNCERTAIN, and every
        version is kept for the prompts file
      - the cells lose or duplicate text of the
        table's area (conservation_error)          -> UNCERTAIN
    A candidate that fails the rule checks and has no better version is
    dropped, so its blocks flow back into normal processing. Dropped
    candidates from the drawing and tag sources are appended to `rejected`
    when given: their area probably is a table, so flag.py marks it.
    """
    # calls: candidate_from_section, page_furniture, stitch_pages, cross_reader_continuation, split_at_headers, join_split_words, stacked.apply, evidence.current, table_flags, _is_bad, _row_top, _same_region, +14 more
    # called by: pdf._run_pipeline

def split_at_headers(cand: TableCandidate) -> list[TableCandidate]:
    """Two tables stacked in one reading: a different header row inside the body
    (short bold labels after a non-bold row) starts a new table (the user's
    header rule; an identical header repeated is the same table and stays).
    Single-page readings only; tags and polls delimit their own tables.
    """
    # calls: _is_header_row, types.TableCandidate, _bold_row, _same_header
    # called by: select_tables

def stitch_pages(cands: list[TableCandidate], blocks: list[Block], furniture: frozenset = frozenset()) -> list[TableCandidate]:
    """Join a table that ends one page with one that starts the next page.

    Requires the same column count and x-extent, and no text after the first
    part or before the second (headers and footers are already stripped from
    blocks) - a caption in between means two different tables. A header row
    that the PDF repeats on the continuation is dropped.
    """
    # calls: _new_header, _same_columns, _continuation_votes, _text_outside, _same_header, types.TableCandidate, evidence.current
    # called by: pdf._build_scan_tables, select_tables

def table_flags(cand: TableCandidate) -> list[str]:
    """Rule-based sanity checks. Flags in BAD_TABLE_FLAGS mean the grid is
    probably wrong; the others are informational.
    """
    # calls: _split_code_cell, _diagram_inside
    # called by: ruled._bad_flags, ruled.extract_ruled_tables, select_tables

def witness(primary: TableCandidate, agreeing: list[TableCandidate], cands: list[TableCandidate], blocks: list[Block]) -> dict:
    """Per property, the distinct information sources behind the agreeing readings."""
    # calls: _extent_open
    # called by: select_tables

BAD_TABLE_FLAGS = ...

# Each reader's measured accuracy within each generator family (reader_track.json, built by
# the PoC's reader_track.py from the development sets): competing readings of a region are
# ranked by it first - the reader that has been right more often for PDFs from this
# generator - then by the fixed priority. A family or reader with too few measured readings
# falls back to the reader's accuracy over all families, then to the priority alone.
CURRENT_GENERATOR = 'unknown'

# areas drawn as diagrams (diagonal lines, arrowheads): set per paper by the pipeline
# (diagram_boxes); a reading lying in one is a drawing, not a table
DIAGRAM_BOXES: dict = {}

NUM_JOIN_REFUSED = [0]  # how often the number rule refused a join (measurement)

# + 35 private module-level names
```

<a id="lib-pdf-tablemodel-py"></a>

## `lib/pdf/tablemodel.py` ([source](../../lib/pdf/tablemodel.py))

```python
"""Lossless table model and its semantic flattening to plain Markdown.

Internally a table keeps spans: {"r", "c", "rows", "cols", "kind"} (0-based,
r/c = the cell holding the text), detected from the page geometry. Markdown
has no spans, so `flatten` renders them by meaning (the convention in the
PoC's work/TABLE_CONVENTION.md):

  header    a header cell over sub-headers -> combined headers "Top / Sub",
            the top row removed (over plain data: kept once)
  label     a category spanning rows        -> repeated in each row
  data      a shared value spanning cells   -> kept once (first cell)
  title     a full-width title/section row  -> kept once (first cell)
  ambiguous                                  -> kept as printed, flagged

and `marker` writes every span into an HTML comment beside the table, so
the structure stays machine-readable. `flatten` works on any grid of cell
values given `empty` and `combine` callbacks, so the Markdown renderer
(cells of spans) and the scorer (cells of text) share it.
"""

def detect_spans(columns) -> list[dict]:
    """Spans read from the geometry of a table's cells (lists of spans).

    - header: a row-0 cell whose text runs over the column(s) to its right,
      which are empty in row 0, with sub-headers under them in row 1;
    - title: any other row whose only text runs across columns;
    - label/data: a cell vertically centred across rows below it whose
      cells in its column are empty (multirow); a cell aligned with the top
      of its row cannot be told from an empty cell below it, so it is left
      alone.
    """
    # calls: _box, _text
    # called by: classify.gate_tables

def flatten(grid, spans, empty, combine):
    """(new grid, kept spans) with the flattening convention applied."""
    # calls: _two_level
    # called by: emit._render_table_body, flatten_text

def flatten_text(rows, spans):
    """Text grid version (used by the scorer)."""
    # calls: flatten

def marker(spans) -> str:
    """<!-- tomd:merged ... --> for the spans (1-based rows/columns)."""
    # called by: emit._render_table_body

SEP = ' / '

# + 3 private module-level names
```

<a id="lib-pdf-tagged-py"></a>

## `lib/pdf/tagged.py` ([source](../../lib/pdf/tagged.py))

```python
"""Table detection from the PDF's accessibility tags (Tagged PDF).

When the producing application wrote a structure tree (Google Docs, Word,
LibreOffice, Typst, Chrome print), tables are explicitly marked up as
Table / TR / TH / TD elements. PyMuPDF exposes them per page through
get_text("dict") with TEXT_COLLECT_STRUCTURE: structure nodes appear as
blocks of type 2 that contain the text blocks they own.

Cross-page tables: a Table element continued on the next page appears on
both pages with the same structure index, so the parts are joined by
index; a row split by the page break (same TR index) is joined too.

Empty cells own no text, so a page's dict may omit them. Rows shorter
than the table are therefore re-aligned by x position against the column
positions of full rows.

Untagged PDFs (LaTeX/pdfTeX, ReportLab, most tools) simply yield nothing.
"""

def extract_tagged_tables(doc) -> list[TableCandidate]:
    """All tables marked up in the document's structure tree.

    When MuPDF reports structure-tree errors while reading the pages (some
    Word exports), every candidate gets the "tags-malformed" flag so table
    selection ranks it below the ruling-line version.
    """
    # calls: _page_tables, evidence.reader_error, _realign, types.TableCandidate
    # called by: pdf._run_pipeline

# + 5 private module-level names
```

<a id="lib-pdf-types-py"></a>

## `lib/pdf/types.py` ([source](../../lib/pdf/types.py))

```python
"""Shared data types, constants, and precompiled regex patterns for PDF conversion."""

@dataclass
class Block:
    """A group of lines forming a paragraph-level unit."""
    lines: list[Line] = field(default_factory=list)
    bbox: tuple[float, float, float, float] = (0, 0, 0, 0)
    page_num: int = 0
    @property
    def font_size(self) -> float:
        """Most common font size among lines (one vote per line)."""
    @property
    def text(self) -> str: ...

class Confidence(Enum):
    """Confidence level for structural classification decisions."""
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    UNCERTAIN = 'uncertain'

@dataclass
class Line:
    """A sequence of spans forming a single line of text."""
    spans: list[Span] = field(default_factory=list)
    bbox: tuple[float, float, float, float] = (0, 0, 0, 0)
    page_num: int = 0
    @property
    def font_size(self) -> float:
        """Maximum font size among non-whitespace spans."""
    @property
    def is_bold(self) -> bool: ...
    @property
    def text(self) -> str: ...

@dataclass
class PageEdgeItem:
    """A text item near the top or bottom of a page, used for header/footer detection."""
    text: str
    y: float
    page_num: int
    bbox: tuple[float, float, float, float] = (0, 0, 0, 0)

@dataclass
class Section:
    """A classified region of the document."""
    kind: SectionKind
    text: str
    confidence: Confidence = Confidence.HIGH
    heading_level: int = 0
    lines: list[Line] = field(default_factory=list)
    mupdf_text: str = ''
    spatial_text: str = ''
    page_num: int = 0
    font_size: float = 0.0
    metadata: dict[str, str | list[str]] = field(default_factory=dict)
    columns: list[list[list[Span]]] = field(default_factory=list)
    fence_lang: str = 'cpp'
    indent_level: int = 0

class SectionKind(Enum):
    """The structural role of a document section."""
    TITLE = 'title'
    METADATA = 'metadata'
    HEADING = 'heading'
    PARAGRAPH = 'paragraph'
    LIST = 'list'
    CODE = 'code'
    TABLE = 'table'
    UNCERTAIN = 'uncertain'
    WORDING = 'wording'
    WORDING_ADD = 'wording-add'
    WORDING_REMOVE = 'wording-remove'

@dataclass
class Span:
    """A run of text with uniform font properties."""
    text: str
    font_name: str = ''
    font_size: float = 0.0
    bold: bool = False
    italic: bool = False
    monospace: bool = False
    bbox: tuple[float, float, float, float] = (0, 0, 0, 0)
    origin: tuple[float, float] = (0, 0)
    color: int = 0
    link_url: str | None = None
    wording_role: str | None = None

@dataclass
class TableCandidate:
    """A table proposed by one independent extractor, before selection.

    rows[r][c] is the list of Lines in that cell (several Lines when the
    cell wraps). bboxes maps page_num -> bbox of the table's part on that
    page; a table continued across a page break has several entries.
    """
    source: str  # "tags" | "grid" | "rules" | "tomd"
    rows: list[list[list[Line]]]
    bboxes: dict[int, tuple[float, float, float, float]] = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)
    def cell_text(self, r: int, c: int) -> str:
        # called by: TableCandidate.text_rows
    @property
    def pages(self) -> list[int]: ...
    @property
    def shape(self) -> tuple[int, int]: ...
    def text_rows(self) -> list[list[str]]:
        # calls: TableCandidate.cell_text

def compute_bbox(bboxes: list[tuple]) -> tuple[float, float, float, float]:
    """Compute the bounding box enclosing all given bbox tuples.

    Raises ValueError (via min/max) if bboxes is empty. Callers must
    ensure at least one bbox is present.
    """
    # called by: cleanup._join_cross_page, extract.extract_spatial

def is_readable(text: str) -> bool:
    """Return True if text looks like real content rather than encoded garbage.

    Heuristic check that rejects PDFs with very low alphanumeric content,
    such as scanned-image-only PDFs or CID-encoded artifacts that produce
    mostly non-alphanumeric output.
    """
    # called by: pdf._run_pipeline

AUDIENCE_RE = re.compile('Audience[:\\s]+(.+)', re.IGNORECASE)

BULLET_CHARS = frozenset('•‣●◦⁃∙▪▫')

BULLET_RE = re.compile('^[\\s]*[-*' + ''.join(BULLET_CHARS) + ']\\s+')

COMPOUND_PREFIXES = ...

# Line-anchored pattern targeting "Document Number: PXXXXRN" field lines in
# PDF block text. More restrictive than DOC_NUM_RE in lib/__init__.py, which
# is a broad substring match used for header stripping and HTML contexts;
# both patterns share the core DOC_NUM_PATTERN shape.
DOC_FIELD_RE = ...

EDGE_ITEMS_PER_PAGE = 3

FALLBACK_BODY_SIZE = 11.0

FALLBACK_FONT_SIZE = 12.0

KNOWN_SECTIONS = ...

LINE_SPACING_RATIO = 1.8

MIN_UNCERTAIN_WORDS = 10

NUMBERED_LIST_RE = ...

PAGE_NUM_RE = re.compile('^\\d+$|^[Pp]age\\s+\\d+|^\\d+\\s+of\\s+\\d+')

PARA_SPACING_RATIO = 2.5

# Minimum pages a text must appear on (as fraction) to be a header/footer
REPEATING_THRESHOLD = 0.5

REPLY_TO_RE = ...

# Section number at the start of a line with required trailing content
# (used for heading detection); shares the core shape with
# SECTION_NUM_PREFIX_RE in lib/__init__.py.
SECTION_NUM_RE = re.compile(f'^({SECTION_NUM_PATTERN})\\s+(.+)')

# Similarity threshold for dual-path comparison (word-level)
SIMILARITY_THRESHOLD = 0.85

TERMINAL_PUNCTUATION = frozenset('.?!:')

# Spatial rule thresholds (relative to font size)
WORD_GAP_RATIO = 0.3

# Y-position tolerance for header/footer matching across pages
Y_TOLERANCE = 2.0
```

<a id="lib-pdf-validate-py"></a>

## `lib/pdf/validate.py` ([source](../../lib/pdf/validate.py))

```python
"""Round-trip self-verification of an extracted table against the page.

A table read by only one source has no second opinion. Instead of a second
extractor, put the extracted grid back onto the page and check that it is
consistent with where the words actually are:

  - every word in the table's area falls in exactly one cell's box
    (no cell boxes overlap, no word is outside every cell);
  - each cell's words, read in page order (top to bottom, left to right),
    spell the cell's text;
  - rows are stacked: a row's band does not overlap the next row's band;
  - columns are side by side: column bands keep their order and do not
    overlap, except a cell that is alone in its row (a title bar, a
    spanning header), which may cover several columns.

A table that passes is consistent with the page geometry. Whether that is
enough to trust it alone is measured per class before it is used (see
classify.gate_tables).
"""

def add_header_above(sec, words):
    """The line just above the table, aligned with its columns, is its header
    (the region started below it). `words` must include the line above.
    """
    # calls: _contrasts, _with_columns, types.Span

def cell_text(cell) -> str:
    """A cell's text as tomd renders it: spans of a line joined as they are
    (they carry their own spaces: "has_degree<G>", "C++26"), lines joined
    with a space. Joining spans with spaces broke code into "has_degree < G >"
    and made correct tables fail the word-boundary check.
    """
    # called by: _contrasts, verify_layout

def escalate(sec, words, reason: str, depth: int = 2):
    """(re-read section, moves) that passes verification, or (None, [])."""
    # calls: verify_layout
    # called by: classify.gate_tables

def resegment_rows(sec, words):
    """Rebuild row boundaries where both votes agree: a new row where most
    columns start an item AND the gap above is row spacing; a continuation
    where neither holds; otherwise the boundary stays as it was. Code is
    never re-segmented (its lines belong to one listing).
    """
    # calls: _code_row, _gap_threshold, _lines_of, _newline_span, _row_baselines, _join_lines, _with_columns

def split_hidden_column(sec, words):
    """A column whose cells have a wide gap at the same x is two columns:
    split every cell of it at that x (spans left and right of the gap).
    """
    # calls: _lines_of, _newline_span, _join_lines, _with_columns

def split_stacked_rows(sec, words):
    """Rows whose cells hold several entries on shared baselines become one
    row per baseline (the drawn cell grouped several entries).
    """
    # calls: _newline_span, _lines_of, _column_rights, _code_row, _wraps, _yc, _join_lines, _with_columns

def switch_reader(sec, words):
    """Another source's reading of the same region, the first that verifies.

    The content builder reads rows and columns from word positions, the same
    information the verifier checks, so it passes by construction: it may
    replace a reading that also came from words (tomd, the rule-band reader's
    columns), never one whose rows and columns come from drawn paths or the
    structure tree (grid, tags) - that would be one witness checking itself.
    """
    # calls: _with_columns, verify_layout

def verify_layout(sec: Section, words: list) -> str:
    """"" when the grid is consistent with the page, else what failed.

    `words` are the page's words (fitz "words" tuples) in the table's area.
    """
    # calls: _cell_boxes, _inside, cell_text, _tokens, _gap_threshold, _code_row, _row_baselines, _lines_of, _line_ys
    # called by: classify.gate_tables, escalate, switch_reader, verify_pieces

def verify_pieces(sec, words_on) -> str:
    """A table stitched across pages: each piece against its own page's
    words (words_on(page, bbox)), then the whole by its parts. "" when every
    piece verifies, else "page N: what failed".
    """
    # calls: _with_columns, verify_layout
    # called by: classify.gate_tables

# + 16 private module-level names
```

<a id="lib-pdf-visibility-py"></a>

## `lib/pdf/visibility.py` ([source](../../lib/pdf/visibility.py))

```python
"""Text the PDF holds but the page does not show.

A PDF's text layer can carry text a reader never sees: invisible render mode,
zero opacity, text clipped away, text outside the page, text under something
drawn over it, text the colour of what is behind it, text too small to see.
Most of it is accidental (LaTeXiT base64 blobs, slide builds, clipped figure
labels); some could be deliberate (instructions aimed at the model that reads
the Markdown). Either way it is not the paper as people read it.

Each page is classified once, from the paint trace (get_texttrace: render mode,
colour, opacity, size, drawing order) and the paint log (get_bboxlog: what was
drawn when). Text of a removable class is redacted from the in-memory page
before any reader sees it, and every region is listed - page, box, why, and its
text - at the end of the Markdown and in the summary, so nothing is lost and
nothing hidden is presented as the paper's words. The rules are the cheap,
deterministic classes of work/hidden_text/scan.py (HIDDEN_TEXT.md), kept to the
ones whose precision on the corpus allows removal:

  invisible-render-mode  render mode 3/7, not over an image (an image under it is
                         a scan's OCR layer: the only text of the page, kept)
  opacity-0              fill opacity <= 0.05, not over an image (macOS emoji are
                         images under a transparent copy of the character: kept)
  clipped                kept by get_text(flags=0), dropped by TEXT_CLIP
  tiny                   size < 1 pt and glyph box < 1.5 pt high, on a page with
                         no Type3 font (old Type3 text reports 0.24 pt sizes)
  under-image            every character under an opaque image drawn later
  same-colour            the colour of a known background under every character
                         (the page, or an opaque rectangle; anything else under it
                         - an image, a shading, a curved path - is unknown: kept)
                         These two guess at what is under the text, so each is
                         confirmed by the picture: the region is rendered as is and
                         with the text redacted, and the text is kept if it shows
                         (white text on a black glyph drawn first; an image drawn
                         with a blend mode: p2988r6, n5024, p3389r0)
  under-box              under an opaque rectangle drawn later; removed by
                         pagecache.remove_covered_text, only listed here
  off-page               outside the page box; MuPDF drops it, only listed here

A hidden run that duplicates visible text at the same place (an invisible copy
of a visible line) is kept: the page shows that text. TOMD_VISIBILITY=0 turns
the check off.
"""

def check_page(page) -> list[dict]:
    """classify the page once per document, record the regions on the document,
    and return them (before any redaction: the caller removes them)
    """
    # calls: classify, evidence.reader_error
    # called by: pdf._upright_page

def classify(page) -> list[dict]:
    """The page's text that the page does not show, as regions:
    {page, bbox, why, chars, text, action, points}; points are the character
    centres to redact (empty when the text is kept or already gone).
    """
    # calls: _clipped_origins, _image_masks, _inside, _rgb, _centre, _text, _shows
    # called by: check_page

def discards(regions: list[dict]) -> list[tuple]:
    """the Removed-content lines: one per reason, with its pages"""
    # calls: summary
    # called by: pdf._run_pipeline

def markdown(regions: list[dict]) -> str:
    """the list at the end of the Markdown: each region's page, box, reason and
    text, quoted in a code fence - shown to an analyst, never read as the paper
    """
    # calls: _fence
    # called by: pdf._run_pipeline

def regions_of(doc) -> list[dict]:
    """every region recorded for the document, in page order"""
    # called by: pdf._run_pipeline

def remove_hidden_text(page, regions) -> bool:
    """redact (in memory) the characters of the removable regions; True if any"""
    # called by: pdf._upright_page

def summary(regions: list[dict]) -> dict:
    """the summary's `visibility` object"""
    # called by: pdf._run_pipeline, discards

WHY_TEXT = ...

# + 8 private module-level names
```

<a id="lib-pdf-wg21-py"></a>

## `lib/pdf/wg21.py` ([source](../../lib/pdf/wg21.py))

```python
"""WG21-specific metadata extraction from PDF blocks.

Parses the metadata block at the top of WG21 papers (document number,
date, audience, reply-to) from the raw MuPDF block structure, before
table detection or structuring runs.
"""

def extract_metadata_from_blocks(blocks: list[Block], text_colors: dict[float, float] | None = None) -> tuple[dict, set[int]]:
    """Extract WG21 metadata from the first blocks of page 0.

    PDF block-level scan (pathway 2 of 3). Higher precedence than
    structure._extract_metadata; both are merged in convert_pdf with this
    result winning on key conflicts.

    Handles two formats:
      - Scrivener: each field is its own block (label on line 0, value on line 1+)
      - Google Docs: multiple fields in one block (each line has label: value)

    Title is chosen by two signals: largest font size (primary) and
    darkest color (secondary, via space-color proxy for Type 3 fonts).

    Returns (metadata_dict, consumed_block_indices).
    Metadata dict keys: "title", "document", "date", "audience", "reply-to".
    All keys are optional; only fields found in the PDF are included.
    "reply-to" value is a list of "Name <email>" strings.
    """
    # calls: _clean, _lookup_lightness, _store_field, _parse_authors
    # called by: pdf._run_pipeline

# Maximum number of continuation blocks consumed after a reply-to label.
REPLY_TO_CONTINUATION_CAP = 5

# + 4 private module-level names
```

<a id="lib-pdf-worddict-py"></a>

## `lib/pdf/worddict.py` ([source](../../lib/pdf/worddict.py))

```python
"""A fixed English word list for deciding line-end hyphens in table cells (2026-10-23).

The decision used to rest on the paper's running text, which is outside the table (locality),
and was wrong where the paper never wrote the word whole ("re-gion", "illformed"). The word list
is the system's Webster's Second (/usr/share/dict/web2), used only when its contents match the
pinned hash, so the output never depends on which word list a machine happens to have; without
it the earlier behaviour stands.
"""

def available() -> bool:
    # calls: words
    # called by: emit._join_hyphenated

def is_word(w: str) -> bool:
    """w, or w with a common inflection removed, is in the word list (False without one)."""
    # calls: words
    # called by: emit._join_hyphenated

@lru_cache(maxsize=1)
def words() -> frozenset | None:
    # called by: available, is_word

DICT_PATH = Path('/usr/share/dict/web2')

DICT_SHA256 = ...
```

<a id="lib-pdf-wording-py"></a>

## `lib/pdf/wording.py` ([source](../../lib/pdf/wording.py))

```python
"""Wording section detection via multi-signal HSV color + drawing analysis.

Detects ins/del markup in WG21 PDF papers by combining three signals:
  1. Block-level color contamination filter - blocks containing non-wording
     chromatic colors (purple, orange, cyan) are syntax-highlighted code
     and are skipped entirely.
  2. Line-level wording detection - lines where the majority of non-link
     characters are green/red, or where green/red spans appear on an
     otherwise-black line (partial-line wording pattern).
  3. Span-level classification - green spans become ins; red spans with
     a confirmed strikethrough drawing become del.

Hyperlinks (span.link_url set) are excluded from all checks and fractions.
Insertions require no drawing decoration. Deletions require a strikethrough
drawing whose width overlaps at least 30% of the span to avoid matching
table borders and decorative rules.
"""

def classify_wording(blocks: list[Block], page_drawings: dict[int, list]) -> list[str]:
    """Classify spans as ins/del/context using multi-signal analysis.

    Three-layer filter:
      1. Blocks with foreign chromatic colors (not green/red/blue) are
         skipped — they are syntax-highlighted code, not wording markup.
      2. Lines qualify if either the majority (>50%) of non-link characters
         are green/red, or if any green/red spans appear with the remaining
         text being black (partial-line wording pattern).
      3. Green spans on qualifying lines become ins (no drawing required).
         Red spans become del only with a confirmed strikethrough drawing.

    Sets span.wording_role on matching spans.
    Returns an empty list (reserved for future diagnostic messages).
    """
    # calls: _block_has_foreign_colors, _line_wording_fraction, _line_has_wording_on_black, is_green_ins, is_red_del, _match_strikethrough, _is_chromatic, _color_int_to_rgb
    # called by: pdf._run_pipeline

def collect_line_drawings(page) -> list[tuple[float, float, float, tuple]]:
    """Collect horizontal line drawings from a page for decoration detection.

    Returns list of (y, x0, x1, color_rgb) for horizontal lines.
    """
    # calls: evidence.reader_error
    # called by: pdf._run_pipeline

def is_green_ins(color_int: int) -> bool:
    """True if color is in the green hue range with sufficient saturation."""
    # calls: _hsv
    # called by: _is_wording_color, classify_wording

def is_red_del(color_int: int) -> bool:
    """True if color is in the red hue range with sufficient saturation."""
    # calls: _hsv
    # called by: _is_wording_color, classify_wording

# + 11 private module-level names
```

<a id="lib-similarity-py"></a>

## `lib/similarity.py` ([source](../../lib/similarity.py))

```python
"""String similarity algorithms for fuzzy matching.

Two independent algorithms with per-algorithm thresholds:
  1. SequenceMatcher - character-level (difflib, stdlib)
  2. Jaccard - word-level set overlap

A 200-character circuit breaker protects against expensive
comparisons on paragraph-length strings.
"""

def similar(a: str, b: str) -> bool:
    """True if EITHER algorithm scores above its calibrated threshold.

    The per-string check is lenient because the caller (TOC detection)
    provides a second guard via the 3+ consecutive run requirement.
    Identical strings short-circuit to True regardless of length; the
    200-char gate only protects against expensive fuzzy-compare work.
    """
    # calls: _sequence_similarity, _jaccard_similarity
    # called by: toc.find_toc_indices

# + 2 private module-level names
```

<a id="lib-toc-py"></a>

## `lib/toc.py` ([source](../../lib/toc.py))

```python
"""Table of Contents detection.

Format-agnostic: operates on plain strings and returns indices.
No dependency on PDF or HTML converter types.
"""

def find_toc_indices(texts: list[str], headings: set[str], structural_hints: list[bool] | None = None) -> set[int]:
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
    # calls: _normalize_toc_entry, similarity.similar, _first_line, _is_toc_label
    # called by: pdf._run_pipeline

# + 3 private module-level names
```

<a id="main-py"></a>

## `main.py` ([source](../../main.py))

```python
"""tomd - Convert PDF and HTML files to Markdown.

PDF: hybrid dual extraction (MuPDF + spatial rules) with confidence scoring.
HTML: DOM traversal with generator-specific metadata extraction.

Usage (after `pip install -e tomd`):
    tomd input.pdf                  # -> input.md + input.prompts.md + input.summary.json
    tomd input.html                 # -> input.md
    tomd *.pdf *.html --outdir out/ # batch mode

Also runnable as `python -m tomd.main ...`.
"""

def main():
    """CLI entry point: parse arguments, resolve inputs, and convert files."""
    # calls: qa.run_qa_report, html.convert_html, pdf.convert_pdf_with_summary, llmrepair.paper_record

# fresh7 (70 papers): about 4,400 tokens per paper; 5M tokens covers about 1,100 papers
CORPUS_LLM_BUDGET = 5000000

# per paper (2026-10-24): about $1 of repair at the assumed list prices $15 / $75 per million input /
# output tokens (rate (b); not confirmed against billing), converted with the tuning sets' measured
# repair mix (3,328,038 in, 264,036 out = $69.72 for 3.59M tokens, $19.41 per million). Measured on
# the tuning sets it would have left none of the 30 fixed or 23 broken tables unrepaired.
CORPUS_LLM_PAPER_BUDGET = 51500
```

## Index

- `add_header_above`: [`lib/pdf/validate.py`](#lib-pdf-validate-py)
- `aligned_regions`: [`lib/pdf/flag.py`](#lib-pdf-flag-py)
- `ALLOWED_LINK_SCHEMES`: [`lib/__init__.py`](#lib-init-py)
- `annotate`: [`lib/pdf/continuation.py`](#lib-pdf-continuation-py)
- `apply`: [`lib/pdf/fullwidth.py`](#lib-pdf-fullwidth-py)
- `apply`: [`lib/pdf/stacked.py`](#lib-pdf-stacked-py)
- `area_features`: [`lib/pdf/scan.py`](#lib-pdf-scan-py)
- `area_word_features`: [`lib/pdf/docmeasure.py`](#lib-pdf-docmeasure-py)
- `AreaContext`: [`lib/pdf/checks/__init__.py`](#lib-pdf-checks-init-py)
- `areas`: [`lib/pdf/scan.py`](#lib-pdf-scan-py)
- `ascii_escape`: [`lib/__init__.py`](#lib-init-py)
- `ask`: [`lib/pdf/llmrepair.py`](#lib-pdf-llmrepair-py)
- `assign`: [`lib/pdf/levels.py`](#lib-pdf-levels-py)
- `attach_links`: [`lib/pdf/extract.py`](#lib-pdf-extract-py)
- `AUDIENCE_RE`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `available`: [`lib/pdf/worddict.py`](#lib-pdf-worddict-py)
- `BAD_TABLE_FLAGS`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `band`: [`lib/pdf/scan.py`](#lib-pdf-scan-py)
- `BANDS`: [`lib/pdf/paper_model.py`](#lib-pdf-paper-model-py)
- `Block`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `build`: [`lib/pdf/content.py`](#lib-pdf-content-py)
- `build`: [`lib/pdf/summary.py`](#lib-pdf-summary-py)
- `build_columns`: [`lib/pdf/llmrepair.py`](#lib-pdf-llmrepair-py)
- `build_text`: [`lib/pdf/content.py`](#lib-pdf-content-py)
- `BULLET_CHARS`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `BULLET_RE`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `candidate_from_section`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `candidates_agree`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `cell_markers`: [`lib/pdf/levels.py`](#lib-pdf-levels-py)
- `cell_text`: [`lib/pdf/validate.py`](#lib-pdf-validate-py)
- `Check`: [`lib/pdf/checks/__init__.py`](#lib-pdf-checks-init-py)
- `CHECK`: [`lib/pdf/checks/caption.py`](#lib-pdf-checks-caption-py)
- `CHECK`: [`lib/pdf/checks/coherence.py`](#lib-pdf-checks-coherence-py)
- `CHECK`: [`lib/pdf/checks/data_or_format.py`](#lib-pdf-checks-data-or-format-py)
- `CHECK`: [`lib/pdf/checks/drawn_lines.py`](#lib-pdf-checks-drawn-lines-py)
- `CHECK`: [`lib/pdf/checks/footprint.py`](#lib-pdf-checks-footprint-py)
- `CHECK`: [`lib/pdf/checks/nominations.py`](#lib-pdf-checks-nominations-py)
- `CHECK`: [`lib/pdf/checks/same_code.py`](#lib-pdf-checks-same-code-py)
- `CHECK`: [`lib/pdf/checks/text_alignment.py`](#lib-pdf-checks-text-alignment-py)
- `CHECK`: [`lib/pdf/checks/wordgap.py`](#lib-pdf-checks-wordgap-py)
- `check`: [`lib/pdf/llmcheck.py`](#lib-pdf-llmcheck-py)
- `check`: [`lib/pdf/relations.py`](#lib-pdf-relations-py)
- `CHECK_MODEL`: [`lib/pdf/llmcheck.py`](#lib-pdf-llmcheck-py)
- `check_page`: [`lib/pdf/visibility.py`](#lib-pdf-visibility-py)
- `check_table`: [`lib/pdf/ocrcheck.py`](#lib-pdf-ocrcheck-py)
- `class_check`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `classify`: [`lib/pdf/visibility.py`](#lib-pdf-visibility-py)
- `classify_monospace`: [`lib/pdf/mono.py`](#lib-pdf-mono-py)
- `classify_wording`: [`lib/pdf/wording.py`](#lib-pdf-wording-py)
- `cleanup_text`: [`lib/pdf/cleanup.py`](#lib-pdf-cleanup-py)
- `clear`: [`lib/pdf/pagecache.py`](#lib-pdf-pagecache-py)
- `closed_exempt`: [`lib/pdf/ruled.py`](#lib-pdf-ruled-py)
- `CLOSED_GRID_EXEMPT`: [`lib/pdf/ruled.py`](#lib-pdf-ruled-py)
- `code_guard`: [`lib/pdf/llmrepair.py`](#lib-pdf-llmrepair-py)
- `CodeStream`: [`lib/pdf/checks/codereader.py`](#lib-pdf-checks-codereader-py)
- `collect_line_drawings`: [`lib/pdf/wording.py`](#lib-pdf-wording-py)
- `collect_links`: [`lib/pdf/extract.py`](#lib-pdf-extract-py)
- `column_coherence`: [`lib/pdf/checks/coherence.py`](#lib-pdf-checks-coherence-py)
- `column_type`: [`lib/pdf/checks/plausible.py`](#lib-pdf-checks-plausible-py)
- `comment`: [`lib/pdf/levels.py`](#lib-pdf-levels-py)
- `COMMON_LAYOUTS`: [`lib/pdf/summary.py`](#lib-pdf-summary-py)
- `compare_extractions`: [`lib/pdf/structure.py`](#lib-pdf-structure-py)
- `COMPOUND_PREFIXES`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `compute_bbox`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `compute_metrics`: [`lib/pdf/qa.py`](#lib-pdf-qa-py)
- `confidence`: [`lib/pdf/summary.py`](#lib-pdf-summary-py)
- `Confidence`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `conservation_error`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `content_candidates`: [`lib/pdf/content.py`](#lib-pdf-content-py)
- `content_features`: [`lib/pdf/checks/coherence.py`](#lib-pdf-checks-coherence-py)
- `convert_html`: [`lib/html/__init__.py`](#lib-html-init-py)
- `convert_pdf`: [`lib/pdf/__init__.py`](#lib-pdf-init-py)
- `convert_pdf_with_summary`: [`lib/pdf/__init__.py`](#lib-pdf-init-py)
- `CORPUS_LLM_BUDGET`: [`main.py`](#main-py)
- `CORPUS_LLM_PAPER_BUDGET`: [`main.py`](#main-py)
- `cross_reader_continuation`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `current`: [`lib/pdf/evidence.py`](#lib-pdf-evidence-py)
- `CURRENT_GENERATOR`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `DATE_RE`: [`lib/__init__.py`](#lib-init-py)
- `detect_generator`: [`lib/html/extract.py`](#lib-html-extract-py)
- `detect_repeating`: [`lib/pdf/cleanup.py`](#lib-pdf-cleanup-py)
- `detect_spans`: [`lib/pdf/tablemodel.py`](#lib-pdf-tablemodel-py)
- `detect_tables`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `DIAGRAM_BOXES`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `diagram_boxes`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `DICT_PATH`: [`lib/pdf/worddict.py`](#lib-pdf-worddict-py)
- `DICT_SHA256`: [`lib/pdf/worddict.py`](#lib-pdf-worddict-py)
- `dimensions`: [`lib/pdf/dimensions.py`](#lib-pdf-dimensions-py)
- `disabled`: [`lib/pdf/checks/__init__.py`](#lib-pdf-checks-init-py)
- `discards`: [`lib/pdf/visibility.py`](#lib-pdf-visibility-py)
- `DOC_FIELD_RE`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `DOC_NUM_PATTERN`: [`lib/__init__.py`](#lib-init-py)
- `DOC_NUM_RE`: [`lib/__init__.py`](#lib-init-py)
- `DOC_PRIOR`: [`lib/pdf/scan.py`](#lib-pdf-scan-py)
- `DocMeasure`: [`lib/pdf/docmeasure.py`](#lib-pdf-docmeasure-py)
- `DRAWN`: [`lib/pdf/checks/_layout.py`](#lib-pdf-checks-layout-py)
- `drawn_spans`: [`lib/pdf/ruled.py`](#lib-pdf-ruled-py)
- `dropped_nomination_regions`: [`lib/pdf/__init__.py`](#lib-pdf-init-py)
- `dropped_uncovered`: [`lib/pdf/flag.py`](#lib-pdf-flag-py)
- `duplication`: [`lib/pdf/checks/plausible.py`](#lib-pdf-checks-plausible-py)
- `EARLY_NONE`: [`lib/pdf/scan.py`](#lib-pdf-scan-py)
- `EDGE_ITEMS_PER_PAGE`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `EMAIL_RE`: [`lib/__init__.py`](#lib-init-py)
- `emit_markdown`: [`lib/pdf/emit.py`](#lib-pdf-emit-py)
- `emit_prompts`: [`lib/pdf/emit.py`](#lib-pdf-emit-py)
- `enabled`: [`lib/pdf/llmcheck.py`](#lib-pdf-llmcheck-py)
- `Entry`: [`lib/pdf/evidence.py`](#lib-pdf-evidence-py)
- `escalate`: [`lib/pdf/validate.py`](#lib-pdf-validate-py)
- `extend`: [`lib/pdf/extent.py`](#lib-pdf-extent-py)
- `EXTENT_RULE`: [`lib/pdf/extent.py`](#lib-pdf-extent-py)
- `extract_metadata`: [`lib/html/extract.py`](#lib-html-extract-py)
- `extract_metadata_from_blocks`: [`lib/pdf/wg21.py`](#lib-pdf-wg21-py)
- `extract_mupdf`: [`lib/pdf/extract.py`](#lib-pdf-extract-py)
- `extract_poll_tables`: [`lib/pdf/poll.py`](#lib-pdf-poll-py)
- `extract_ruled_tables`: [`lib/pdf/ruled.py`](#lib-pdf-ruled-py)
- `extract_spatial`: [`lib/pdf/extract.py`](#lib-pdf-extract-py)
- `extract_tagged_tables`: [`lib/pdf/tagged.py`](#lib-pdf-tagged-py)
- `FALLBACK_BODY_SIZE`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `FALLBACK_FONT_SIZE`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `features`: [`lib/pdf/checks/data_or_format.py`](#lib-pdf-checks-data-or-format-py)
- `features`: [`lib/pdf/summary.py`](#lib-pdf-summary-py)
- `figure_label`: [`lib/pdf/figures.py`](#lib-pdf-figures-py)
- `find_code_pairs`: [`lib/pdf/codepair.py`](#lib-pdf-codepair-py)
- `find_hidden_regions`: [`lib/pdf/cleanup.py`](#lib-pdf-cleanup-py)
- `find_toc_indices`: [`lib/toc.py`](#lib-toc-py)
- `fit`: [`lib/pdf/fit.py`](#lib-pdf-fit-py)
- `fit_rows`: [`lib/pdf/fit.py`](#lib-pdf-fit-py)
- `flag_possible_tables`: [`lib/pdf/flag.py`](#lib-pdf-flag-py)
- `FLAGS`: [`lib/pdf/classify.py`](#lib-pdf-classify-py)
- `flatten`: [`lib/pdf/tablemodel.py`](#lib-pdf-tablemodel-py)
- `flatten_text`: [`lib/pdf/tablemodel.py`](#lib-pdf-tablemodel-py)
- `FORMAT_CHARS`: [`lib/__init__.py`](#lib-init-py)
- `format_front_matter`: [`lib/__init__.py`](#lib-init-py)
- `fragment_share`: [`lib/pdf/checks/coherence.py`](#lib-pdf-checks-coherence-py)
- `FRONT_MATTER_ORDER`: [`lib/__init__.py`](#lib-init-py)
- `full_mode`: [`lib/pdf/checks/__init__.py`](#lib-pdf-checks-init-py)
- `full_width_rows`: [`lib/pdf/fullwidth.py`](#lib-pdf-fullwidth-py)
- `gap_stats`: [`lib/pdf/docmeasure.py`](#lib-pdf-docmeasure-py)
- `gate_tables`: [`lib/pdf/classify.py`](#lib-pdf-classify-py)
- `generator`: [`lib/pdf/classify.py`](#lib-pdf-classify-py)
- `GENERATOR_TIER`: [`lib/pdf/checks/__init__.py`](#lib-pdf-checks-init-py)
- `GENERATORS`: [`lib/pdf/classify.py`](#lib-pdf-classify-py)
- `get_edge_items`: [`lib/pdf/cleanup.py`](#lib-pdf-cleanup-py)
- `grid_of`: [`lib/pdf/fit.py`](#lib-pdf-fit-py)
- `gutter_regions`: [`lib/pdf/flag.py`](#lib-pdf-flag-py)
- `gutters`: [`lib/pdf/content.py`](#lib-pdf-content-py)
- `has_caption`: [`lib/pdf/checks/caption.py`](#lib-pdf-checks-caption-py)
- `header_comment`: [`lib/pdf/summary.py`](#lib-pdf-summary-py)
- `header_contrast`: [`lib/pdf/checks/coherence.py`](#lib-pdf-checks-coherence-py)
- `heading_confidence`: [`lib/pdf/structure.py`](#lib-pdf-structure-py)
- `hidden_chars`: [`lib/pdf/pagecache.py`](#lib-pdf-pagecache-py)
- `HYPHEN_STATS`: [`lib/pdf/emit.py`](#lib-pdf-emit-py)
- `hyphenates`: [`lib/pdf/docmeasure.py`](#lib-pdf-docmeasure-py)
- `IMAGE_GRID_SHARE`: [`lib/pdf/classify.py`](#lib-pdf-classify-py)
- `image_share`: [`lib/pdf/classify.py`](#lib-pdf-classify-py)
- `INFO`: [`lib/pdf/checks/__init__.py`](#lib-pdf-checks-init-py)
- `info_of`: [`lib/pdf/scan.py`](#lib-pdf-scan-py)
- `is_green_ins`: [`lib/pdf/wording.py`](#lib-pdf-wording-py)
- `is_likely`: [`lib/pdf/emit.py`](#lib-pdf-emit-py)
- `is_readable`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `is_red_del`: [`lib/pdf/wording.py`](#lib-pdf-wording-py)
- `is_word`: [`lib/pdf/worddict.py`](#lib-pdf-worddict-py)
- `jev_enabled`: [`lib/pdf/classify.py`](#lib-pdf-classify-py)
- `JEV_SURE`: [`lib/pdf/scan.py`](#lib-pdf-scan-py)
- `jev_table_or_not`: [`lib/pdf/classify.py`](#lib-pdf-classify-py)
- `join_split_words`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `KNOWN_GENERATORS`: [`lib/pdf/summary.py`](#lib-pdf-summary-py)
- `KNOWN_SECTIONS`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `label_figure_tables`: [`lib/pdf/figures.py`](#lib-pdf-figures-py)
- `layout_features`: [`lib/pdf/checks/_layout.py`](#lib-pdf-checks-layout-py)
- `LAYOUT_TREE`: [`lib/pdf/classify_trees.py`](#lib-pdf-classify-trees-py)
- `LEVELS`: [`lib/pdf/checks/__init__.py`](#lib-pdf-checks-init-py)
- `likelihood`: [`lib/pdf/scan.py`](#lib-pdf-scan-py)
- `likelihood_data`: [`lib/pdf/checks/data_or_format.py`](#lib-pdf-checks-data-or-format-py)
- `Line`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `line_kind`: [`lib/pdf/records.py`](#lib-pdf-records-py)
- `LINE_SPACING_RATIO`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `llm_enabled`: [`lib/pdf/llmrepair.py`](#lib-pdf-llmrepair-py)
- `looks_like_cpp`: [`lib/pdf/checks/codereader.py`](#lib-pdf-checks-codereader-py)
- `main`: [`main.py`](#main-py)
- `mark_matrix`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `markdown`: [`lib/pdf/visibility.py`](#lib-pdf-visibility-py)
- `marker`: [`lib/pdf/tablemodel.py`](#lib-pdf-tablemodel-py)
- `MAX_FILL`: [`lib/pdf/rowbands.py`](#lib-pdf-rowbands-py)
- `measure`: [`lib/pdf/docmeasure.py`](#lib-pdf-docmeasure-py)
- `merge_rule_bands`: [`lib/pdf/rowbands.py`](#lib-pdf-rowbands-py)
- `merged_share`: [`lib/pdf/checks/coherence.py`](#lib-pdf-checks-coherence-py)
- `MIN_RULES`: [`lib/pdf/rowbands.py`](#lib-pdf-rowbands-py)
- `MIN_SEGMENT`: [`lib/pdf/rowbands.py`](#lib-pdf-rowbands-py)
- `MIN_UNCERTAIN_WORDS`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `mismatched_tokens`: [`lib/pdf/ocrcheck.py`](#lib-pdf-ocrcheck-py)
- `MODEL`: [`lib/pdf/dvf_model.py`](#lib-pdf-dvf-model-py)
- `MODEL`: [`lib/pdf/llmrepair.py`](#lib-pdf-llmrepair-py)
- `MODEL`: [`lib/pdf/paper_model.py`](#lib-pdf-paper-model-py)
- `MODEL`: [`lib/pdf/scan_model.py`](#lib-pdf-scan-model-py)
- `NAMES`: [`lib/pdf/levels.py`](#lib-pdf-levels-py)
- `NEAR`: [`lib/pdf/continuation.py`](#lib-pdf-continuation-py)
- `normalize_spans`: [`lib/pdf/spans.py`](#lib-pdf-spans-py)
- `normalize_whitespace`: [`lib/pdf/cleanup.py`](#lib-pdf-cleanup-py)
- `NUM_JOIN_REFUSED`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `NUMBERED_LIST_RE`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `ocr_enabled`: [`lib/pdf/ocrcheck.py`](#lib-pdf-ocrcheck-py)
- `outside_view_regions`: [`lib/pdf/flag.py`](#lib-pdf-flag-py)
- `page_furniture`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `page_hrules`: [`lib/pdf/content.py`](#lib-pdf-content-py)
- `PAGE_NUM_RE`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `page_text`: [`lib/pdf/content.py`](#lib-pdf-content-py)
- `page_words`: [`lib/pdf/content.py`](#lib-pdf-content-py)
- `PageEdgeItem`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `paper_record`: [`lib/pdf/llmrepair.py`](#lib-pdf-llmrepair-py)
- `PARA_SPACING_RATIO`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `parse_author_lines`: [`lib/__init__.py`](#lib-init-py)
- `parse_html`: [`lib/html/extract.py`](#lib-html-extract-py)
- `partial_reading`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `periodic_runs`: [`lib/pdf/records.py`](#lib-pdf-records-py)
- `pieces_of`: [`lib/pdf/content.py`](#lib-pdf-content-py)
- `PipelineResult`: [`lib/pdf/__init__.py`](#lib-pdf-init-py)
- `place_stray_words`: [`lib/pdf/repair.py`](#lib-pdf-repair-py)
- `plausibility`: [`lib/pdf/checks/plausible.py`](#lib-pdf-checks-plausible-py)
- `poll_counts`: [`lib/pdf/checks/plausible.py`](#lib-pdf-checks-plausible-py)
- `predict`: [`lib/pdf/classify.py`](#lib-pdf-classify-py)
- `PROMPT_VERSION`: [`lib/pdf/llmcheck.py`](#lib-pdf-llmcheck-py)
- `prompts_section`: [`lib/pdf/summary.py`](#lib-pdf-summary-py)
- `propagate_monospace`: [`lib/pdf/mono.py`](#lib-pdf-mono-py)
- `QAMetrics`: [`lib/pdf/qa.py`](#lib-pdf-qa-py)
- `rawdict`: [`lib/pdf/pagecache.py`](#lib-pdf-pagecache-py)
- `read_lines`: [`lib/pdf/checks/codereader.py`](#lib-pdf-checks-codereader-py)
- `read_region`: [`lib/pdf/records.py`](#lib-pdf-records-py)
- `reader_error`: [`lib/pdf/evidence.py`](#lib-pdf-evidence-py)
- `Record`: [`lib/pdf/evidence.py`](#lib-pdf-evidence-py)
- `record_for`: [`lib/pdf/relations.py`](#lib-pdf-relations-py)
- `records_candidates`: [`lib/pdf/records.py`](#lib-pdf-records-py)
- `region_features`: [`lib/pdf/classify.py`](#lib-pdf-classify-py)
- `regions_of`: [`lib/pdf/visibility.py`](#lib-pdf-visibility-py)
- `registry`: [`lib/pdf/checks/__init__.py`](#lib-pdf-checks-init-py)
- `rejected_regions`: [`lib/pdf/flag.py`](#lib-pdf-flag-py)
- `RelationRecord`: [`lib/pdf/relations.py`](#lib-pdf-relations-py)
- `remove_covered_text`: [`lib/pdf/pagecache.py`](#lib-pdf-pagecache-py)
- `remove_hidden_text`: [`lib/pdf/visibility.py`](#lib-pdf-visibility-py)
- `remove_table_regions`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `render_body`: [`lib/html/render.py`](#lib-html-render-py)
- `repair`: [`lib/pdf/llmrepair.py`](#lib-pdf-llmrepair-py)
- `REPEATING_THRESHOLD`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `REPLY_TO_CONTINUATION_CAP`: [`lib/pdf/wg21.py`](#lib-pdf-wg21-py)
- `REPLY_TO_RE`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `resegment_rows`: [`lib/pdf/validate.py`](#lib-pdf-validate-py)
- `reset`: [`lib/pdf/evidence.py`](#lib-pdf-evidence-py)
- `reset`: [`lib/pdf/llmcheck.py`](#lib-pdf-llmcheck-py)
- `reset_paper`: [`lib/pdf/llmrepair.py`](#lib-pdf-llmrepair-py)
- `run`: [`lib/pdf/checks/caption.py`](#lib-pdf-checks-caption-py)
- `run`: [`lib/pdf/checks/coherence.py`](#lib-pdf-checks-coherence-py)
- `run`: [`lib/pdf/checks/data_or_format.py`](#lib-pdf-checks-data-or-format-py)
- `run`: [`lib/pdf/checks/drawn_lines.py`](#lib-pdf-checks-drawn-lines-py)
- `run`: [`lib/pdf/checks/footprint.py`](#lib-pdf-checks-footprint-py)
- `run`: [`lib/pdf/checks/nominations.py`](#lib-pdf-checks-nominations-py)
- `run`: [`lib/pdf/checks/same_code.py`](#lib-pdf-checks-same-code-py)
- `run`: [`lib/pdf/checks/text_alignment.py`](#lib-pdf-checks-text-alignment-py)
- `run`: [`lib/pdf/checks/wordgap.py`](#lib-pdf-checks-wordgap-py)
- `run_qa_report`: [`lib/pdf/qa.py`](#lib-pdf-qa-py)
- `run_region_checks`: [`lib/pdf/checks/__init__.py`](#lib-pdf-checks-init-py)
- `run_scan`: [`lib/pdf/scan.py`](#lib-pdf-scan-py)
- `same_code`: [`lib/pdf/codepair.py`](#lib-pdf-codepair-py)
- `Section`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `SECTION_NUM_PATTERN`: [`lib/__init__.py`](#lib-init-py)
- `SECTION_NUM_PREFIX_RE`: [`lib/__init__.py`](#lib-init-py)
- `SECTION_NUM_RE`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `SectionKind`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `select_tables`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `SEP`: [`lib/pdf/tablemodel.py`](#lib-pdf-tablemodel-py)
- `sequence_order`: [`lib/pdf/checks/plausible.py`](#lib-pdf-checks-plausible-py)
- `set_hyphenating`: [`lib/pdf/emit.py`](#lib-pdf-emit-py)
- `shape`: [`lib/pdf/checks/coherence.py`](#lib-pdf-checks-coherence-py)
- `similar`: [`lib/similarity.py`](#lib-similarity-py)
- `SIMILARITY_THRESHOLD`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `SOURCE_INFO`: [`lib/pdf/checks/nominations.py`](#lib-pdf-checks-nominations-py)
- `SOURCES`: [`lib/pdf/classify.py`](#lib-pdf-classify-py)
- `Span`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `sparse_mapping`: [`lib/pdf/ruled.py`](#lib-pdf-ruled-py)
- `SPECIALISTS`: [`lib/pdf/content.py`](#lib-pdf-content-py)
- `split_at_headers`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `split_hidden_column`: [`lib/pdf/validate.py`](#lib-pdf-validate-py)
- `split_stacked`: [`lib/pdf/stacked.py`](#lib-pdf-stacked-py)
- `split_stacked_rows`: [`lib/pdf/validate.py`](#lib-pdf-validate-py)
- `state`: [`lib/pdf/llmcheck.py`](#lib-pdf-llmcheck-py)
- `stitch_pages`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `strip_boilerplate`: [`lib/html/extract.py`](#lib-html-extract-py)
- `strip_format_chars`: [`lib/__init__.py`](#lib-init-py)
- `strip_hidden_blocks`: [`lib/pdf/cleanup.py`](#lib-pdf-cleanup-py)
- `strip_repeating`: [`lib/pdf/cleanup.py`](#lib-pdf-cleanup-py)
- `structure_sections`: [`lib/pdf/structure.py`](#lib-pdf-structure-py)
- `summary`: [`lib/pdf/visibility.py`](#lib-pdf-visibility-py)
- `switch_reader`: [`lib/pdf/validate.py`](#lib-pdf-validate-py)
- `table_coherence`: [`lib/pdf/checks/coherence.py`](#lib-pdf-checks-coherence-py)
- `table_flags`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `TABLE_TREE`: [`lib/pdf/classify_trees.py`](#lib-pdf-classify-trees-py)
- `table_use`: [`lib/pdf/emit.py`](#lib-pdf-emit-py)
- `TableCandidate`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `take_excluded_grids`: [`lib/pdf/ruled.py`](#lib-pdf-ruled-py)
- `TERMINAL_PUNCTUATION`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `text_regions`: [`lib/pdf/flag.py`](#lib-pdf-flag-py)
- `text_rows`: [`lib/pdf/classify.py`](#lib-pdf-classify-py)
- `unfamiliarity`: [`lib/pdf/summary.py`](#lib-pdf-summary-py)
- `verify_layout`: [`lib/pdf/validate.py`](#lib-pdf-validate-py)
- `verify_pieces`: [`lib/pdf/validate.py`](#lib-pdf-validate-py)
- `Violation`: [`lib/pdf/relations.py`](#lib-pdf-relations-py)
- `visual_lines`: [`lib/pdf/content.py`](#lib-pdf-content-py)
- `visual_lines`: [`lib/pdf/docmeasure.py`](#lib-pdf-docmeasure-py)
- `vote_header`: [`lib/pdf/poll.py`](#lib-pdf-poll-py)
- `VOTE_LABELS`: [`lib/pdf/poll.py`](#lib-pdf-poll-py)
- `weak_note`: [`lib/pdf/dimensions.py`](#lib-pdf-dimensions-py)
- `WHY_TEXT`: [`lib/pdf/visibility.py`](#lib-pdf-visibility-py)
- `witness`: [`lib/pdf/table.py`](#lib-pdf-table-py)
- `WORD_GAP_RATIO`: [`lib/pdf/types.py`](#lib-pdf-types-py)
- `words`: [`lib/pdf/worddict.py`](#lib-pdf-worddict-py)
- `words_in`: [`lib/pdf/pagecache.py`](#lib-pdf-pagecache-py)
- `Y_TOLERANCE`: [`lib/pdf/types.py`](#lib-pdf-types-py)
