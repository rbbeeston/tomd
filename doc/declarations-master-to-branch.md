# Declarations, master to tables-reportlab

4 modules changed, 48 added, 0 removed; 14 unchanged.

## `lib/pdf/__init__.py` (changed)

```diff
@@ -13,7 +13,17 @@
     skipped: bool = False
     skip_reason: str = ''
+    discards: list = field(default_factory=list)
 
 # Convert a PDF file to Markdown.
 def convert_pdf(path: Path) -> tuple[str, str | None]: ...
 
-# + 5 private functions or classes
+# convert_pdf plus the paper-level summary (summary.py): tables trusted, flagged and marked,
+# confidence and unfamiliarity. Written as JSON beside the Markdown by the command line.
+def convert_pdf_with_summary(path: Path) -> tuple[str, str | None, dict | None]: ...
+
+# Every area a reader or scan nominated and a rule then excluded, where no kept table covers
+# it, as a possible-table region - a drop never leaves the text silent - except the rules
+# above. (page, bbox, reason, rows) like every mark region.
+def dropped_nomination_regions(record, tables) -> list: ...
+
+# + 14 private functions or classes
```

## `lib/pdf/checks/__init__.py` (added)

```diff
+# The scan's checks: one file each, loaded in a fixed order.
+
+@dataclass
+class AreaContext:
+    # What a region-level check may look at.
+    page: object
+    area: dict
+    generator: str
+    doc_tagged: bool
+    measure: object = None
+    cache: dict = field(default_factory=dict)
+
+@dataclass(frozen=True)
+class Check:
+    name: str
+    levels: tuple[str, ...]
+    info: str
+    cost: int
+    optional: bool
+    run: Callable[['AreaContext'], dict]
+    tier: int = 1
+
+def disabled() -> set[str]: ...
+
+# Every check on every area (training data, the ledger): TOMD_SCAN_FULL=1.
+def full_mode() -> bool: ...
+
+def registry() -> list[Check]: ...
+
+# Tier 1 first; the last-resort tier only while decided(features) is False (or in full mode).
+# Tiers per generator family where the family's ledger says so. Returns the features;
+# "_skipped" lists the checks not run.
+def run_region_checks(ctx: AreaContext, decided: Callable[[dict], bool] | None = None) -> dict: ...
+
+GENERATOR_TIER = ...
+INFO = ...
+LEVELS = ...
+
+# + 1 private function or class
```

## `lib/pdf/checks/_layout.py` (added)

```diff
+# Shared computation for the two layout checks (computed once per area).
+
+def layout_features(ctx) -> dict: ...
+
+DRAWN = ('hrules', 'vrules', 'row_fills', 'enclosing_fill')
```

## `lib/pdf/checks/caption.py` (added)

```diff
+# Document: a "Table N" caption just above or below the area.
+
+def has_caption(text_above: str, text_below: str) -> bool: ...
+
+def run(ctx) -> dict: ...
+
+CHECK = ...
```

## `lib/pdf/checks/codereader.py` (added)

```diff
+# A lightweight reader for C++-like code lines (user, 2026-10-21): not a parser.
+
+class CodeStream:
+    # the state of one column of code
+    def __init__(self): ...
+    def feed(self, line: str) -> dict: ...
+
+# C++ by its content (any font): a token pattern only code has - scope '::', member '->', a
+# template argument list, a call, braces or semicolons, C++ operators, or a leading C++
+# keyword. Abstains (False) on plain words, numbers and math.
+def looks_like_cpp(text: str) -> bool: ...
+
+# per-line facts for one stream of code lines
+def read_lines(lines: list[str]) -> list[dict]: ...
+
+# + 1 private function or class
```

## `lib/pdf/checks/coherence.py` (added)

```diff
+# Meaning: column coherence of the area's best reading - items per cell, fragments, header vs
+# body, the weakest column's shape uniformity, and the first column as a list of keys (local
+# shape tier; no Jev).
+
+# Per column: share of the dominant shape among filled body cells, or None (abstain).
+def column_coherence(rows, skip_header=True): ...
+
+def content_features(rows) -> dict: ...
+
+# Fragments: body cells that start as a continuation (lowercase first word after a cell above
+# that ended mid-phrase) or end mid-phrase.
+def fragment_share(rows): ...
+
+# Header vs body: share of columns whose header cell is a different kind from the column's
+# body (a category over instances).
+def header_contrast(rows): ...
+
+# Items per cell: the worst column's share of body cells holding several items of the column's
+# own single-item kind (identifiers, numbers, marks), or several sentences. High means rows
+# were merged.
+def merged_share(rows): ...
+
+def run(ctx) -> dict: ...
+
+def shape(cell: str) -> str: ...
+
+def table_coherence(rows): ...
+
+CHECK = ...
+
+# + 1 private function or class
```

## `lib/pdf/checks/data_or_format.py` (added)

```diff
+# Meaning: tabular data or formatting? In data a cell's meaning depends on its row and its
+# column (look a value up by row key and column header); in formatting the grid only places
+# content (front matter, label: value entries, callouts, slide layouts). Features follow the
+# web-table literature (cell length and type consistency down columns, rows x columns, single
+# record, label: value pattern, large prose cells, borders), measured on the existing keys
+# before use (train_dvf.py: cross-validated AUC 0.99).
+
+def features(rows, f) -> dict | None: ...
+
+# P(tabular data) for a reading, or None without one.
+def likelihood_data(rows, f) -> float | None: ...
+
+def run(ctx) -> dict: ...
+
+CHECK = ...
```

