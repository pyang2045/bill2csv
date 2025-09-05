# Bill→CSV Converter -- POC CLI Design Specification

**Version:** 1.0\
**Date:** 2025-09-05

------------------------------------------------------------------------

## 1. Overview

This project provides a **command-line tool** (`bill2csv`) for macOS
that converts a **single multi-page PDF bill** into a CSV file. The
conversion uses the **Gemini 2.5 Flash API**, which directly ingests
PDFs and extracts **expense detail tables**.

**Output CSV schema:**

    Date,Description,Amount,Category

-   **Date:** `DD-MM-YYYY` (numeric, e.g., `13-06-2018`)\
-   **Description:** text, one line, quotes if commas present\
-   **Amount:** signed decimal with `.` separator
    -   Charges/expenses: negative\
    -   Payments/credits/refunds: positive
-   **Category:** Intelligent categorization of transactions
    -   Possible values: Food & Dining, Transportation, Shopping, Entertainment, 
        Bills & Utilities, Healthcare, Education, Travel, Fees & Charges, 
        Income/Credit, Other

------------------------------------------------------------------------

## 2. CLI Usage

### Command

    bill2csv <pdf_path> [options]

### Options

-   `--outdir <dir>` : output directory (default: same as input).\
-   `--meta` : also generate `<stem>.meta.json`.\
-   `--quiet` : suppress console logs (errors still shown).\
-   `--api-key-env <ENV_NAME>` : read API key from environment variable
    (default: `GEMINI_API_KEY`).\
-   `--keychain-service <svc> --keychain-account <acct>` : read API key
    securely from macOS Keychain.\
-   `--strict` : fail if any invalid row (instead of writing
    `.errors.csv`).\
-   `--version` : show tool version.\
-   `-h/--help` : show usage help.

------------------------------------------------------------------------

## 3. Security of API Key

### Retrieval priority

1.  **macOS Keychain (preferred)**
    -   Store key once:

        ``` bash
        security add-generic-password -a "<acct>" -s "<svc>" -w "<YOUR_KEY>" -U
        ```

    -   Retrieve at runtime:

        ``` bash
        security find-generic-password -a "<acct>" -s "<svc>" -w
        ```
2.  **Environment variable**
    -   Example:

        ``` bash
        export GEMINI_API_KEY="your_api_key"
        ```

**Do not**:\
- Hard-code keys in source.\
- Log keys.\
- Store in plain config files.

------------------------------------------------------------------------

## 4. Processing Workflow

1.  **Parse CLI args** and resolve API key (Keychain → env).\

2.  **Send PDF file** to Gemini 2.5 Flash with strict prompt.\

3.  **Receive CSV response**.\

4.  **Clean output**:

    -   Strip markdown/code fences.\
    -   Keep from first `Date,Description,Amount`.\

5.  **Validate rows**:

    -   Date → ensure `DD-MM-YYYY`; attempt parsing variants
        (`DD/MM/YYYY`, `YYYY-MM-DD`) and reformat.\
    -   Description → collapse whitespace; single line; quote if
        contains commas.\
    -   Amount → signed decimal, normalize minus `−` to `-`, remove
        thousands separators.\

6.  **Write outputs**:

    -   Always `<stem>.csv`.\
    -   If invalid rows exist: `<stem>.errors.csv`.\
    -   If `--meta`: `<stem>.meta.json`.\

7.  **Console log summary**:

        ✅ bill.pdf → bill.csv (15 rows, 1 error)

------------------------------------------------------------------------

## 5. Gemini Prompt (v3 -- Table Focused with Category)

Send PDF + this text:

    You read the attached multi-page bill PDF and extract ONLY the EXPENSE DETAIL TABLE(S).
    Ignore dashboards, charts/graphs, summaries, totals, advertisements, and cover pages.

    Output ONLY raw CSV with this exact header:
    Date,Description,Amount,Category

    Mapping rules:
    - Identify rows representing itemized expenses/charges or payments/credits.
    - Column mapping:
      * Date: posting date or transaction date for each row
      * Description: the row's textual label (e.g., merchant/item/service period)
      * Amount: numeric value for the row
      * Category: intelligently categorize based on the description and context

    Normalization:
    - Date: DD-MM-YYYY (numeric day-month-year, e.g., 13-06-2018)
    - Description: one line; if it contains commas, quote the field
    - Amount: signed decimal with '.' decimal separator; no thousands separators
      * Outflows/charges: NEGATIVE (e.g., -120.50)
      * Inflows/payments/credits/refunds: POSITIVE (e.g., 120.50)
    - Category: one of the following standard categories:
      * Food & Dining
      * Transportation
      * Shopping
      * Entertainment
      * Bills & Utilities
      * Healthcare
      * Education
      * Travel
      * Fees & Charges
      * Income/Credit
      * Other

    Scope:
    - Extract ALL rows from the expense detail table(s) across ALL pages.
    - If multiple detail tables exist, include them all (one row per transaction).
    - If the bill contains NO itemized rows, output ONE row using the total due as a charge (negative).

    Constraints:
    - If a field is unknown, leave it empty (no N/A).
    - Output only CSV text. No explanations, no markdown, no code fences, no extra columns.

    Header example:
    Date,Description,Amount,Category

------------------------------------------------------------------------

## 6. Output Files

-   **CSV**: `<stem>.csv` -- cleaned & validated rows.\

-   **Errors**: `<stem>.errors.csv` -- only if invalid rows exist.

        row,reason,raw
        3,Invalid date format,"06/2018,Rent,-500.00"

-   **Metadata** (optional): `<stem>.meta.json`

    ``` json
    {
      "source_file": "bill.pdf",
      "model": "gemini-2.5-flash",
      "timestamp": "2025-09-05T14:25:00+08:00",
      "pages": 4,
      "rows": 15,
      "errors": 1
    }
    ```

------------------------------------------------------------------------

## 7. Validation Rules

-   **Header**: exactly `Date,Description,Amount,Category`.\
-   **Date**: must be convertible to `DD-MM-YYYY`.\
-   **Description**: non-empty, single line, quoted if contains commas.\
-   **Amount**: regex `^-?\d+(\.\d+)?$`, with sign convention applied.
-   **Category**: must be one of the predefined categories or "Other".

------------------------------------------------------------------------

## 8. Logging & Privacy

-   Console log summary (rows/errors).\
-   Optional `run.log` (filename, duration, counts).\
-   Never log bill text or API responses.

------------------------------------------------------------------------

## 9. Dependencies

-   Python 3.9+\
-   `google-generativeai` SDK\
-   Standard libraries: `argparse`, `csv`, `json`, `datetime`, `re`,
    `subprocess`

------------------------------------------------------------------------

## 10. Acceptance Criteria

-   Running `bill2csv sample.pdf` produces `sample.csv` with correct
    header and fields in `DD-MM-YYYY`.\
-   Invalid rows isolated in `.errors.csv`.\
-   API key resolved securely.\
-   Works on multi-page PDFs with expense tables.\
-   Logs show only operational summaries.
