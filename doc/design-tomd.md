# tomd: a PDF-to-Markdown converter that trusts a table only when independent evidence agrees, and says so in the output

**The design of the tomd converter at `tables-reportlab` HEAD `5809ae7`: the whole PDF path, with the table pipeline in depth, its output contracts, and how its quality is measured.**

---

## 1. Executive Summary

tomd turns a WG21 paper (PDF or HTML) into Markdown that a person or an AI can read. Each PDF conversion writes up to three files: the Markdown (`paper.md`), a prompts file of everything tomd is unsure about (`paper.prompts.md`, written only when something is), and a machine-readable paper summary (`paper.summary.json`, new in this branch). The text path has not changed: two independent extractions of every page, compared word by word, with agreement as the confidence. This branch rebuilds the table path on the same principle.

**Readers and trust.** Up to nine table readers share as little logic as possible. Each one reports what it saw and what it rejected. A table is trusted (HIGH, level L0) only when readers using different kinds of information agree on it and every character in its area is accounted for. Every other table is still emitted, with a graded level (L1 to L4) that says how it may be wrong. Any area that may be a table but was not produced gets a mark (L5). No candidate is dropped without a trace. All of this goes into HTML comments, the prompts file and the summary JSON. The Markdown itself stays plain.

**Determinism and locality.** These are invariants. The same PDF gives byte-identical output under any hash seed. One table's evidence, failure or vocabulary never changes another table.

**LLM tier.** An optional LLM tier, on only in the `--corpus` profile, can repair the structure of flagged tables. It cannot write text: it answers with word indices. Its repairs stay flagged, keep the first reading, and run under a per-run and a per-paper token budget.

**Measured results.** Against answer keys built blind by AI agents from page images and the text layer, under written conventions decided by a person (a blind re-key of 30 papers by other agents agrees on 147 of 154 tables, 95.5%, and 5,974 of 5,990 cells), mean per-table accuracy on the 1,746 tables of the eleven tuning sets rose from 12.3% (original tomd) to 84.2%. On fresh10, the least-tuned set (142 tables), it rose from 4.0% to 67.1%. Every HIGH table was right: 447 of 447 on the tuning sets and 27 of 27 on fresh10. Silent misses on the tuning sets fell from 1,438 to 47. Docling scores 51.9% and Table Transformer 45.5% on the same tuning tables.

**Targets not met.** The targets were 90–95% on the tuning sets and 80% on unseen papers, and neither is met. fresh10 has been looked at several times and is weakened as an unseen check. The untouched checks are the 200-paper reserved pool and the newest WG21 mailing, both frozen until the final benchmark. Paper confidence is a calibrated base rate that barely tells papers apart. LLM dollar figures are estimates at assumed list prices.

**Reviewing.** Read the branch as the stacked `pr2/*` series described in the last section.

---

## 2. Key Design Choices

1. **A table is trusted only on agreement between independent readers.** tomd emits HIGH only when a second reader produces the same cells, or tomd's text-position reading is a correct subset of a fully ruled table, and when every letter and digit in the table's area appears in the cells as often as on the page. *Evidence:* HIGH was right 447 of 447 times on the tuning sets and 27 of 27 on fresh10, including false tables. On the tuning sets, wrong HIGH key tables fell from 169 to 0, and non-tables marked HIGH from 647 to 0 (the original tomd: 816 trusted-but-wrong on the tuning sets, 175 on fresh10, 991 overall). *Tension:* most correct tables have a single source or come from readers that disagree, so they are flagged. 1,280 tables on the tuning sets are exactly right, but only 447 of them are L0 (L0 and HIGH are the same 447 tables).

2. **Independence is counted per kind of information and per property, never per reader.** Every piece of evidence is labelled with its information type: words, paths (drawn rules, boxes, shading), tree (PDF tags), meaning (content kinds, poll vocabulary, shared code) or document. Two readers of the same text layer count as one witness to the text. Drawn dividers and shading set a table's extent, but they are not a second witness to it. Document priors (the paper's typography, generator, whether it is tagged) shape likelihoods and never count as a witness. *Evidence:* agreement between readers of one text layer proves nothing about the text. On p3830r0 all three sources agreed on "WF" where the page prints "F". So code-pair agreement with the content builder is recorded as a witness but never makes HIGH. *Tension:* a damaged text layer is a common-mode failure. Only the opt-in OCR check sees it.

