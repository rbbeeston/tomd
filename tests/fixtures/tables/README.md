# Table truth set

Hand-verified tables for measuring table extraction. Each `<stem>.json` lists
every table in one WG21 paper, transcribed from the rendered pages by a human
reviewer following the protocol below. `test_table_truth.py` converts each
paper and checks that every in-scope table appears in tomd's Markdown with the
right grid and the right text in every cell, and that tomd emits no tables
that are not in the list.

- `tables[].rows`: cell text as printed, whitespace collapsed, lines of a
  wrapped cell joined with a space, empty cells as `""`, header as row 0.
  A table continued across a page break is one table.
- `tables[].pages`: 0-based pages the table occupies.
- `tables[].scope`: `table` (measured), `front-matter` (title-page metadata
  block, which tomd emits as YAML front matter instead), `borderline`
  (tab-aligned label/value blocks; reviewers disagreed whether these are
  tables).
- `not_tables`: regions that look like tables but are not (wording
  highlight boxes, code listings, tables of contents).
- `source_pdf`: where the PDF comes from. Only `p0533r9` and `p0957r8` are
  committed (in `../golden/`); for the others set `TOMD_TABLE_CORPUS` to a
  folder holding `<stem>.pdf` downloaded from open-std.org.

Protocol: every page was skimmed for tables; tables proposed by any
extractor were checked cell by cell against page renders (long tables: header,
first 10 and last 5 rows, and every row where extractors disagreed). Where
the PDF's text layer and its appearance differ (for example a space
character before a comma), the text layer wins and the table's `note` says
so. Text that is garbled in the PDF itself (fonts without a Unicode mapping)
was typed from the image; no text-based extractor can reproduce it.

## Sets

- 44 papers (development set): built while developing the table sources.
- 77 papers with `"set": "heldout-2026-10"`: a seeded random sample (all of
  a 60-paper draw from the 2025 mailings, plus a generator-stratified draw of
  unused 2026 papers) measured once on frozen code before any tuning on
  them (60/114 tables exact), then used to fix general bugs. They are now
  development data too; a fresh sample is needed for the next unbiased
  measurement. KNOWN_GAPS / KNOWN_FALSE_TABLES in test_table_truth.py track
  what is still open.