## `lib/pdf/checks/drawn_lines.py` (added)

```diff
+# Drawing: rules, vertical lines, row shading and enclosing boxes in the area.
+
+def run(ctx) -> dict: ...
+
+CHECK = Check('drawn_lines', ('region',), 'paths', 1, False, run)
```

## `lib/pdf/checks/footprint.py` (added)

```diff
+# Words: the area's text footprint against the prose measure: left and right inset (cell
+# padding), and how many lines end on the right measure (justified prose does; cell text ends
+# raggedly).
+
+def run(ctx) -> dict: ...
+
+CHECK = ...
```

## `lib/pdf/checks/nominations.py` (added)

```diff
+# Which scans nominated the area and which rules excluded it (the evidence record), with the
+# number of independent information types among them.
+
+def run(ctx) -> dict: ...
+
+CHECK = Check('nominations', ('region',), 'record', 0, False, run)
+SOURCE_INFO = ...
```

## `lib/pdf/checks/plausible.py` (added)

```diff
+# Content plausibility: does the reading make sense as data? A meaning-based witness,
+# independent of geometry: it reads only the cells' text.
+
+def column_type(rows) -> list: ...
+
+def duplication(rows) -> list: ...
+
+# Every violation of the content checks for a reading (rows of cell strings).
+def plausibility(rows) -> list: ...
+
+def poll_counts(rows) -> list: ...
+
+def sequence_order(rows) -> list: ...
+
+# + 1 private function or class
```

## `lib/pdf/checks/same_code.py` (added)

```diff
+# Meaning: the largest code-pair similarity recorded in the area (weighted by size where it
+# was computed; one-line blocks abstain upstream).
+
+def run(ctx) -> dict: ...
+
+CHECK = ...
```

## `lib/pdf/checks/text_alignment.py` (added)

```diff
+# Alignment and shape of the text: rows, pieces per row, aligned starts, monospace and digit
+# shares, size and position (the classifier's features).
+
+def run(ctx) -> dict: ...
+
+CHECK = Check('text_alignment', ('region',), 'words', 1, False, run)
```

## `lib/pdf/checks/wordgap.py` (added)

```diff
+# Words: gaps between neighbouring words in units of the document's normal space. Prose has
+# uniform gaps (one space, or uniformly stretched when justified); table lines have bimodal
+# gaps that recur at the same x.
+
+def run(ctx) -> dict: ...
+
+CHECK = ...
```

## `lib/pdf/classify.py` (added)

```diff
+# Stage-2 gate: is a selected table really a table, and how is it built?
+
+# Classify every selected table and adjust its confidence (see module doc).
+def gate_tables(doc, pages, sections: list[Section], paper: str = '') -> dict: ...
+
+def generator(meta: dict) -> str: ...
+
+# The share of bbox covered by images drawn on the page (union approximated by the sum, capped
+# at 1; overlapping images are rare inside a table).
+def image_share(page, bbox) -> float: ...
+
+def jev_enabled() -> bool: ...
+
+# [(label, probability)] for every table area, and the Jev version(s).
+def jev_table_or_not(paper: str, regions: list) -> tuple[list, str]: ...
+
+# (label, confidence) from a tree exported by cart.Tree.export().
+def predict(tree: dict, x: dict): ...
+
+# (features, text lines) of one table area. Shared with the PoC's training.
+def region_features(page, bbox, sources, flags, gen: str, doc_tagged: bool): ...
+
+# Text rows in rect: [(top, bottom, [(x0, x1, text, mono)])], pieces split at wide gaps.
+def text_rows(page, rect): ...
+
+FLAGS = ...
+GENERATORS = ...
+IMAGE_GRID_SHARE = 0.5
+SOURCES = ['tags', 'poll', 'grid', 'rules', 'tomd', 'text']
+
+# + 4 private functions or classes
```

## `lib/pdf/classify_trees.py` (added)

```diff
+# Decision trees for the table gate (lib/pdf/classify.py).
+
+LAYOUT_TREE = ...
+TABLE_TREE = ...
```

## `lib/pdf/codepair.py` (added)

```diff
+# Side-by-side code comparisons, found from geometry and confirmed by content.
+
+# Code-comparison candidates on every page. rules_for(page) gives the page's drawn horizontal
+# rules (y, x0, x1): a rule between two lines separates them (rows of a ruled comparison are
+# not one block).
+def find_code_pairs(blocks: list[Block], rules_for=None) -> list[TableCandidate]: ...
+
+# Share of the smaller block's trigrams that the other block has too.
+def same_code(left: list[Line], right: list[Line]) -> float: ...
+
+# + 10 private functions or classes
```

## `lib/pdf/content.py` (added)

