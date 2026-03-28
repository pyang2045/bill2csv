# bill2csv Skill Design

## Summary

A Claude Code skill that converts PDF bills to CSV format using Claude as the extraction engine. No external API dependencies (Gemini, etc.). The skill is conversational: it asks for a PDF path, reads the PDF, extracts transactions, validates data, writes a CSV file, and shows a summary.

## Target Users

Other developers with Claude Code who want to convert PDF bills to CSV without setting up a Gemini API key or installing the bill2csv Python package.

## Approach

Pure markdown skill — all extraction logic, validation rules, and category definitions are embedded in the skill instructions. Claude reads the PDF directly via the Read tool and applies the rules to produce structured CSV output.

## Skill Location

`~/.claude/skills/bill2csv/SKILL.md`

Available in any Claude Code session regardless of working directory.

## Conversation Flow

1. **Ask for PDF path** — prompt the user for the file path
2. **Read PDF** — use the Read tool to read the PDF contents
3. **Extract transactions** — Claude analyzes the bill content and extracts expense detail rows
4. **Validate & normalize** — apply normalization rules to each row
5. **Write CSV** — write to same directory as PDF, same basename with `.csv` extension
6. **Show summary** — display row count, total charges, total credits, category breakdown

If ambiguous or unreadable rows are found, flag them in conversation and ask the user how to proceed.

## CSV Format

### Columns

| Column | Description |
|--------|-------------|
| Date | DD-MM-YYYY format, transaction date preferred over posting date |
| Description | Cleaned text, symbols replaced with spaces, quoted if contains commas |
| Payee | Merchant/vendor name extracted from description, original language preserved |
| Amount | Signed decimal — negative for charges, positive for credits/payments |
| Category | Hierarchical with ` > ` separator from baked-in category list |

### Normalization Rules

**Date:**
- Format: DD-MM-YYYY (e.g., 13-06-2018)
- Prefer transaction date (when purchase occurred) over posting date
- Accept various input formats (DD/MM/YYYY, YYYY-MM-DD, etc.)

**Description:**
- Replace symbols (`*`, `#`, `@`, `&`, `/`, `\`, `|`, `<`, `>`, `~`, `` ` ``, `^`, `_`, `+`, `=`, `[`, `]`, `{`, `}`) with spaces
- Collapse multiple spaces into one
- Quote with double quotes if contains commas
- Example: `WALMART#1234*STORE` becomes `WALMART 1234 STORE`

**Payee:**
- Extract clean merchant/vendor name from description
- Preserve original language/script (Chinese, Japanese, etc.)
- Remove store numbers, transaction codes, extra details
- Examples:
  - `WALMART#1234*STORE` -> `Walmart`
  - `星巴克咖啡#12345` -> `星巴克咖啡`
  - `AMZ*MKTP US*2Y4T85TN2` -> `Amazon Marketplace`
- Quote if contains commas

**Amount:**
- Signed decimal with `.` separator, no thousands separators
- Charges/outflows: negative (e.g., `-120.50`)
- Credits/payments/refunds: positive (e.g., `120.50`)
- Remove currency symbols, handle Unicode minus signs

**Category:**
- Use ONLY categories from the baked-in list
- Hierarchical format: `Main > Sub` (e.g., `Food & Dining > Restaurants`)
- Default to `Uncategorized` if no match

### Scope Rules

- Extract ALL rows from expense detail tables across ALL pages
- Ignore dashboards, charts/graphs, summaries, totals, advertisements, cover pages
- If multiple detail tables exist, include all (one row per transaction)
- If no itemized rows, output one row using total due as a negative charge

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

The full category hierarchy embedded in the skill:

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
- Transportation (Travel)
  - Flights
  - Hotels
  - Car Rental
  - Local Transport
- Accommodation
  - Hotels
  - Vacation Rentals
  - Hostels
- Activities
  - Tours
  - Attractions
  - Dining
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
- Tuition
- Books & Supplies
- Courses & Training
- Student Loans
- Salary
- Freelance
- Refunds
- Credits
- Interest
- Dividends
- Other Income
- Uncategorized
- Cash Withdrawal
- Transfers
- Adjustments
```

## Error Handling

- **Ambiguous rows**: Flag in conversation, ask user how to proceed
- **Unreadable pages**: Inform user which pages couldn't be parsed
- **No transactions found**: Tell user explicitly rather than writing empty CSV
- **File not found**: Ask user to verify the path

## Non-Goals

- No metadata/meta.json generation
- No separate errors.csv file (errors handled conversationally)
- No Gemini/external API dependency
- No Python package dependency
- No custom categories file support (categories are baked in)
