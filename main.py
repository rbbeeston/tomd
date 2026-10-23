#!/usr/bin/env python3
"""tomd - Convert PDF and HTML files to Markdown.

PDF: hybrid dual extraction (MuPDF + spatial rules) with confidence scoring.
HTML: DOM traversal with generator-specific metadata extraction.

Usage (after `pip install -e tomd`):
    tomd input.pdf                  # -> input.md + input.prompts.md + input.summary.json
    tomd input.html                 # -> input.md
    tomd *.pdf *.html --outdir out/ # batch mode

Also runnable as `python -m tomd.main ...`.
"""

import argparse
import os
import glob as globmod
import sys
from pathlib import Path

_HTML_EXTENSIONS = frozenset({".html", ".htm"})
_PDF_EXTENSIONS = frozenset({".pdf"})


# fresh7 (70 papers): about 4,400 tokens per paper; 5M tokens covers about 1,100 papers
CORPUS_LLM_BUDGET = 5_000_000


def main():
    """CLI entry point: parse arguments, resolve inputs, and convert files."""
    parser = argparse.ArgumentParser(
        prog="tomd",
        description="Convert PDF and HTML files to Markdown.",
    )
    parser.add_argument(
        "input", nargs="*",
        help="PDF/HTML file(s) or glob patterns to convert")
    parser.add_argument(
        "-o", "--output",
        help="Output Markdown path (single-file mode only)")
    parser.add_argument(
        "--outdir",
        help="Output directory for batch mode")
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable debug logging")
    parser.add_argument(
        "--qa", action="store_true",
        help="Run QA scoring instead of converting; prints a ranked report")
    parser.add_argument(
        "--qa-json",
        help="Write per-file QA metrics as JSON to this path (implies --qa)")
    parser.add_argument(
        "--workers", type=int, default=1,
        help="Parallel workers for --qa mode (default: 1)")
    parser.add_argument(
        "--timeout", type=int, default=120,
        help="Seconds with no progress before aborting remaining files (default: 120)")
    parser.add_argument(
        "--corpus", action="store_true",
        help="Corpus-run profile: LLM repair of L3/L4 tables (asked twice; repairs stay flagged and "
             "keep the first reading) and a second look (a confirmed mismatch names the rows to "
             "check), with a per-run token budget; needs Anthropic credentials, and runs on "
             "without them when they or the network are missing")
    parser.add_argument(
        "--llm-budget", type=int, default=None,
        help=f"Tokens (input + output) LLM repair may spend in this run "
             f"(default with --corpus: {CORPUS_LLM_BUDGET})")

    args = parser.parse_args()

    if args.corpus:
        # the corpus profile turns LLM repair on unless explicitly switched off
        # LLM repair of L3/L4 tables on (stays flagged, keeps the first reading): measured on
        # 24 papers +832.8 per-table points at 1x, +761.5 at 2x, +690.1 at 3x (wrong facts
        # weighted); the 7 tables it broke were all already L3 (REPORT.md, LLM second look)
        os.environ.setdefault("TOMD_LLM", "1")
        os.environ.setdefault("TOMD_LLM_BUDGET", str(CORPUS_LLM_BUDGET))
        # the second look at L3/L4 tables: a confirmed "no" names the rows to check; it never
        # changes a table's text or raises its level
        os.environ.setdefault("TOMD_LLM_CHECK", "1")
    if args.llm_budget is not None:
        os.environ["TOMD_LLM_BUDGET"] = str(args.llm_budget)

    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG,
                            format="%(name)s: %(message)s")

    if not args.input:
        parser.print_help()
        sys.exit(0)

    input_files = []
    for pattern in args.input:
        expanded = globmod.glob(pattern, recursive=True)
        if expanded:
            input_files.extend(expanded)
        else:
            input_files.append(pattern)
    input_files = list(dict.fromkeys(input_files))
    input_files = [Path(f) for f in input_files]

    if args.qa or args.qa_json:
        qa_files = [f for f in input_files
                    if f.suffix.lower() in _PDF_EXTENSIONS | _HTML_EXTENSIONS]
        if not qa_files:
            print("No PDF/HTML files found for QA scoring.", file=sys.stderr)
            sys.exit(1)
        from .lib.pdf.qa import run_qa_report
        json_path = Path(args.qa_json) if args.qa_json else None
        run_qa_report(qa_files, json_path=json_path, workers=args.workers,
                      timeout=args.timeout)
        sys.exit(0)

    if args.output and len(input_files) > 1:
        parser.error("-o/--output cannot be used with multiple input files")

    successes = []
    failures = []

    for input_file in input_files:
        if not input_file.exists():
            print(f"SKIP: {input_file} not found", file=sys.stderr)
            failures.append(input_file)
            continue

        if args.output and len(input_files) == 1:
            md_path = Path(args.output)
        elif args.outdir:
            md_path = Path(args.outdir) / input_file.with_suffix(".md").name
        else:
            md_path = input_file.with_suffix(".md")

        prompts_path = md_path.with_suffix(".prompts.md")
        summary_path = md_path.with_suffix(".summary.json")
        summary = None

        try:
            ext = input_file.suffix.lower()
            if ext in _HTML_EXTENSIONS:
                from .lib.html import convert_html
                md_text, prompts_text = convert_html(input_file)
            elif ext in _PDF_EXTENSIONS:
                from .lib.pdf import convert_pdf_with_summary
                md_text, prompts_text, summary = convert_pdf_with_summary(input_file)
            else:
                print(f"SKIP: {input_file} unsupported format", file=sys.stderr)
                failures.append(input_file)
                continue

            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(md_text, encoding="utf-8")
            if summary is not None:
                import json
                summary_path.write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")

            if prompts_text:
                prompts_path.write_text(prompts_text, encoding="utf-8")
                print(f"  ok: {input_file} -> {md_path} + {prompts_path}")
            else:
                if prompts_path.exists():
                    prompts_path.unlink()
                print(f"  ok: {input_file} -> {md_path}")

            successes.append(input_file)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                "FAIL: %s", input_file, exc_info=True)
            print(f"FAIL: {input_file} -- {e}", file=sys.stderr)
            failures.append(input_file)

    if len(input_files) > 1:
        print(f"\n{len(successes)} succeeded, {len(failures)} failed")
    if os.environ.get("TOMD_LLM") == "1":
        # the run's LLM repair status (no key or token is ever printed)
        from .lib.pdf import llmrepair
        rec = llmrepair.paper_record()
        spent = llmrepair._SPENT
        cap = os.environ.get("TOMD_LLM_BUDGET") or "none"
        print(f"LLM repair: {rec['status'].split(' (')[0]}; tokens spent this run {spent} (budget {cap})")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