```diff
+# One content-first row/column builder for every table class.
+
+# -> (rows of cell strings, trace).
+def build(words, hrules=(), specialists=None): ...
+
+# Rows of cell strings (for measurement).
+def build_text(words, hrules=(), specialists=None): ...
+
+# For every located region (page, bbox) - from any reader, kept or not - the content-first
+# grid of the words inside it.
+def content_candidates(pages, regions, specialists=None, rules_by_page=None) -> list[TableCandidate]: ...
+
+# x intervals crossed by at most _SPAN_LINES lines' pieces.
+def gutters(lines_pieces, x_lo, x_hi): ...
+
+# Drawn horizontal separators on the page: (y, x0, x1).
+def page_hrules(page, drawings=None) -> list[tuple[float, float, float]]: ...
+
+# Horizontal words (x0, y0, x1, y1, text, monospace), and rotated lines (x0, y0, x1, y1, text)
+# - labels set at 90 degrees, as table headers often are. Rotated text is kept out of line,
+# row and column building.
+def page_text(page) -> tuple[list[tuple], list[tuple]]: ...
+
+# (x0, y0, x1, y1, text, monospace) for every horizontal word on the page.
+def page_words(page) -> list[tuple]: ...
+
+def pieces_of(line): ...
+
+# words: (x0, y0, x1, y1, text) -> lines of words sorted left to right.
+def visual_lines(words): ...
+
+SPECIALISTS = {'code_rows': True, 'separators': True}
+
+# + 4 private functions or classes
```

## `lib/pdf/continuation.py` (added)

```diff
+# A note on table pieces that may continue the previous page's table (2026-10-24).
+
+# Set metadata["continues_from"] = {"page": N, "reasons": [...]} (N 1-based, the previous
+# page) on table pieces that may continue the previous page's table. Returns the count.
+def annotate(doc, tables) -> int: ...
+
+NEAR = 0.06
+
+# + 5 private functions or classes
```

## `lib/pdf/dimensions.py` (added)

```diff
+# Stage 2 (relationship plan): confidence per dimension.
+
+# {dimension: {"level": strong|ok|weak, "why": [...]}} from a table's metadata.
+def dimensions(meta: dict) -> dict: ...
+
+# One line for the prompts: the weak dimensions and why, or "".
+def weak_note(dims: dict) -> str: ...
```

## `lib/pdf/docmeasure.py` (added)

```diff
+# Level 0: what ordinary prose looks like in this document.
+
+@dataclass
+class DocMeasure:
+    left: float = 0.0
+    right: float = 0.0
+    justified: float = 0.0
+    space: dict = field(default_factory=dict)
+    known: bool = False
+    def word_space(self, height: float) -> float: ...
+
+# Word-gap and footprint features of the words in one area.
+def area_word_features(words, m: DocMeasure) -> dict: ...
+
+# One visual line's word gaps in units of the document's normal space.
+def gap_stats(line, m: DocMeasure) -> dict | None: ...
+
+# Does the document break words with a hyphen at line ends? Evidence: a line ending in "word-"
+# whose join with the next line's first word appears elsewhere in the document unhyphenated
+# ("compari-" + "son", "comparison" seen elsewhere). Two or more such breaks: it hyphenates.
+# None: a line-end hyphen is the word's own ("Use-" + "cases"). One: undecided, treated as
+# hyphenating (the earlier behaviour). Measured on the keys: 4 to 223 such breaks in
+# hyphenating papers (LaTeX, and Word with hyphenation on), 0 in papers that never hyphenate.
+# The maker alone does not tell (Word can do either).
+def hyphenates(page_words: list[list]) -> bool: ...
+
+# page_words: per page, fitz "words" tuples (x0, y0, x1, y1, text, block, line, n).
+def measure(page_words: list[list]) -> DocMeasure: ...
+
+# Words (x0, y0, x1, y1, text, ...) sharing a baseline, left to right.
+def visual_lines(words): ...
```

## `lib/pdf/dvf_model.py` (added)

```diff
+# Data-vs-formatting model, fitted by train_dvf.py on the existing keys.
+
+MODEL = ...
```

## `lib/pdf/emit.py` (changed)

```diff
@@ -7,3 +7,17 @@
 def emit_prompts(sections: list[Section]) -> str | None: ...
 
-# + 14 private functions or classes
+# A flagged table whose words fit its drawn cells evenly (fit.py): 'likely correct', between
+# trusted (HIGH) and flagged. Never HIGH until a fresh sample proves the fit about 99% precise
+# out of sample.
+def is_likely(sec: Section) -> bool: ...
+
+def set_hyphenating(value: bool) -> None: ...
+
+# What a grid is used for, by the user's decisions (2026-10-19): "label-value" - repeated per-
+# item "label: value" entries (not a table); "contents" - a contents page or reference list
+# laid out in a grid (not a table); "table" - everything else.
+def table_use(rows) -> str: ...
+
+HYPHEN_STATS: Counter = Counter()
+
+# + 30 private functions or classes
```

## `lib/pdf/evidence.py` (added)

```diff
+# The evidence record: what every scan saw, nominated and rejected, and why.
+
+@dataclass
+class Entry:
+    kind: str
+    scan: str
+    page: int
+    bbox: Box
+    rule: str
+    info: str
+    value: object = None
+    observed: bool = True
+
+@dataclass
+class Record:
+    entries: list[Entry] = field(default_factory=list)
+    readings: list[tuple] = field(default_factory=list)
+    doc_measure: object = None
+    errors: list[dict] = field(default_factory=list)
+    def exclude(self, scan: str, page: int, bbox: Box, rule: str, info: str, value=None) -> None: ...
+    def feature(self, scan: str, page: int, bbox: Box, name: str, info: str, value, observed=True) -> None: ...
+    def nominate(self, scan: str, page: int, bbox: Box, cue: str, info: str, value=None) -> None: ...
+    def on_page(self, page: int, kind: str | None = None) -> list[Entry]: ...
+
+def current() -> Record: ...
+
+# Record a reader, check or specialist that raised (stage, page or None for the whole paper,
+# exception type and message). Tables the failure touched drop to UNCERTAIN ("reader error");
+# the prompts note and the paper summary list it. TOMD_STRICT=1 re-raises instead (tests).
+def reader_error(stage: str, page, exc: BaseException, table=None) -> None: ...
+
+def reset() -> Record: ...
```

