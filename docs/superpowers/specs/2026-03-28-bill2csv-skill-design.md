# bill2csv Skill Design

> **Status: implemented 2026-07-18** as a *hybrid* skill (markdown + bundled stdlib
> validator script), deployed at `~/.claude/skills/bill2csv/` and mirrored in
> [`skill/`](../../../skill/) in this repo. The hybrid variant was chosen over the
> pure-markdown design originally described here to keep the deterministic
> formatting guarantees and `.errors.csv` isolation of the Python CLI, which this
> skill replaces (the CLI is now archived). Sections below are updated to as-built.

## Summary

A Claude Code skill that converts PDF bills to CSV format using Claude as the extraction engine. No external API dependencies (Gemini, etc.). The skill is conversational: it asks for a PDF path, reads the PDF, extracts transactions, then runs a bundled Python (stdlib-only) script that validates/normalizes the rows, writes the CSV plus an `.errors.csv` for rejected rows, and prints a summary.

## Target Users

Other developers with Claude Code who want to convert PDF bills to CSV without setting up a Gemini API key or installing the bill2csv Python package.

## Approach

Hybrid skill — extraction judgment lives in markdown, formatting guarantees live in code:

- **Claude** (per `SKILL.md`): reads the PDF visually (bills are often image-only, no text layer), extracts transaction rows, cleans payees, assigns categories, and reconciles totals against the statement's printed control totals.
- **`scripts/validate.py`** (Python 3, stdlib only, ~150 lines ported from the CLI's `validators.py`): deterministically normalizes dates (6 input formats → DD-MM-YYYY) and amounts (Unicode minus, parentheses, currency symbols, thousands separators → signed 2-decimal), scrubs description symbols, resolves categories against `categories.md` (bare sub-names map to their hierarchy, unknowns → `Other > Uncategorized`), writes the UTF-8 CSV with correct quoting, isolates rejected rows into `<stem>.errors.csv` (`row,reason,raw`), and prints the summary.

## Skill Location

```
~/.claude/skills/bill2csv/
  SKILL.md              # workflow + extraction rules
  categories.md         # category taxonomy (read by Claude and the script)
  scripts/validate.py   # deterministic validation / output / summary
```

Available in any Claude Code session regardless of working directory. Source is version-controlled in this repo under `skill/`.

## Conversation Flow

1. **Ask for PDF path** — prompt the user for the file path
2. **Read PDF** — use the Read tool to read every page visually (statements are often image-only); re-render ambiguous pages at high DPI (≥300) rather than guessing
3. **Extract transactions** — Claude analyzes the bill content and extracts all expense detail rows (including zero-amount informational rows) to a raw temp CSV
4. **Validate & normalize** — run `scripts/validate.py RAW.csv OUT.csv`; it writes the output CSV and `.errors.csv`, and prints the summary
5. **Reconcile** — compare the script's charge/credit totals against the statement's printed control totals; on mismatch, re-read and fix before delivering
6. **Show summary** — relay row count, total charges, total credits, category breakdown, rejected/remapped rows

If ambiguous or unreadable rows are found, flag them in conversation and ask the user how to proceed.

## CSV Format

### Columns

The CSV must include a header row as the first line, followed by data rows. Column order is fixed:

| # | Column | Description |
|---|--------|-------------|
| 1 | Date | DD-MM-YYYY format, transaction date preferred over posting date |
| 2 | Description | Cleaned text, symbols replaced with spaces, quoted if contains commas |
| 3 | Payee | Merchant/vendor name extracted from description, original language preserved |
| 4 | Amount | Signed decimal — negative for charges, positive for credits/payments |
| 5 | Category | Hierarchical with ` > ` separator from baked-in category list |

Header row: `Date,Description,Payee,Amount,Category`

Encoding: UTF-8 (required for CJK character support).

### Normalization Rules

**Date:**
- Format: DD-MM-YYYY (e.g., 13-06-2018)
- Prefer transaction date (when purchase occurred) over posting date
- Accept various input formats (DD/MM/YYYY, YYYY-MM-DD, etc.)

**Description:**
- Replace symbols (`*`, `#`, `@`, `&`, `/`, `\`, `|`, `<`, `>`, `~`, `` ` ``, `^`, `_`, `+`, `=`, `[`, `]`, `{`, `}`) with spaces
- Replace hyphens and dashes (`-`, `–`, `—`) with spaces
- Collapse multiple spaces into one
- Quote with double quotes if contains commas
- Example: `WALMART#1234*STORE` becomes `WALMART 1234 STORE`
- Example: `7-ELEVEN_STORE` becomes `7 ELEVEN STORE`

**Payee:**
- Extract clean merchant/vendor name from description
- Preserve original language/script (Chinese, Japanese, etc.)
- Remove store numbers, transaction codes, extra details
- Examples:
  - `WALMART#1234*STORE` -> `Walmart`
  - `星巴克咖啡#12345` -> `星巴克咖啡`
  - `AMZ*MKTP US*2Y4T85TN2` -> `Amazon Marketplace`
- Quote if contains commas
- If no merchant can be identified, use an empty string (`""`)

**Amount:**
- Signed decimal with `.` separator, no thousands separators
- Always use exactly 2 decimal places (e.g., `120.00`, not `120`)
- Charges/outflows: negative (e.g., `-120.50`)
- Credits/payments/refunds: positive (e.g., `120.50`)
- Remove currency symbols, handle Unicode minus signs

**Category:**
- Use ONLY categories from the baked-in list
- Hierarchical format: `Main > Sub` (e.g., `Food & Dining > Restaurants`)
- Default to `Other > Uncategorized` if no match

### Scope Rules

- Extract ALL rows from expense detail tables across ALL pages
- Ignore dashboards, charts/graphs, summaries, totals, advertisements, cover pages
- If multiple detail tables exist, include all (one row per transaction)
- If no itemized rows, output one row: Date = bill date, Description = bill issuer name, Payee = bill issuer, Amount = total due (negative), Category = `Other > Uncategorized`

## Output

### CSV File

Written to same directory as input PDF, same basename with `.csv` extension.

Example: `eStatement_202602.pdf` -> `eStatement_202602.csv`

### Conversation Summary

After writing the CSV, display:
- Total rows extracted
- Total charges (sum of negative amounts)
- Total credits (sum of positive amounts)
- Category breakdown (count per top-level category)

## Categories (Baked In)

The full category hierarchy embedded in the skill. This is an intentionally cleaned-up version of the repo's `expense_categories.md` — duplicates removed, flat items grouped under parents. The Python CLI continues to use the original file; the skill uses this self-contained list.

```
- Food & Dining
  - Restaurants
  - Groceries
  - Coffee Shops
  - Fast Food
  - Delivery & Takeout
- Transportation
  - Public Transit
  - Rideshare & Taxi
  - Gas & Fuel
  - Parking & Tolls
  - Vehicle Maintenance
  - Car Insurance
- Shopping
  - Clothing & Accessories
  - Electronics
  - Home & Garden
  - Books & Media
  - Gifts
- Entertainment
  - Movies & Shows
  - Events & Concerts
  - Sports & Recreation
  - Gaming
  - Streaming Services
- Health & Wellness
  - Medical Services
  - Pharmacy
  - Gym & Fitness
  - Personal Care
  - Health Insurance
- Housing
  - Rent
  - Mortgage
  - Property Tax
  - HOA Fees
- Utilities
  - Electricity
  - Gas
  - Water & Sewer
  - Internet
  - Phone
  - Cable & TV
- Maintenance
  - Repairs
  - Cleaning Services
  - Lawn & Garden
- Banking
  - Service Fees
  - ATM Fees
  - Overdraft Fees
- Credit Cards
  - Interest Charges
  - Annual Fees
  - Late Fees
- Investments
  - Brokerage Fees
  - Advisory Fees
- Insurance
  - Life Insurance
  - Home Insurance
  - Other Insurance
- Travel
  - Flights
  - Hotels
  - Vacation Rentals
  - Hostels
  - Car Rental
  - Local Transport
  - Tours & Attractions
- Office
  - Supplies
  - Equipment
  - Software
- Professional
  - Legal Services
  - Accounting
  - Consulting
- Marketing
  - Advertising
  - Promotions
  - Events
- Education
  - Tuition
  - Books & Supplies
  - Courses & Training
  - Student Loans
- Income
  - Salary
  - Freelance
  - Refunds
  - Credits
  - Interest
  - Dividends
  - Other Income
- Other
  - Uncategorized
  - Cash Withdrawal
  - Transfers
  - Adjustments
```

## Error Handling

- **Password-protected PDF**: ask the user for the password (never guess or brute-force), decrypt locally with `scripts/unlock.py` (pypdf, falling back to qpdf; no network involved), save the copy as `<stem>.unlocked.pdf` next to the original, and continue with it. Wrong password (exit 2) → ask again.
- **Rows failing validation**: written to `<stem>.errors.csv` (`row,reason,raw`) by the script; Claude shows them and offers to fix
- **Ambiguous rows**: Flag in conversation, ask user how to proceed
- **Unreadable pages**: Inform user which pages couldn't be parsed
- **No transactions found**: Tell user explicitly rather than writing empty CSV
- **File not found**: Ask user to verify the path
- **File already exists**: Ask user before overwriting an existing CSV file
- **Multi-currency**: Extract amounts as-is in whatever currency appears; do not convert. Note currency in the summary if mixed currencies detected.

## Verification (as implemented)

Tested TDD-style against real image-only credit-card statements (kept locally
only — statements and their golden CSVs contain personal data and are excluded
from git via `.gitignore`): a clean-room agent following only the skill
reproduced the golden row set produced by the Gemini pipeline, reconciled
exactly against all three statement control totals, rejected zero rows, and
matched the golden category distribution (1 uncategorized row). `validate.py` is additionally unit-tested against crafted
edge cases (bad dates, `(99.50)`/`−8`/`87,792` amounts, comma-bearing CJK payees,
unknown categories).

## Non-Goals

- No metadata/meta.json generation
- No Gemini/external API dependency
- No *installed* Python package dependency (the bundled script is stdlib-only, run directly)
- No custom categories file support (categories are baked into the skill directory)