3. **Nothing is lost silently.** A reading that fails a rule check is never simply erased: it is recorded with the rule that rejected it, and its area becomes a possible-table mark unless no kept table needs it. Removed headers, contents pages, hidden text, skipped documents and reader exceptions are all listed in the prompts file and the summary. *Evidence:* silent misses fell from 1,438 to 47 on the tuning sets and from 132 to 10 on fresh10. An audit of 2,490 rejected readings found that 95–100% per rule are not tables, and including them would have cost far more than marking them. Counted by area instead, the large drop rules are not near-perfect discards: 7–12% of the areas they exclude hold a key table (most already covered by another reader's table), which is why those rules leave a mark, or deliberately do not where the marks would swamp the reader. *Tension:* the marks are noisy. Grouping brought them from 4,770 uncertainty markers to 4,149 on the tuning sets, but a reader still sees many warnings over non-tables.

4. **Trust is graded L0–L5 and published per table.** A binary trusted/flagged label says only whether to trust a table. An AI reading the paper also needs to know how a flagged table may be wrong. The most severe applicable level wins, and the content is never changed by a level. *Evidence (tuning sets):* L0 is 447 of 447 exact, L1 47 of 47, L2 354 of 421 (94.6% mean), L3 320 of 453 (89.8%), L4 98 of 162 (88.8%). *Tension:* L2–L4 order trust only loosely, and "L4 incomplete" does not separate a correct partial table from a wrong one.

5. **One content-first builder reads every region; drawn lines confirm it rather than build it.** Inside a located region, rows and columns come from the words: baselines, word-gap pieces, gutters no piece crosses, row gaps or key-column starts. Specialists (polls, tags, rule bands, code pairs, column rules, records) hook in at a level and record what they added. *Evidence:* forcing the readers onto tables none of them read made about 45% of those tables exact or one fix away on the tuning sets, all of them through this builder. *Tension:* construction is the bottleneck. The partial-reconstruction experiment built only 9.5% of key rows right before validation and was reverted. It is also weakest on LaTeX booktabs: 61.5% accuracy, against 82.3% for Table Transformer.

6. **A region scan decides what is a table, from one-file checks with a measured order** *(new in this branch)*. Any cue can nominate an area. Checks turn each area into typed features. A logistic model fitted on the answer keys gives a likelihood. The decision bands are: trust (p ≥ 0.8 with two independent information types; may be trusted), build (p ≥ 0.55; built and flagged), mark (0.3 ≤ p < 0.55), and none (below 0.3; recorded only). The checks run cheapest and most decisive first, as an effectiveness ledger ranks them. A last-resort tier runs only while an area is still undecided, with per-generator tiers where a family's own ledger justifies them. *Tension:* the model and the order are fitted on the tuning sets, and every check is one more switch to keep honest.

7. **Verification needs no answer key, and diagnosis is kept apart from decision.** Conservation, round-trip layout verification and the fit witness can change a level. The relational checker, the per-dimension confidence and the plausibility checks only explain a failure. *Evidence:* switching a flagged table to another reading by its weak dimension fixed none and broke 15, so dimensions stayed diagnostic. The fit witness was right 80 of 81 times on ruled grids, which earns LIKELY (L1) but not HIGH. *Tension:* LIKELY stays below HIGH until a fresh sample shows about 99% precision out of sample.

8. **Every repair is blind, smallest-first, flagged, and keeps the first reading.** Escalation to another reading, smallest-set repair with inferred cells, and LLM repair are all allowed to change a table. None of them can raise it above L4, and each one records the reading it replaced. *Tension:* a repair that is wrong but confident (the LLM's identical double answers) stays in the output, flagged.

9. **LLM help is optional, structure-only, budgeted and fail-safe** *(new in this branch)*. It is off in ordinary use and on with `--corpus`. The model gets the page crop and indexed page words, and returns rows of word indices. A repair must use every word exactly once and pass the same layout verification as any reader. A second look, asked twice, can name wrong rows but never raises a level. *Evidence (tuning sets, at assumed prices):* mean 84.16% → 84.30%, 30 tables fixed, 23 broken, silent errors unchanged, about $74. *Tension:* it breaks exact tables (exact count −5) and spends money for a small mean gain.

10. **Determinism and locality are invariants, enforced by tests and the gate** *(new in this branch)*. No output may depend on set order or hash seed. No table's level, mark or cell text may depend on another table's evidence, on another page, or on vocabulary outside the table, beyond a pinned word list. *Evidence:* under seed 0 against seed 1, only 2 of 2,121 key tables differed before the fix, and the fix makes the output byte-identical. The five locality fixes each passed the gate with zero flips. *Tension:* some useful global signals (the paper's own hyphenation habit, a reader error anywhere on a page) are given up or narrowed.

11. **Text the page does not show is removed and listed; an unreadable PDF never yields an empty file** *(new in this branch)*. Invisible, transparent, clipped, tiny, covered or background-coloured text is removed before any reader sees it, then quoted in a fenced section at the end of the Markdown. Pages with no text layer, and text layers that are not text, produce a loud warning and a zero confidence. *Tension:* removal risks deleting real text. The two classes that guess at what lies under the text are confirmed by rendering.

12. **Paper confidence is a calibrated base rate, capped by unfamiliarity** *(new in this branch)*. The summary states the measured share of similar papers whose tables hold no silent error, with its interval. An unfamiliar paper (unmeasured generator, rare layouts, an undecided scan, no prose measure) is capped below that figure. *Evidence:* on the 370 tuning papers with tables, the stated mean is 0.87 against 0.92 actually free of silent error. *Tension:* discrimination is weak: the AUC is 0.58 on the tuning sets and 0.77 on fresh10's 43 papers.

13. **Every behaviour change ships behind a switch and through a production gate on the tuning sets.** A change passes only if no class or generator loses a correct table, gains a silent error or a false HIGH, or loses more than a point on any table. The two held-back sets stay frozen until the final benchmark. *Tension:* the code now reads over 90 `TOMD_*` switches. The targets are not met, and the one least-tuned set has been weakened by repeated use.

14. **Machine information lives beside the Markdown, never in it.** Levels, marks, notes and spans are HTML comments with a fixed syntax. Line-numbered uncertainty markers point at the exact text. The prompts file carries every alternative reading, and the summary JSON carries the counts. A Markdown viewer shows clean tables; a program reads the comments. *Tension:* the comment syntax is now a public format, so it is costly to change.

---

## 3. A PDF becomes Markdown, a prompts file and a summary

### The pipeline runs strictly in order, and table work slots in before structure

The PDF path runs one ordered pipeline per paper. Steps marked *(new)* or *(changed)* are new or changed in this branch.

```
open PDF
  ├─ early exits: slide deck, standards draft  -> skipped, never silently   (changed: cheap table scan reported)
  ├─ per page: visibility check, covered-text removal, upright copy of rotated pages   (new)
  ├─ per page: MuPDF + spatial extraction, edge items, links
  ├─ per page: drawings read once; rule-band/grid reader, poll reader              (new)
  ├─ document: prose measure (level 0), hyphenation habit, tagged reader           (new)
close PDF
  ├─ unreadable text layer / no text layer -> loud warning, confidence 0           (changed)
  ├─ header/footer strip, monospace propagation, wording, cleanup, span snap
  ├─ WG21 metadata (front matter)
  ├─ tables: text-position reader, code pairs, content builder, records,
  │          extent step, selection, gate (classifier, verification, repair)       (new)
  ├─ region scan: decide, build or mark areas no reader kept                       (new)
  ├─ rule-band rows, continuation notes, figure labels                             (new)
  ├─ possible-table marks; dual-path comparison -> sections; tables inserted
  ├─ structure: headings, lists, paragraphs, code; TOC strip                       (changed)
  ├─ reader-error scoping, levels L0-L5, optional LLM second look                  (new)
  └─ emit Markdown + prompts; summary header, JSON; hidden-text appendix           (changed)
```

Readers run while the document is open, so each page's drawings and characters are read once and shared. The cost of reversing this order is high. Structure classification assumes that table regions have already been removed from both text paths, and the line numbers in the uncertainty markers assume that the summary comment and the hidden-text appendix are inserted after emission and shifted for.

### The dual-path text extraction stays the confidence mechanism for prose

Every page is still extracted twice: by MuPDF's block hierarchy and by a spatial walk over raw characters with four font-relative thresholds. The two are compared with a five-stage cascade. Where they disagree, the MuPDF text is emitted under an uncertainty marker and both versions go to the prompts file. This branch leaves the mechanism unchanged. It does add one rule: a table's lines are removed from both paths, except lines whose words the table did not capture, so text is never lost to a table.

### Structure, TOC and front matter: three narrow fixes

Headings, lists, paragraphs, code blocks and WG21 front matter work as before, and front matter is still written as YAML. The branch changes three things (changed in this branch):

- A TOC entry must name a heading that appears later in the document. Previously, a paper with no TOC had its own leading headings stripped as "contents".
- A selected table is never removed as a contents entry.
- A page promoted from uncertain to confident is rebuilt from scratch rather than appended twice.

Two locality guards also land in structure. Text carrying a possible-table mark never merges with unmarked text. A merged code block keeps a mark only for its marked parts, and never across a page.

### HTML conversion is a separate, single-source path

HTML papers go through DOM traversal with per-generator metadata. There is one source, so there is no uncertainty. This branch does not touch it; its architecture document remains the reference.

---

## 4. Readers produce independent evidence, typed by what they read

### Each reader reads one kind of information and records what it rejected

Every reader is an independent way to see a table. It proposes candidates with page boxes, rows and cells, flags its own doubts, and writes every nomination and exclusion, with the deciding rule, to the paper's evidence record.

| Reader | Reads | Information type | Status |
|---|---|---|---|
| Tagged | the PDF structure tree (Table/TR/TH/TD) | tree | new |
| Poll | an `SF F N A SA` line and the counts under it, however drawn | meaning + words | new |
| Grid | tables ruled in both directions | paths | new |
| Rule band | horizontal rules and shaded row boxes (booktabs, ReportLab) | paths | new |
| Column rules | tables drawn with vertical rules only | paths | new |
| Code pairs | two monospace blocks side by side that share code | words + meaning | new |
| Content builder | the words of any located region, top down | words | new |
| Records | repeating kinds of lines (name, number, number, ...) | meaning | new |
| Text positions | columnar MuPDF blocks (the original detector) | words | changed |

The column-rule reader is its own reader but emits its candidates with source `grid` (`_column_ruled_tables`), so it shares the grid slot in selection's priority.

Readers fail independently. An exception in any reader is caught, recorded as a reader error (stage, page, type, message), listed in the prompts file and the summary, and it downgrades only the tables that stage touched (new in this branch). `TOMD_STRICT=1` re-raises instead, for tests. This contract exists because a silent reader failure would look exactly like "no table here".

A lightweight C++ line reader (bracket depth, unit starts, statement ends) is present and tested. It is wired only behind `TOMD_CODE_BY_CONTENT=1` (new in this branch, off).

### The evidence record is the only channel between readers and decisions

Later steps never read a reader's private verdict. They read the record: the scan, the marks, the prompts and the diagnosis all do. Each entry carries its provenance (observed on the page, or inferred by a reader) and its information type. This record is what makes "nothing lost silently" checkable. It is also what allows independence to be counted by type rather than by reader. Reversing it would mean re-plumbing every consumer to every reader.

### Level 0 measures the document before any table is judged

Before any table is judged, tomd measures what ordinary prose looks like in this paper: its left and right edges, whether it is justified, the normal word space per text height, and whether the paper hyphenates at line ends (new in this branch). Table features are judged against this measure: inset from the margin, bimodal word gaps, ragged right edges. The rule behind it is to size each container from all of its content first, then fit and check each piece. The document's units come from the whole text, a table's extent from every row that shares its grid, and a row's band from its tallest cell.

---

## 5. Selection, verification and repair turn readings into one table per region

### Selection prefers specialists, then lets evidence break ties

Candidates are grouped by position, and continued pieces are stitched across page breaks: by the same reader when the columns match, and across readers when they differ (such joins are never HIGH). Rule checks then remove readings that look like contents, lists, references, comment columns, ragged or split code. The primary reading is the first one without a bad flag, in priority order (`_SOURCE_PRIORITY`): tags, poll, grid, malformed tags, rule band, code pair, text positions, content, records. "Malformed tags" is a priority slot, not a reader: a tagged reading flagged as malformed drops below the grid. So there are nine readers and nine slots, but they do not line up one to one: the grid and column-rule readers share the grid slot, and the tagged reader holds two slots. Ties within one priority level are broken by evidence (conservation, support), never by the order readers happened to run.

A per-generator reader track record was tried twice as the ranking and failed the gate both times. It stays off (`TOMD_TRACK_ORDER=1`). The measured ceiling for selection is small: on the 420 tuning tables where the emitted table is one of several competing readings, the current choice averages 93.4% and a perfect choice would average 97.6%, worth under 2 points of overall tuning accuracy. A calibrated per-reading model (cross-validated AUC 0.87) still could not beat the current choice on held-out folds.

### HIGH needs agreement plus conservation; the gate can also lower it

Confidence is HIGH when another reader agrees cell for cell, or when tomd's text-position reading is a correct subset of a fully ruled table. It is UNCERTAIN when the reading has a single source or when readers disagree, in which case every version goes to the prompts file. A stage-2 gate then describes each selected table with cheap geometric features. Two small decision trees, learned from the keys, answer two questions: is this a table, and of which layout class?

The gate can lower HIGH. It can also raise a single-source table, but only when its leaf is pure, the class matches the reader, and that class's own check passed. Three further rules (new in this branch) can only lower a table:

- A grid whose cells are mostly images is never HIGH.
- Damaged-text characters force UNCERTAIN.
- A conservation surplus (characters in cells more often than on the page) forces L4.

### Verification without a key is the backbone of the levels

Each flagged table is put back on the page and checked against it. Every word in the area must fall in exactly one cell, cells must spell their words in page order, rows must stack, and columns must sit side by side. The fit witness asks whether the words sit evenly inside the drawn cells; if they do, a flagged table is LIKELY.

The relational checker lists every contradiction between what a table asserts (shared row, column or cell) and what the page shows (baselines, gutters, rules). It reports these by dimension: rows, columns and cells. Per-dimension confidence (rows, columns, header, cells) and content plausibility only diagnose. They are metadata and prompts, and never a level change, because acting on them measured net harm.

### Repairs are ordered from cheapest to costliest, and none is trusted

There are three repair steps, tried in order:

- **Escalation.** When verification fails, tomd switches to an alternative reading that passes.
- **Smallest-set repair.** Stray page words that lie in a column's span and a row's span are placed in that cell. Words outside every row become an inferred row, marked in the output with `tomd:inferred`.
- **LLM repair.** Optional; described in section 9.

Each repair records the reading it replaced, and each leaves the table flagged.

### Extent, rows and continuation have their own steps

Extent, rows and continuation are handled by separate steps:

- **Extent step.** Records why each reader stopped. It attaches a row just outside a reading when that row's text sits over the body's columns, when a shaded band spans it, or when the body's vertical rules run through it. A label row found under the columns becomes the header and is noted (`tomd:header-below`).
- **Full-width rows.** In ruled tables, these become spans.
- **Stacked entries.** Entries stacked in one band are one row each.
- **Rule-band rows** (new in this branch). In a grid whose records are separated by drawn rules, a continuation line with an empty key cell joins the row above. The join is blocked when the line fills at least two-thirds of its other columns (the fill guard).
- **Continuation notes** (new in this branch). A note says a piece *may* continue the previous page's table, but only when the first column's numbering also continues. The note never joins pieces. On the tuning sets it fired 15 times: 10 right, 5 wrong.

A real page join is not built, because no measured signal separates continued tables from separate ones.

### Rendering follows written table conventions, losslessly underneath

Internally, a table keeps its spans. In Markdown, spans are flattened by meaning:

- combined headers ("Top / Sub");
- category labels repeated in each row;
- shared values and titles kept once.

Every span is also written into a `tomd:merged` comment. Some tables have a special use:

- **Code comparisons** become paired code blocks (`tomd:table kind=code-comparison`).
- **Contents, label–value blocks and heading-like grids** are rendered as what they are, under a `tomd:use` comment.
- **Probable formatting grids** are marked `tomd:use formatting?`.
- **Tables drawn inside a figure** get an italic label naming the figure.

Wrapped cells join their lines with `<br>`. A line-end hyphen in a cell is kept or dropped by the table's own words plus a pinned English word list (new in this branch). Two pure numbers on separate cell lines are never joined into one value.

---

## 6. The region scan decides, builds or marks every area any cue nominated

### Nominating is cheap and decides nothing

Areas come from the evidence record: every place any reader or scan nominated or excluded, merged per page. Each table takes the single scan area that best covers its own box, not a chain of areas that includes a neighbour (locality fix 2b).

### Checks are one file each, typed, tiered and switchable

Each check under `lib/pdf/checks/` declares:

- its name;
- the level it serves;
- the information type it reads;
- a cost tier;
- whether it is optional (needs a network or costs money);
- a function from the area to evidence items.

The checks are drawn lines, text alignment, word gaps, footprint, caption, coherence, plausibility, same code, data-or-format, nominations and the code reader. A check never changes a grid. Every check can be switched off by name (`TOMD_CHECKS_OFF`), which is how the ledger measures each check's unique contribution.

The registry runs in a fixed order. Word gaps, footprint and caption add least on their own and form a last-resort tier. That tier is promoted per generator family where the family's own ledger shows a gain: word gaps for LibreOffice, ReportLab and Chrome/Skia, and footprint for "other" generators. `TOMD_SCAN_FULL=1` runs everything (for training data and the ledger).

### Four bands turn a likelihood into an action

A logistic model gives each area a likelihood, recorded with its top supporting and opposing features. Thresholds are HIGH = 0.8 and LOW = 0.3; the build band starts halfway between them, at 0.55 (`scan.band`).

| Band | Likelihood | Action |
|---|---|---|
| trust | ≥ 0.8 and two independent information types | may compete for HIGH |
| build | ≥ 0.55 (including ≥ 0.8 with only one information type) | built by the content builder, emitted UNCERTAIN, gated like any table |
| mark | 0.3 ≤ p < 0.55 | possible-table mark (L5) |
| none | < 0.3 | recorded only |

A built area that reads as contents or label–value entries stays a mark. An optional Jev meaning tier batches up to 40 areas per paper (`TOMD_JEV=1`, off). The documented reason it stays off is that it batches many areas into one prompt, which breaks locality.

### Drops leave marks, grouped one per area

An area a reader nominated and a rule then excluded becomes a possible-table mark wherever no kept table covers it. This is the drop-to-mark policy, decided by harm to an AI reader with wrong facts weighted 2x and 3x. A few drop rules leave no mark, because they measured almost never a table: prose between rules, too few rule bands, monospace prose, page furniture, and pure list, reference or comment-column flags.

A mark never crosses a page break and never takes in lines outside its region. Consecutive sections carrying the same mark share one uncertainty marker (new in this branch, `TOMD_MARK_GROUP_ALL`).

---

## 7. Trust levels, marks and notes are the reader-facing contract

### L0–L5 have fixed meanings

| Level | Name | Meaning | Emitted as |
|---|---|---|---|
| L0 | trusted | HIGH: independent sources agree, characters conserved | plain table, no marker |
| L1 | likely | flagged, but the words fit the drawn cells evenly | `tomd:likely` + uncertainty marker |
| L2 | minor | flagged on one source; every content check passed | `tomd:level L2` + uncertainty marker |
| L3 | structure-uncertain | readers disagree, fit or layout check failed, relational violations, open extent, joined from two readers | `tomd:level L3` + marker |
| L4 | content-at-risk | duplicated or misattributed text, damaged text, cells out of order, a reader error, repaired (including by the LLM); "incomplete" when text is only missing | `tomd:level L4` + marker |
| L5 | mark-only | a possible table that was not produced | uncertainty marker over the text |

Levels are metadata, and the cell text is the same whatever the level. The level comment for a flagged table lists the reasons. For L2 and above, it also lists the cells (`cells=r1c2,...`) where alternative readings of the same shape disagree.

### The comment syntax is a public format

The following lines are the complete set tomd writes into Markdown. Each is an HTML comment on its own line. Most go directly before what they describe. The summary goes after the front matter, warnings go at the top, and hidden-text entries go in the appendix. Fields in braces are filled in; the free text in parentheses may change wording but not position.

```
<!-- tomd:summary tables=N trusted=N flagged=N likely=N marked=N confidence=X.XX unfamiliarity=X.XX [hidden=N] -->
<!-- tomd:uncertain:L{start}-L{end} -->                     the lines of the text that follows
<!-- tomd:level L{n} {name}[ (incomplete)]: {reasons}[ cells=r{r}c{c},...] -->
<!-- tomd:likely reason=fit (...) -->
<!-- tomd:continues page={N} (may continue the table on page N: {reasons}; not merged) -->
<!-- tomd:header-below (...) -->
<!-- tomd:table kind=code-comparison cols={N} -->
<!-- tomd:merged {kind} row[s]={r[-r]} col[s]={c[-c]}; ... -->
<!-- tomd:use heading|label-value|contents|formatting? (...) -->
<!-- tomd:inferred cells={...} (...) -->
<!-- tomd:hidden page={N} bbox={x0,y0,x1,y1} why={class} chars={N} -->
<!-- tomd:warning:graphic-text pages={list} -->   <!-- tomd:warning:image-pages pages={list} -->
<!-- tomd:not-converted pages=1-{N} why=unreadable-text-layer -->
<!-- tomd:skipped:{reason}: {note} -->
```

`tomd:uncertain` existed on master. It is changed in this branch: it now covers flagged tables and possible-table marks, and its line numbers are shifted for the summary comment and warnings inserted above. Every other form is new in this branch.

Changing any of these forms breaks every consumer that parses them: the scorer, the downstream AI pipeline, and any regex over a corpus already converted. Add fields at the end; never rename.

---

## 8. Paper confidence states a measured base rate, not a judgement of this paper

### The summary states the rate for papers like this one

The paper model takes a handful of paper-level features: number of tables, shares trusted, likely and flagged, marks, undecided scan areas, unfamiliarity, relational violations, and low-scan tables. Its raw score maps to a band. Each band reports the share of tuning papers in it that held no silent table error (a wrong HIGH, or a missed table with no mark), with a 95% Wilson interval and the number of papers behind it. The model was refit on corrected, page-restricted labels after the determinism and locality commits (changed in this branch).

### Unfamiliarity caps the figure

Unfamiliarity is a score from 0 to 1 with stated reasons:

| Reason | Adds |
|---|---|
| generator not among the measured papers | 0.4 |
| rare layout classes | up to 0.2 |
| more than a fifth of scan areas left undecided | up to 0.3 |
| rotated text | 0.1 |
| no prose measure | 0.2 |
| skipped document | 0.3 |

The stated confidence is capped at 1 − 0.5 × unfamiliarity, and the summary says when the cap applied. A paper whose text is drawn as graphics, or whose text layer is unreadable, gets confidence 0.

### The figure is honest on average and weak per paper

On the 370 tuning papers with tables, the stated mean is 0.87 and 0.92 were actually free of silent error. On fresh10, 0.86 was stated and 39 of 43 papers (0.91) were free of silent error. The stated confidence separates good papers from bad ones poorly: AUC 0.58 on the tuning sets, 0.77 on fresh10's 43 papers, which is weak evidence. Better discrimination needs per-table evidence in the model, not paper averages.

---

## 9. The LLM tier: optional, structure-only, budgeted, and never trusted

### It is on only in the corpus profile, and it fails safe

| Item | What it does | Model | Only when |
|---|---|---|---|
| Repair | rearranges a flagged table's page words into rows, by index | claude-opus-5-5 | `TOMD_LLM=1`, L3/L4 tables (all flagged with `TOMD_LLM_ALL_FLAGGED=1`) |
| Second look | "do these rows match the page? which are wrong?" | claude-sonnet-5-5 | `TOMD_LLM_CHECK=1`, L3/L4 single-page tables |

Both are turned on by `--corpus` and nothing else. Both ask twice and use only identical answers. Both are cached by PDF hash, region, model and prompt version. Credentials are resolved by the Anthropic SDK, and tomd never reads, logs or prints a key. With no credentials, rejected credentials, a network error or a spent budget, the run continues without the LLM, and the paper summary's `witnesses.llm` says why.

### Guards keep the LLM from writing text or losing it

A repair is kept only if three things hold:

- it uses every word of the region exactly once;
- it passes layout verification;
- it does not add a line-number column to code (the code guard, new in this branch).

A kept repair sets the table to L4, records "llm-repaired", and keeps the first deterministic reading and its reader in the metadata and the prompts file.

The second look never changes text and never raises a level. A confirmed "no" adds the rows to check to the table's note and level comment. It was right 81% of the time (60 of 74). A confirmed "match" was right only 65–72% of the time, too weak to raise anything.

### Budgets cap the spend per run and per paper

`TOMD_LLM_BUDGET` caps the tokens for a run. Under `--corpus` the default is 5,000,000, or the value of `--llm-budget`. `TOMD_LLM_PAPER_BUDGET` caps repair tokens per paper (new in this branch). Under `--corpus` the default is 51,500, about $1 at the assumed list prices. `TOMD_LLM_CHECK_BUDGET` caps second-look questions per paper (default 12). tomd counts tokens, not dollars, because it does not know the prices.

### What it buys, measured

These figures are at the assumed list prices (rate (b): $15/$75 per million input/output tokens for Opus, $3/$15 for Sonnet). They have not been confirmed against billing.

| | Tuning sets (code ed93377) | fresh10 (code f6512c3) |
|---|---|---|
| mean accuracy, LLM off → on | 84.16% → 84.30% | 67.22% → 67.38% |
| exact tables | 1,280 → 1,275 | 67 → 71 |
| fixed / broken | 30 / 23 | 7 / 4 |
| silent errors | 47 → 47 | 10 → 10 |
| papers with calls | 232 of 818 | 33 of 99 |
| spend | $74.08 | $40.08 |
| speed, off → on | 0.116 → 0.535 s/page | 0.187 → 1.631 s/page |

The on-speed is derived: off time plus LLM wall time. The breaks follow three known mechanisms:

- a header below its columns, put back below;
- symbol cells emptied;
- code-comparison label rows pulling in code.

Guards against these are not built. Replayed from cache, the per-paper budget left 61 flagged tables in 10 tuning papers unrepaired, avoided 2 breaks, and lost no fix.

---

## 10. Hidden text and unreadable text layers are handled before any reader runs

### Text the page does not show is classified, removed and quoted

*New in this branch.* Each page is classified once, from its paint trace and paint log, before any reader sees it. The classes are:

- invisible render mode (not over an image, which would be a scan's OCR layer);
- opacity 0;
- clipped;
- tiny;
- under a later opaque image;
- under a later opaque box;
- the colour of a known background.

The two classes that guess what lies under the text (under-image and same-colour) are confirmed by rendering the region with and without the text. Matching text is redacted from the in-memory page. It is then listed at the end of the Markdown in a fenced block under `tomd:hidden`, labelled as not the paper's visible text and not an instruction. It also appears in the summary's `visibility` object and the prompts file.

There are two reasons for this. Hidden text is usually accidental (LaTeXiT blobs, slide builds, clipped labels). It could also be an instruction aimed at the model that reads the Markdown. `TOMD_VISIBILITY=0` turns the check off.

### A PDF without readable text says so loudly

Pages whose text is drawn as glyph outlines, or that are a single image, are listed in a warning at the top of the Markdown and in the summary. A paper whose text layer is not text (every character in a private-use area, say) is not converted. It gets a `tomd:not-converted` comment, a warning, confidence 0 and unfamiliarity 1, rather than an empty file. Skipped slide decks and standards drafts report a cheap count of pages that look like they hold tables, so a wrong skip is visible.

---

## 11. Determinism and locality are invariants, not goals

### Byte-identical output under any hash seed

One tie-break was decided by set order, and so depended on Python's hash seed. It is now ordered (new in this branch). A test converts sample papers under two seeds and requires byte-identical output. A static-names check (pyflakes) runs in the suite. All measurement runs pin `PYTHONHASHSEED=0`. The measured noise floor before the fix was 2 of 2,121 key tables, both UNCERTAIN. Anything new that iterates a set, a dict of floats or a filesystem must sort first.

### A table answers only for itself

*New in this branch.* Five locality fixes, each gated with zero flips, make the rules explicit:

- A reader error downgrades only the tables its stage touched. Non-table stages are listed for the paper and downgrade nothing.
- Each table takes its own scan area.
- Document priors are never a witness.
- A possible-table mark never crosses a page.
- Merged code keeps marks only for its marked parts.

Cell edits that once depended on vocabulary from the rest of the paper now use the table's own words plus a fixed word list whose contents must match a pinned hash. Without that list, the earlier behaviour stands. Reversing locality would let one table's trouble rewrite another's level, which is exactly what made levels hard to trust before.

---

## 12. Output contracts: three files, a stable JSON, and switches that default to the measured behaviour

### The command line writes three files; ordinary use never calls a network

`tomd paper.pdf` writes `paper.md` and `paper.summary.json` (new in this branch). It writes `paper.prompts.md` only when something is flagged, removed or failed, and deletes a stale prompts file otherwise. `--outdir` and `-o` place the files. `--qa` scores Markdown only, and never sees converter state. `--corpus` turns on the LLM profile. When the LLM was asked for, the run ends with one status line giving tokens spent and budget.

The prompts file gains new sections in this branch:

- every alternative reading of a flagged table;
- the removed-content list;
- reader errors;
- visibility;
- the paper summary.

### The summary JSON has stable keys; optional keys appear only when they apply

`paper.summary.json` (new in this branch) is one object. Its keys are stable. Optional keys appear only when they apply.

| Key | Contents |
|---|---|
| `tables` | `total`, `trusted`, `flagged`, `likely`, `trusted_pages`, `flagged_pages`, `likely_pages`, `types` (layout class counts), `with_violations` |
| `continuations` | list of `{page, from_page, reasons}` for continuation notes |
| `marks`, `marked_pages` | possible-table marks and their pages |
| `removed` | list of `{what, why}`: headers, contents, hidden text, dropped candidates, skipped document, table-count shortfall |
| `scan` | `areas`, `undecided`, `low_tables` |
| `unfamiliarity` | `score` (0–1), `reasons` |
| `generator` | producer family (LaTeX, Word, Google Docs, ReportLab, ...) |
| `confidence` | `value`, `low`, `high`, `band`, `band_low`, `papers`, `raw`, `capped`; or `{value: 0, capped, reason}` when not converted |
| `visibility` | `regions`, `chars`, `by_why`, `hidden` (page, bbox, why, chars, action, text), `truncated` |
| `witnesses` | optional: `llm` (status, model, calls and results, tokens, seconds, run budget and spent, unrepaired by paper budget), `llm_check`, `jev` |
| `reader_errors` | optional: list of `{stage, page, type, message, kind, table}` |
| `graphic_text_pages`, `image_pages`, `not_converted` | optional: pages not converted and why |

### Switches follow one rule, and a few are user-facing

The generating rule is simple. Every improvement in the table path ships behind `TOMD_<NAME>`, on by default, and `TOMD_<NAME>=0` restores the earlier behaviour. The gate and the ledger use the same switch to measure what each change contributes. Measured experiments that did not pass ship off, and `=1` turns them on. The switches a user or operator may set are listed below. All others are kill switches for single improvements; decide by use.

| Switch | Default | Effect |
|---|---|---|
| `--corpus` | off | sets `TOMD_LLM=1`, `TOMD_LLM_CHECK=1`, `TOMD_LLM_BUDGET=5000000`, `TOMD_LLM_PAPER_BUDGET=51500` unless already set |
| `--llm-budget N` | — | overrides `TOMD_LLM_BUDGET` |
| `TOMD_LLM` | off | LLM repair of L3/L4 tables |
| `TOMD_LLM_BUDGET` | none (5,000,000 in `--corpus`) | tokens per run |
| `TOMD_LLM_PAPER_BUDGET` | none (51,500 in `--corpus`) | repair tokens per paper |
| `TOMD_LLM_CHECK` / `TOMD_LLM_CHECK_BUDGET` | off / 12 | second look; questions per paper |
| `TOMD_LLM_ALL_FLAGGED`, `TOMD_LLM_ASK_ONCE`, `TOMD_LLM_REPAIR_CHECK` | off | repair every flagged table; ask once; gate repairs on the second look |
| `TOMD_LLM_CODE_GUARD` | on | reject repairs that add a line-number column |
| `TOMD_CACHE_DIR` | `~/.cache/tomd` | LLM answer cache |
| `TOMD_JEV` / `TOMD_JEV_BUDGET` | off / 40 | Jev meaning tier in the scan and gate |
| `TOMD_OCR` | off | OCR check of HIGH tables (needs tesseract) |
| `TOMD_VISIBILITY`, `TOMD_GRAPHIC_TEXT` | on | hidden-text removal; graphic-text page detection |
| `TOMD_SUMMARY`, `TOMD_LEVELS` | on | summary JSON and header; L0–L5 comments |
| `TOMD_RULE_BANDS` | on | rule-band row joins (with the fill guard) |
| `TOMD_CONTINUES` / `TOMD_CONTINUES_ALL` | on / off | continuation notes; notes without the numbering condition |
| `TOMD_MARK_GROUP_ALL`, `TOMD_MARK_ONE_PER_AREA` | on | one uncertainty marker per marked area |
| `TOMD_DROPMARK` | `misread` | which rejected readings become marks (`misread`, `all`, `0`) |
| `TOMD_SCAN_FULL`, `TOMD_CHECKS_OFF=a,b` | off / empty | run every check; switch named checks off |
| `TOMD_GEN_TIERS` | on | per-generator check tiers |
| `TOMD_TRACK_ORDER`, `TOMD_DIAGRAMS`, `TOMD_CODE_BY_CONTENT`, `TOMD_CODEPAIR_HIGH` | off | experiments measured and not adopted |
| `TOMD_STRICT` | off | reader errors re-raise (tests) |

---

## 13. Quality is measured against answer keys, through a gate, with sets held back

### Answer keys define "right", and per-table accuracy is the primary metric

The harness lives outside this repo. It scores tomd against answer keys built blind by AI agents from page images and the text layer, never seeing tomd's output: one JSON per paper of the tables a reader should get, under written conventions for spans, code comparisons, front matter and table uses. Key changes are recorded with their reason. A subset of the keys ships as test fixtures. The conventions were decided by a person, who also approved every key change, but no person checked the keys table by table. A blind re-key of 30 papers by other agents checks the keys themselves (147 of 154 tables, 95.5%, and 5,974 of 5,990 cells agree). A second labeller, also an agent, agrees with the table categories 93.5% of the time (kappa 0.90).

The primary metric is mean per-table accuracy, scored one-to-one and restricted to the key table's own pages (that restriction corrected an earlier, generous scorer). It is reported with exact tables, silent errors (missed without a mark, or trusted but wrong), false tables, per-layout class, per-generator and per-category results, and a loss budget by cause.

### Sets have roles, and the roles are kept

| Role | Sets | Use |
|---|---|---|
| Tuning | dev, heldout, fresh, fresh2–fresh9 (818 papers, 1,746 key tables) | development, gate, fitting |
| Least-tuned check | fresh10 (99 papers, 142 key tables) | scored once per change set, reported apart; weakened |
| Untouched | 200-paper reserved pool; the WG21 mailing released around 2026-10-23 | frozen: not opened, converted or keyed until the code is frozen; scored once |

fresh10 is weakened as an unseen check. It informed one default (the diagram flag, switched off after it broke a fresh10 table). It was also used for the LLM-on runs, the code-guard and budget replays, and the rule-band checks. Its figures are therefore slightly optimistic.

### The production gate refuses any loss, per class and generator

Every change runs on the tuning sets with `PYTHONHASHSEED=0`, against the reference run, per layout class and per generator. The verdict is:

- **FAIL** if any class or generator loses a correct table, gains a silent error or a false HIGH, or if any table loses more than one point, or the content-weighted total drops.
- **WARN** if the flagged count or flagged false tables rise more than 10%.
- **PASS** otherwise.

A gate is read only after confirming zero reader errors. Flips within the noise floor (about ±1 table) are not evidence. Tuning follows the rule that a fix must name its mechanism in one sentence and generalise, with no paper-specific constants. A change that fails the gate twice is reverted.

### tomd is far ahead of where it started and short of its targets

| | Original tomd | HEAD, LLM off |
|---|---|---|
| tuning mean / median accuracy | 12.3% / 0% | 84.2% / 100% |
| tuning exact tables | 111 | 1,280 |
| tuning silent misses / wrong-HIGH | 1,438 / 169 | 47 / 0 |
| fresh10 mean / median | 4.0% / 0% | 67.1% / 97.9% |
| fresh10 silent misses / wrong-HIGH | 132 / 8 | 10 / 0 |

On the same tuning tables, Docling scores 51.9% and Table Transformer 45.5%. On fresh10 they score 42.8% and 36.1%. Booktabs (61.5% against 73.5% and 82.3%) and code in cells (43.9% against 53.3% and 55.4%) are the layout classes where both beat tomd.

By producer on the tuning sets, accuracy is:

| Producer | Tables | Mean accuracy |
|---|---|---|
| LaTeX | 881 | 78.8% |
| Word | 199 | 84.9% |
| Google Docs | 174 | 93.4% |
| ReportLab | 242 | 98.2% |

The largest remaining loss is tables marked but not produced: 133 tables, 7.6 of the 15.8 points lost per table.

---

## 14. Known limits: targets missed, the unseen check weakened

These limits are open; none is a closed question.

1. **Targets not met.** Tuning accuracy is 84.2% against a 90–95% target, and fresh10 is 67.1% against an 80% target.
2. **fresh10 is weakened** as an unseen check. Only the two frozen sets can support an unseen claim.
3. **LLM costs are estimates.** Every dollar figure is at rate (b). LLM repair breaks some exact tables, and guards for the three known mechanisms are not built.
4. **Paper confidence discriminates weakly.** It is a calibrated base rate (AUC 0.58 tuning, 0.77 fresh10).
5. **The rule-band fill guard is mixed on fresh10.** It was not tuned there: one grouped grid stays worse (p2318r1-t8, 53.4 → 31.6) and one table lost its exact match (p1619r2-t2, 100 → 90.8).
6. **No page join.** No signal separates continued tables from separate ones, and long split tables still score as one piece.
7. **Marks remain numerous.** There are 4,149 uncertainty markers on the tuning sets, against a grouped-area estimate of about 305.
8. **Speed was measured at load 5–6.** The LLM-on speed is derived (off time plus LLM wall time).
9. **The answer keys were made by models.** AI agents built them blind, and other agents did the re-key and the second category labelling. Keys made by models may share a model's blind spots; a human spot-check of a sample is still to do.

---

## 15. Decide by use: details that are cheap to change later

These are settled enough to build on and cheap to change when a use demands it:

- the order of check files within a tier;
- the individual kill switches;
- the exact wording inside the parentheses of comment lines;
- the band boundaries of the paper model (refit with the keys);
- the per-generator tier table;
- the size of the hidden-text appendix and summary caps;
- the default run and paper budgets;
- the cache location;
- whether the second look runs outside `--corpus`.

---

## 16. Reviewing the branch: the pr2 series

The branch is `master..5809ae7` on `tables-reportlab`: 91 commits. The `pr2/*` series is 24 local branches, `pr2/01` … `pr2/24`. They are stacked: `pr2/01` is based on `master` and each later branch on the previous one. Together they replay the branch's commits in order, so `pr2/24`'s tree equals `tables-reportlab` at `5809ae7`. The older `pr/*` series (16 PRs, up to `ecfd5f2`) is the one pushed to the fork, and it is left as it is.

| PR | Commits | Content |
|---|---|---|
| pr2/01-design | — | this document only |
| pr2/02 | … `3d4f54a` | compare independent table sources; detect polls; greedy selection; first answer-key fixtures |
| pr2/03 | … `79c21d0` | ReportLab tables and agreement rules; partial readings agree; held-out keys as fixtures |
| pr2/04 | … `084c0ba` | safety net (HIGH only on agreement and conservation, possible-table marks) and classifier gate; TOC and promoted-page fixes |
| pr2/05 | … `a0c7330` | round-trip verification, negative-space marks, visible discards, opt-in OCR |
| pr2/06 | … `76ed99a` | gated round: poll variants, span model, escalation, code comparisons, opt-in LLM repair |
| pr2/07 | … `2daafa4` | no erasure, independent witnesses per information type, code pairs, shared content-first builder |
| pr2/08 | … `c6a68e6` | evidence record, code-pair rows, drawings read once |
| pr2/09 | … `28bdc87` | region scan core, `checks/` package, rotated headers, cross-page continuation |
| pr2/10 | … `2002a8e` | text fixes, poll blank rows, header rule, rule bands, data vs formatting |
| pr2/11 | … `c7ceb12` | relationship checking, per-paper summary and confidence, figure tables, ledger ordering |
| pr2/12 | … `209faf9` | records reader, scan build band, join votes, Jev tier, `--corpus` profile |
| pr2/13 | … `c9c21ab` | fixes from the 2023 test: full-width rows, marks survive merging, recalibration |
| pr2/14 | … `002c343` | fit witness and the LIKELY level |
| pr2/15 | … `3b27581` | row fixes, plausibility checks (diagnosis), one extraction per page |
| pr2/16 | … `04c07bc` | cross-reader continuation (never HIGH) |
| pr2/17 | … `ecfd5f2` | extent step: stop reasons, headers outside the body, shading, rules through headers |
| pr2/18 | `905fe35` … `ae2fc64` | drops leave a mark; polls through pipes; column-rule reader; C++ code reader (off) |
| pr2/19 | `a8762ad` … `483e2a3` | single-cell fixes; lessons from the vision readers; reader errors never silent |
| pr2/20 | `05681ad` | hidden text; unreadable text layers |
| pr2/21 | `a9fc6de`, `dd46442` | marked-but-not-produced round 1; graded levels; wording headings; LLM second look; per-generator check tiers |
| pr2/22 | `e664bc0` … `2f57e19` | determinism; locality fixes 1, 2b, 4, 5b, 6; paper-confidence refit |
| pr2/23 | `ffc91e0` … `f6512c3` | hyphen dictionary; number rule; image grids never HIGH; one mark per dropped area |
| pr2/24 | `e6207bd` … `5809ae7` | rule-band rows and fill guard; LLM code guard; grouped marks; continuation notes; per-paper LLM budget |

**Read these first for the design:**

- `pr2/01` (this document);
- `pr2/04` (the safety net, which defines HIGH and marks);
- `pr2/07` and `pr2/08` (independence per information type, the content builder, the evidence record);
- `pr2/09` (the scan and the `checks/` contract);
- `pr2/11` (summary and paper confidence);
- `pr2/21` (levels L0–L5);
- `pr2/22` (determinism and locality);
- `pr2/12` with `pr2/24` (the LLM profile and its budgets).

**Mostly fixtures and data:**

- `pr2/02` and `pr2/03` carry about 20,000 lines of answer-key JSON against under 2,000 lines of code.
- `pr2/21` adds the reader track record (`reader_track.json`, kept off) and a few fixtures.
- `pr2/23` is about half fixture data.

**Tests:** `pr2/07`, `pr2/08`, `pr2/13`, `pr2/14`, `pr2/16` and `pr2/17` add no unit tests and rely on the goldens and the gate. Among `pr2/18`–`pr2/24`, `pr2/20`, `pr2/22` and `pr2/24` carry most of the new tests (visibility, reader errors, determinism, static names, rule bands, code guard, paper budget).

**Harness not in the repo:** the scorer and gate that produce every number here live outside the repo.

*2026-10-24, Claude Opus 5.5*