## `lib/pdf/extent.py` (added)

```diff
+# The extent step: where each reader's table stops, and the rows just outside it.
+
+def extend(cands: list[TableCandidate], pages: dict) -> None: ...
+
+EXTENT_RULE = ...
+
+# + 19 private functions or classes
```

## `lib/pdf/figures.py` (added)

```diff
+# Tables inside figures: label them with the figure they belong to.
+
+# blocks: (bbox, text) of the page's text blocks; bbox: the table's box.
+def figure_label(blocks, bbox, text_width: float) -> str | None: ...
+
+# Set metadata["figure_label"] on single-page tables drawn inside a figure.
+def label_figure_tables(doc, table_sections) -> int: ...
+
+# + 1 private function or class
```

## `lib/pdf/fit.py` (added)

```diff
+# The fit witness: does the word layout fit the drawn cells evenly?
+
+# Does the reading `columns` (rows of cells of spans) fit the drawn grid?
+def fit(page, bbox, words, columns) -> dict: ...
+
+# The partial fit for ruled-row tables (horizontal rules, no vertical ones): row bands come
+# from the drawn rules, columns from the reading's own gutters. Every word lies inside one
+# band and one column with a clear gutter on both sides, the bands holding words match the
+# reading's rows one to one, no band holds stacked entries, and each cell's characters equal
+# the text layer's in its band and column. Measured apart from the grid fit; it never counts
+# as a witness unless it separates as well.
+def fit_rows(page, bbox, words, columns) -> dict: ...
+
+# (xs, ys, has_v, has_h) of the drawn grid, or None: at least 3 column lines and 3 row lines
+# that span the region.
+def grid_of(page, bbox): ...
+
+# + 6 private functions or classes
```

## `lib/pdf/flag.py` (added)

```diff
+# Mark text that is probably a table but was not extracted as one.
+
+# Tables without rules found by their columns, as the vision readers find them: text in three
+# or more columns whose starts line up down consecutive rows (left-aligned cells), with no
+# line running across a column start. A header row just above (centred labels) joins the
+# region. Code listings, contents pages and front matter are left out; what remains is read by
+# the content reader and checked like any other reading.
+def aligned_regions(blocks: list[Block]) -> list[Region]: ...
+
+# Every dropped candidate (any source, any reason) that no kept table covers, for the prompts
+# file: nothing a reader found is erased, but only misread-looking ones are marked in the
+# Markdown (rejected_regions).
+def dropped_uncovered(rejected: list[TableCandidate], tables: list[Section]) -> list[str]: ...
+
+# Mark sections inside a region; returns how many. Locality: a section is cut at page breaks,
+# so its lines on other pages never inherit a mark (variant 5b).
+def flag_possible_tables(sections: list[Section], regions: list[Region]) -> int: ...
+
+# Tables found by their negative space: a vertical whitespace gutter.
+def gutter_regions(blocks: list[Block]) -> list[Region]: ...
+
+# Tables seen from the outside, against the paper's own prose: a block that is set apart (its
+# rows fill much less than the prose measure) AND two-dimensional (most rows hold 2+ pieces
+# whose positions recur on other rows). A block that is set apart but one-dimensional is a
+# quote or a list; prose fills the measure. Measured on the tuning sets before use.
+def outside_view_regions(sections: list[Section]) -> list[Region]: ...
+
+# Areas of rejected drawing/tag tables that no selected table covers.
+def rejected_regions(rejected: list[TableCandidate], tables: list[Section]) -> list[Region]: ...
+
+# Table-like areas in the remaining text.
+def text_regions(blocks: list[Block]) -> list[Region]: ...
+
+# + 11 private functions or classes
```

## `lib/pdf/fullwidth.py` (added)

```diff
+# Full-width rows in drawn tables: titles and spanning rows read as spans.
+
+# Move each full-width row's text to its first cell; record the spans.
+def apply(sec, page, bbox) -> list[int]: ...
+
+def full_width_rows(columns, page, bbox) -> list[int]: ...
+
+# + 2 private functions or classes
```

## `lib/pdf/levels.py` (added)

```diff
+# Graded table levels (L0-L5) and cell markers, from tomd's own evidence.
+
+# {"level", "name", "why", "incomplete", "cells"} for a table section
+def assign(sec) -> dict: ...
+
+# cells where an alternative reading of the same shape disagrees with the table
+def cell_markers(sec) -> list[tuple[int, int]]: ...
+
+def comment(info: dict) -> str: ...
+
+NAMES = ...
+
+# + 1 private function or class
```

## `lib/pdf/llmcheck.py` (added)

```diff
+# Opt-in LLM second look at questionable tables: a narrow check, asked twice.
+
+# {"match", "wrong_rows", "consistent"} from two identical answers, or None (the answers
+# differed, an error, or the budget is spent)
+def check(client, page, bbox, rows, pdf_hash: str) -> dict | None: ...
+
+def enabled() -> bool: ...
+
+def reset() -> None: ...
+
+def state() -> dict: ...
+
+CHECK_MODEL = 'claude-sonnet-5-5'
+PROMPT_VERSION = 'check-v1'
+
+# + 3 private functions or classes
```

