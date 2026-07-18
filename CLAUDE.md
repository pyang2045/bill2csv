# CLAUDE.md

## Project Overview

bill2csv converts PDF bills to CSV format. It extracts expense tables from PDFs and outputs structured CSV with Date, Description, Payee, Amount, and Category columns.

**The Python/Gemini CLI is ARCHIVED (2026-07-18)** — do not extend it. The active implementation is the Claude Code skill in `skill/`, deployed to `~/.claude/skills/bill2csv/`: Claude extracts transactions from the PDF visually, and `skill/scripts/validate.py` (stdlib-only) deterministically normalizes rows, writes the CSV + `.errors.csv`, and prints a summary. Design and as-built record: `docs/superpowers/specs/2026-03-28-bill2csv-skill-design.md`.

## Working on the Skill

- Edit `skill/` and re-copy to `~/.claude/skills/bill2csv/` — keep the two in sync
- Test end-to-end against the sample statements in the repo root (image-only PDFs with golden CSVs alongside); reconcile extracted totals against the statement's printed control totals
- The sample PDFs/CSVs contain personal data: they are local-only, excluded via `.gitignore` (`*.pdf`, `*.csv`), and must NEVER be committed, pushed, or uploaded anywhere
- `skill/categories.md` is the category taxonomy read by both Claude and `validate.py`

## Archived Python CLI (reference only)

- `bill2csv/` - Main package (cli.py, pdf_processor.py, csv_cleaner.py, validators.py, output.py, config.py, api_key.py, utils.py)
- `tests/` - Unit tests (`python -m pytest tests/`)
- `expense_categories.md` - CLI's category hierarchy (superseded by `skill/categories.md`)
- `bill2csv_spec.md` - Original product specification
- `DESIGN_DOCUMENT.md` - CLI technical architecture

## Key Conventions

- CSV date format: DD-MM-YYYY
- Amounts: signed, 2 decimal places; charges negative, credits positive
- Categories use hierarchical format with ` > ` separator (e.g., "Food & Dining > Restaurants")
- Payee names preserve original language/script (Chinese, Japanese, etc.)
- Invalid rows go to a separate `.errors.csv` file rather than failing
