# Claude Development Guide for bill2csv

## Project Overview
This is a command-line tool for macOS that converts PDF bills into CSV format using the Gemini 2.5 Flash API. The tool extracts expense detail tables from multi-page PDFs and outputs structured CSV data.

## Key Technical Details

### Technology Stack
- Python 3.9+
- google-generativeai SDK
- Standard libraries: argparse, csv, json, datetime, re, subprocess

### CSV Output Format
- Header: `Date,Description,Amount,Category`
- Date format: DD-MM-YYYY (e.g., 13-06-2018)
- Amount: Negative for charges/expenses, positive for payments/credits
- Description: Quoted if contains commas
- Category: Intelligent categorization (Food & Dining, Transportation, Shopping, etc.)

### Core Components to Implement
1. CLI argument parser with options for output directory, metadata, API key handling
2. Secure API key retrieval (macOS Keychain preferred, environment variable fallback)
3. PDF processing via Gemini API
4. CSV validation and cleaning logic
5. Error handling and logging

## Development Guidelines

### Security Requirements
- NEVER hard-code API keys in source code
- Use macOS Keychain as primary storage method
- Fall back to environment variables (default: GEMINI_API_KEY)
- Never log API keys or bill content

### File Output Structure
- Main CSV: `<stem>.csv`
- Error rows: `<stem>.errors.csv` (only if validation failures)
- Metadata: `<stem>.meta.json` (optional, with --meta flag)

### Validation Rules
1. Date must be convertible to DD-MM-YYYY format
2. Description must be single line, non-empty
3. Amount must match regex: `^-?\d+(\.\d+)?$`
4. Invalid rows go to separate errors file unless --strict mode

### Testing Approach
- Test with sample multi-page PDF bills
- Verify CSV output format compliance
- Test API key retrieval methods
- Validate error handling for malformed data
- Check file output locations with different --outdir values

## Common Commands

### Setup
```bash
# Install dependencies
pip install google-generativeai

# Store API key in macOS Keychain
security add-generic-password -a "bill2csv" -s "gemini-api" -w "YOUR_API_KEY" -U
```

### Usage Examples
```bash
# Basic conversion
bill2csv sample.pdf

# With custom output directory
bill2csv sample.pdf --outdir ./output

# With metadata generation
bill2csv sample.pdf --meta

# Using environment variable for API key
export GEMINI_API_KEY="your_key"
bill2csv sample.pdf

# Using Keychain credentials
bill2csv sample.pdf --keychain-service gemini-api --keychain-account bill2csv
```

## Important Implementation Notes
- The Gemini prompt (v2) is specifically tuned for table extraction - maintain exact wording
- Clean API responses by stripping markdown/code fences
- Normalize various date formats to DD-MM-YYYY
- Handle Unicode minus signs (−) by converting to ASCII minus (-)
- Remove thousands separators from amounts
- Console output should show summary: `✅ bill.pdf → bill.csv (15 rows, 1 error)`

## Error Handling
- Invalid rows should not stop processing (unless --strict)
- Create `.errors.csv` with format: `row,reason,raw`
- Always show errors to console even in --quiet mode
- Exit with non-zero code if critical failures

## Privacy Considerations
- Never log actual bill content or transaction details
- Log only operational metadata (counts, durations, filenames)
- Optional run.log should contain only summary information