## `lib/pdf/llmrepair.py` (added)

```diff
+# Opt-in LLM repair of flagged tables: structure only, never content.
+
+# (rows of index lists, model id, seconds, usage) or None.
+def ask(client, page, bbox, words): ...
+
+# Cells of spans from word indices, or (None, reason) if the answer is unusable: an index out
+# of range, used twice, or a word left out.
+def build_columns(rows, words): ...
+
+# A repair may not add a column of bare line numbers to code (2026-10-24). Returns the failed
+# check or "". Measured on fresh10's cached answers: it turns the two breaks LLM repair caused
+# in side-by-side code (p2318r1, one row per code line plus a line-number column) into no
+# change. A wider rule, rejecting any repair that cuts a multi-line code cell into rows, also
+# undid two of the seven fixes (p2329r0-t2, p1985r3-t2), whose first readings had packed
+# several rows into one code cell; it is not used.
+def code_guard(first, repaired) -> str: ...
+
+def llm_enabled() -> bool: ...
+
+# What LLM repair did for this paper, for the paper summary: whether it was asked for and
+# available, the model(s), calls, results, tokens, seconds, and the run's budget. With no
+# credentials, no network or no budget left the run goes on without repair, and the status
+# says so.
+def paper_record() -> dict: ...
+
+# Try to repair one flagged table in place. Returns what happened.
+def repair(sec, page, bbox, words, verify, client=None) -> str: ...
+
+def reset_paper() -> None: ...
+
+MODEL = 'claude-opus-5-5'
+
+# + 7 private functions or classes
```

## `lib/pdf/ocrcheck.py` (added)

```diff
+# Check a HIGH table's text layer against the picture of the page.
+
+# "" if the header (and a poll's votes) read the same in the picture, else a note.
+def check_table(page, sec) -> str: ...
+
+# Text-layer tokens the OCR does not show.
+def mismatched_tokens(text_tokens: list[str], ocr_text: str) -> list[str]: ...
+
+def ocr_enabled() -> bool: ...
+
+# + 2 private functions or classes
```

## `lib/pdf/pagecache.py` (added)

```diff
+# One rawdict extraction per page, shared by the readers that need characters (the rule-band
+# reader and the poll reader each extracted it on their own). The cache lives on the document
+# object, so it goes away with it (keying a global cache by id() returned another document's
+# text once ids were reused).
+
+# Kept for callers; the cache is per document and needs no clearing.
+def clear() -> None: ...
+
+# bboxes of characters an opaque box drawn after them covers (slide decks hide the rows of a
+# build under a white box): text the page does not show
+def hidden_chars(page, drawings=None) -> list: ...
+
+def rawdict(page): ...
+
+# redact (in memory) the characters hidden_chars finds; pages changed
+def remove_covered_text(pages) -> int: ...
+
+# The page's words whose centre lies in bbox. Words are taken whole from the whole page: a
+# clipped extraction drops glyphs whose ink falls outside the clip (a period on the baseline
+# below a region's edge) and splits the word there.
+def words_in(page, bbox): ...
+
+# + 2 private functions or classes
```

## `lib/pdf/paper_model.py` (added)

```diff
+# Paper-level confidence model (P(no silent table error)), fitted by paper_calibration.py on
+# the existing keys (2026-10-23, after the determinism and locality commits: corrected page-
+# restricted labels, tuning sets only; calibrated base rate, weak discrimination, cross-
+# validated AUC 0.59).
+
+BANDS = ...
+MODEL = ...
```

## `lib/pdf/poll.py` (added)

```diff
+# WG21 poll result tables.
+
+# Poll result tables on one page. `words_hint` (the page's words, already extracted) lets a
+# page with no vote label skip the character extraction.
+def extract_poll_tables(page, page_num: int, words_hint=None) -> list[TableCandidate]: ...
+
+# These cell texts form a poll header (see VOTE_LABELS).
+def vote_header(labels: list[str]) -> bool: ...
+
+VOTE_LABELS = ...
+
+# + 7 private functions or classes
```

## `lib/pdf/records.py` (added)

```diff
+# Content record-pattern reader: a table seen as runs of records that share a schema of kinds,
+# with no geometry.
+
+# One kind for a line: its tokens' kind when they all share one, else 'mixed'.
+def line_kind(text: str) -> str: ...
+
+# (start, period, records) for runs whose kinds repeat with a period, longest first.
+def periodic_runs(kinds: list[str]) -> list[tuple[int, int, int]]: ...
+
+# Every run of records in the region (longest first, not overlapping), each with its header
+# and its own box; none unless together they cover most of the region's lines (a region
+# holding two stacked tables reads as two).
+def read_region(page, page_num: int, bbox) -> list[TableCandidate]: ...
+
+# The record-pattern reading of every located region (page, bbox).
+def records_candidates(pages, regions) -> list[TableCandidate]: ...
+
+# + 3 private functions or classes
```

## `lib/pdf/relations.py` (added)

