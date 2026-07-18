---
name: bill2csv
description: Use when the user wants to convert a PDF bill, credit card statement, bank statement, or invoice into CSV transaction data — e.g. "convert this bill to CSV", "extract transactions from this statement PDF", "bill2csv".
---

# bill2csv

Convert a PDF bill to a transactions CSV. You extract and categorize; the bundled script guarantees formatting, writes the CSV, and isolates bad rows.

## Workflow

1. **Get the PDF path** — from the request, or ask. Verify the file exists.
2. **If the PDF is password-protected** (reading fails with an encryption error, or `pypdf`'s `is_encrypted` is true): ask the user for the password — never guess or brute-force. Then decrypt locally: `python3 <skill-dir>/scripts/unlock.py IN.pdf <stem>.unlocked.pdf PASSWORD` (uses pypdf or qpdf on this machine; nothing leaves it). Exit 2 means wrong password — ask again. Continue the workflow with the unlocked copy, and tell the user it was saved next to the original.
3. **Read the PDF with the Read tool.** Statements are often image-only (no text layer) — read every page visually; use `pages` ranges for PDFs over 10 pages. If a merchant name or digit is ambiguous, re-render that page at high DPI (e.g. PyMuPDF ≥300 dpi) and re-read before guessing.
4. **Extract every row of every transaction detail table** across all pages into a raw CSV at a temp path, header exactly: `Date,Description,Payee,Amount,Category` (rules below). Include zero-amount informational rows (e.g. installment remaining-principal lines). Ignore dashboards, charts, summaries, totals, ads, cover pages. If the bill has NO itemized rows, emit one row: bill date, issuer as Description and Payee, total due as a negative Amount, `Other > Uncategorized`.
5. **Validate:** `python3 <skill-dir>/scripts/validate.py RAW.csv OUT.csv` where OUT is next to the PDF, same basename, `.csv` extension. If OUT already exists, ask before overwriting. The script normalizes dates/amounts/descriptions, writes UTF-8 CSV plus `<stem>.errors.csv` for rejected rows, and prints a summary.
6. **Reconcile.** If the statement shows control totals (charges/credits subtotals), compare them to the script's `total_charges`/`total_credits`. On mismatch, re-read the pages and fix the raw CSV before delivering.
7. **Report:** row count, totals, category breakdown, any rejected/remapped rows (show them and offer to fix), and pages that couldn't be parsed. If no transactions were found, say so — don't write an empty CSV.

## Extraction rules

- **Date**: transaction date, not posting date. Any common format is fine — the script normalizes to DD-MM-YYYY. Infer the year from the statement period when rows omit it.
- **Description**: the transaction text as shown, one line.
- **Payee**: clean merchant name, **original script preserved** (星巴克咖啡, セブンイレブン…). Strip store numbers, transaction IDs, locations, and payment-channel prefixes (`APE`=Apple Pay, `連加`=LINE Pay, `TST*`, `SQ *`, `PAYPAL *`…). `AMZ*MKTP US*2Y4T85TN2` → `Amazon Marketplace`. Unknown → empty.
- **Amount**: charges/outflows **negative**, payments/credits/refunds **positive** — flip signs if the statement displays the opposite. Use the billed (converted) currency; if currencies are mixed, don't convert — note it in the report.
- **Category**: pick from `categories.md` in this skill directory only, as `Main > Sub`. When the purchased item is unknown, categorize by the merchant's type — marketplaces (Shopee, Taobao, Amazon…) and department stores are `Shopping`; a bare `Main` with no sub is fine. Reserve `Other > Uncategorized` for merchants you cannot identify at all.
- Unknown field → leave empty, never "N/A".