```diff
+# Stage 1: the relationship record and the relational checker.
+
+@dataclass
+class RelationRecord:
+    observed: list = field(default_factory=list)
+    asserted: list = field(default_factory=list)
+    violations: list = field(default_factory=list)
+    def by_dimension(self) -> dict: ...
+
+@dataclass
+class Violation:
+    dimension: str
+    kind: str
+    where: tuple
+    evidence: str
+
+# rows_boxes: {(row, col): bbox of the cell's text}; words: fitz word tuples in the table's
+# region; hrules: (y, x0, x1) of drawn horizontal rules - only those crossing most of the
+# table are row boundaries (an underline, a strike-through or one cell's own rule is not).
+def check(rows_boxes: dict, words: list, hrules=(), reader: str = '?', mono=frozenset()) -> RelationRecord: ...
+
+# The relationship record of an emitted table section (cells from its spans).
+def record_for(sec, words, hrules=()) -> RelationRecord: ...
+
+# + 2 private functions or classes
```

## `lib/pdf/repair.py` (added)

```diff
+# Stage 3 (relationship plan): blind smallest-set repair and inferred cells.
+
+# (new columns, inferred [(row, col)], stray words) or None when the stray words are not
+# explained by the table's own rows and columns.
+def place_stray_words(columns: list, words: list, nl: Span): ...
+
+# + 5 private functions or classes
```

## `lib/pdf/rowbands.py` (added)

```diff
+# Rows bounded by drawn rules (2026-10-24).
+
+# Join empty-key continuation rows into the record above within one rule band; returns the
+# number of rows joined. rules: the page's horizontal rule segments (y, x0, x1).
+def merge_rule_bands(sec, rules) -> int: ...
+
+MAX_FILL = 0.67
+MIN_RULES = 4
+MIN_SEGMENT = 15.0
+
+# + 2 private functions or classes
```

## `lib/pdf/ruled.py` (added)

```diff
+# Table detection from ruling lines (vector drawings).
+
+# a closed grid's own layout explains its empty cells, unless a whole column is empty (a
+# doubled rule read as a column of its own)
+def closed_exempt(t) -> bool: ...
+
+# the spans a closed grid's own lines allow: a span inferred from the text's position is
+# dropped when a drawn line separates the cells it would join (the grid draws every cell it
+# has; an empty drawn cell is not part of its neighbour)
+def drawn_spans(page, columns, spans) -> list[dict]: ...
+
+# All tables on one page that ruling lines reveal.
+def extract_ruled_tables(page, page_num: int, drawings=None) -> list[TableCandidate]: ...
+
+# a closed grid of two or more drawn columns whose rows mostly fill only their first cell with
+# a short label (a mapping where most entries have no counterpart): a table, not a framed
+# paragraph under a lead-in line (whose single cells are prose)
+def sparse_mapping(t) -> bool: ...
+
+# Grids the reader excluded since the last call (for the drop marks).
+def take_excluded_grids() -> list[TableCandidate]: ...
+
+CLOSED_GRID_EXEMPT = ...
+
+# + 37 private functions or classes
```

## `lib/pdf/scan.py` (added)

```diff
+# The region scan: check every piece that makes a table, then decide.
+
+# Every enabled region-level check's evidence for one area (checks/); the last-resort tier
+# only while decided(features) is False.
+def area_features(page, a, generator: str, doc_tagged: bool, measure=None, decided=None) -> dict: ...
+
+# Nominated and excluded places, merged per page (half the smaller one overlapping).
+def areas(record) -> list[dict]: ...
+
+def band(p: float, info_types: int) -> str: ...
+
+def info_of(name: str) -> str: ...
+
+# P(table) and the features that pushed it most (signed contributions).
+def likelihood(x: dict, model: dict) -> tuple[float, list[tuple[str, float]]]: ...
+
+# Score every area in the evidence record and decide by band.
+def run_scan(path, record, tables, builds: list | None = None) -> list: ...
+
+DOC_PRIOR = 'document prior'
+EARLY_NONE = 0.02
+JEV_SURE = 0.9
+
+# + 6 private functions or classes
```

## `lib/pdf/scan_model.py` (added)

```diff
+# Region scan model, fitted by train_scan.py on the existing truth sets.
+
+MODEL = ...
```

## `lib/pdf/stacked.py` (added)

```diff
+# Stacked entries are one row each (table convention, "Rows: one row per entry").
+
+def apply(cands: list[TableCandidate]) -> list[TableCandidate]: ...
+
+def split_stacked(cand: TableCandidate) -> TableCandidate: ...
+
+# + 4 private functions or classes
```

## `lib/pdf/summary.py` (added)

```diff
+# Paper-level summary: what tomd did with this paper's tables, how sure it is, and how unlike
+# the measured papers this one is.
+
+def build(result, sections, evidence, generator: str) -> dict: ...
+
+# The measured chance that this paper's tables hold no silent error: the rate on the answer
+# keys for papers with a similar score, with its interval. An unfamiliar paper never gets the
+# familiar papers' figure: it is capped by unfamiliarity, and the interval widens to match.
+def confidence(s: dict) -> dict | None: ...
+
+# The paper-level model's inputs.
+def features(s: dict) -> dict: ...
+
+def header_comment(s: dict) -> str: ...
+
+def prompts_section(s: dict) -> str: ...
+
+# 0 (like the measured papers) .. 1 (unlike them), with the reasons.
+def unfamiliarity(generator: str, layouts: list[str], undecided: int, areas: int, rotated: bool, measured: bool, skipped: bool) -> tuple[float, list[str]]: ...
+
+COMMON_LAYOUTS = {'poll', 'grid', 'rule-per-row', 'tagged', 'booktabs'}
+KNOWN_GENERATORS = ...
```

## `lib/pdf/table.py` (changed)

```diff
@@ -1,9 +1,87 @@
-# Table detection from MuPDF block/line structure.
+# Table detection: the text-position detector, and selection across sources.
+
+# Wrap a detect_tables() section (cells are span lists) as a candidate.
+def candidate_from_section(sec: Section) -> TableCandidate: ...
+
+# Same grid shape and every cell matching.
+def candidates_agree(a: TableCandidate, b: TableCandidate) -> bool: ...
+
+# Why this table can be trusted from one source, or "".
+def class_check(cand: TableCandidate) -> str: ...
+
+# Check that the text in the table's area went into its cells exactly once.
+def conservation_error(cand: TableCandidate, blocks: list[Block]) -> str: ...
+
+# A table continuing across a page is the same table whichever reader read each piece (user:
+# preserve meaningful spatial relationships regardless of mechanism). After every reader's own
+# stitching, a piece ending low on page N joins a piece from a different reader starting high
+# on page N+1 under the same conditions as same-reader stitching: the same column count and
+# column starts (or extent), no different header, nothing between them (page furniture aside).
+# Polls are never joined this way. The joined table keeps the first piece's reader, is flagged
+# 'cross-reader' and records both.
+def cross_reader_continuation(cands: list[TableCandidate], blocks: list[Block], furniture: frozenset = frozenset()) -> list[TableCandidate]: ...
 
 # Detect table regions from MuPDF block structure.
 def detect_tables(blocks: list[Block]) -> tuple[list[Section], list[Block]]: ...
 
-# Remove blocks whose vertical midpoint falls within a detected table region.
-def exclude_table_regions(blocks: list[Block], table_sections: list[Section]) -> list[Block]: ...
+# Areas of a page drawn as a diagram: a graph or flowchart draws edges as diagonal lines and
+# arrowheads; a table uses horizontal and vertical rules only (tables inside figures too).
+# Returned as the drawn shapes' bounding boxes, merged per drawing cluster.
+def diagram_boxes(page, page_num: int) -> list: ...
 
-# + 4 private functions or classes
+# A word split by a narrow cell is still one word (user, 2026-10-21): a cell line that runs to
+# the cell's right edge ending mid-token, followed by a line that continues the token, is
+# joined without a space - when the joined token occurs elsewhere in the document and one of
+# the pieces never occurs on its own there, or when the break splits one identifier
+# (underscores in both pieces, the second piece not a name used on its own elsewhere) or one
+# long number or paper name (a run of 5+ characters ending in a digit, broken before a
+# remainder of at most two digits: "P0876R1" / "1", "20210" / "6") and a piece never occurs on
+# its own. A name followed by a number ("SC 22") and a year followed by a version ("2022" /
+# "17.14") are never joined. The next line is marked (joins_prev); cell text and spans honour
+# the mark.
+def join_split_words(cands: list[TableCandidate], blocks: list[Block]) -> None: ...
+
+# A check-mark matrix (status, feature or compliance tables): row keys in the first column,
+# and the filled cells beside them are marks. Sparse by design, so empty cells and sparse or
+# ragged columns are not misreadings.
+def mark_matrix(cand: TableCandidate) -> bool: ...
+
+# Lines repeated at the same height on several pages once digits are normalised: running
+# headers and footers with page numbers that header stripping missed (a header block holding
+# the page number).
+def page_furniture(blocks: list[Block], min_pages: int = 3) -> frozenset: ...
+
+# True when `other` is tomd's text-position reading of part of a fully ruled table: same
+# columns, and every one of its rows matches, cell for cell, a row of the ruled table in the
+# same order. The text-position detector often stops early or starts late on ruled tables; a
+# correct subset confirms the rows it saw rather than contradicting the rest.
+def partial_reading(primary: TableCandidate, other: TableCandidate) -> bool: ...
+
+# Drop the lines that fall inside any chosen table's region.
+def remove_table_regions(blocks: list[Block], tables: list[Section]) -> list[Block]: ...
+
+# Choose one table per region from the three extractors.
+def select_tables(tomd_sections: list[Section], ruled: list[TableCandidate], tagged: list[TableCandidate], blocks: list[Block], polls: list[TableCandidate] = (), rejected: list[TableCandidate] | None = None, codepairs: list[TableCandidate] = (), content: list[TableCandidate] = (), generator: str = 'unknown') -> list[Section]: ...
+
+# Two tables stacked in one reading: a different header row inside the body (short bold labels
+# after a non-bold row) starts a new table (the user's header rule; an identical header
+# repeated is the same table and stays). Single-page readings only; tags and polls delimit
+# their own tables.
+def split_at_headers(cand: TableCandidate) -> list[TableCandidate]: ...
+
+# Join a table that ends one page with one that starts the next page.
+def stitch_pages(cands: list[TableCandidate], blocks: list[Block], furniture: frozenset = frozenset()) -> list[TableCandidate]: ...
+
+# Rule-based sanity checks. Flags in BAD_TABLE_FLAGS mean the grid is probably wrong; the
+# others are informational.
+def table_flags(cand: TableCandidate) -> list[str]: ...
+
+# Per property, the distinct information sources behind the agreeing readings.
+def witness(primary: TableCandidate, agreeing: list[TableCandidate], cands: list[TableCandidate], blocks: list[Block]) -> dict: ...
+
+BAD_TABLE_FLAGS = ...
+CURRENT_GENERATOR = 'unknown'
+DIAGRAM_BOXES: dict = {}
+NUM_JOIN_REFUSED = [0]
+
+# + 35 private functions or classes
```

## `lib/pdf/tablemodel.py` (added)

```diff
+# Lossless table model and its semantic flattening to plain Markdown.
+
+# Spans read from the geometry of a table's cells (lists of spans).
+def detect_spans(columns) -> list[dict]: ...
+
+# (new grid, kept spans) with the flattening convention applied.
+def flatten(grid, spans, empty, combine): ...
+
+# Text grid version (used by the scorer).
+def flatten_text(rows, spans): ...
+
+# <!-- tomd:merged ... --> for the spans (1-based rows/columns).
+def marker(spans) -> str: ...
+
+SEP = ' / '
+
+# + 3 private functions or classes
```

## `lib/pdf/tagged.py` (added)

```diff
+# Table detection from the PDF's accessibility tags (Tagged PDF).
+
+# All tables marked up in the document's structure tree.
+def extract_tagged_tables(doc) -> list[TableCandidate]: ...
+
+# + 5 private functions or classes
```

## `lib/pdf/types.py` (changed)

```diff
@@ -88,4 +88,18 @@
     wording_role: str | None = None
 
+@dataclass
+class TableCandidate:
+    # A table proposed by one independent extractor, before selection.
+    source: str
+    rows: list[list[list[Line]]]
+    bboxes: dict[int, tuple[float, float, float, float]] = field(default_factory=dict)
+    flags: list[str] = field(default_factory=list)
+    def cell_text(self, r: int, c: int) -> str: ...
+    @property
+    def pages(self) -> list[int]: ...
+    @property
+    def shape(self) -> tuple[int, int]: ...
+    def text_rows(self) -> list[list[str]]: ...
+
 # Compute the bounding box enclosing all given bbox tuples.
 def compute_bbox(bboxes: list[tuple]) -> tuple[float, float, float, float]: ...
```

## `lib/pdf/validate.py` (added)

```diff
+# Round-trip self-verification of an extracted table against the page.
+
+# The line just above the table, aligned with its columns, is its header (the region started
+# below it). `words` must include the line above.
+def add_header_above(sec, words): ...
+
+# A cell's text as tomd renders it: spans of a line joined as they are (they carry their own
+# spaces: "has_degree<G>", "C++26"), lines joined with a space. Joining spans with spaces
+# broke code into "has_degree < G >" and made correct tables fail the word-boundary check.
+def cell_text(cell) -> str: ...
+
+# (re-read section, moves) that passes verification, or (None, []).
+def escalate(sec, words, reason: str, depth: int = 2): ...
+
+# Rebuild row boundaries where both votes agree: a new row where most columns start an item
+# AND the gap above is row spacing; a continuation where neither holds; otherwise the boundary
+# stays as it was. Code is never re-segmented (its lines belong to one listing).
+def resegment_rows(sec, words): ...
+
+# A column whose cells have a wide gap at the same x is two columns: split every cell of it at
+# that x (spans left and right of the gap).
+def split_hidden_column(sec, words): ...
+
+# Rows whose cells hold several entries on shared baselines become one row per baseline (the
+# drawn cell grouped several entries).
+def split_stacked_rows(sec, words): ...
+
+# Another source's reading of the same region, the first that verifies.
+def switch_reader(sec, words): ...
+
+# "" when the grid is consistent with the page, else what failed.
+def verify_layout(sec: Section, words: list) -> str: ...
+
+# A table stitched across pages: each piece against its own page's words (words_on(page,
+# bbox)), then the whole by its parts. "" when every piece verifies, else "page N: what
+# failed".
+def verify_pieces(sec, words_on) -> str: ...
+
+# + 16 private functions or classes
```

## `lib/pdf/visibility.py` (added)

```diff
+# Text the PDF holds but the page does not show.
+
+# classify the page once per document, record the regions on the document, and return them
+# (before any redaction: the caller removes them)
+def check_page(page) -> list[dict]: ...
+
+# The page's text that the page does not show, as regions: {page, bbox, why, chars, text,
+# action, points}; points are the character centres to redact (empty when the text is kept or
+# already gone).
+def classify(page) -> list[dict]: ...
+
+# the Removed-content lines: one per reason, with its pages
+def discards(regions: list[dict]) -> list[tuple]: ...
+
+# the list at the end of the Markdown: each region's page, box, reason and text, quoted in a
+# code fence - shown to an analyst, never read as the paper
+def markdown(regions: list[dict]) -> str: ...
+
+# every region recorded for the document, in page order
+def regions_of(doc) -> list[dict]: ...
+
+# redact (in memory) the characters of the removable regions; True if any
+def remove_hidden_text(page, regions) -> bool: ...
+
+# the summary's `visibility` object
+def summary(regions: list[dict]) -> dict: ...
+
+WHY_TEXT = ...
+
+# + 8 private functions or classes
```

## `lib/pdf/worddict.py` (added)

```diff
+# A fixed English word list for deciding line-end hyphens in table cells (2026-10-23).
+
+def available() -> bool: ...
+
+# w, or w with a common inflection removed, is in the word list (False without one).
+def is_word(w: str) -> bool: ...
+
+def words() -> frozenset | None: ...
+
+DICT_PATH = Path('/usr/share/dict/web2')
+DICT_SHA256 = ...
```
