# bill2csv

Convert PDF bills to CSV format using Google's Gemini 2.5 Flash API.

## Features

- Extracts expense detail tables from multi-page PDF bills
- Outputs structured CSV with Date, Description, Amount, and Category columns
- Intelligent categorization of transactions (Food & Dining, Transportation, Shopping, etc.)
- Secure API key management via macOS Keychain or environment variables
- Validates and normalizes data (dates, amounts, descriptions, categories)
- Isolates invalid rows in separate error file
- Optional metadata generation

## Installation

```bash
pip install -e .
```

## Setup

### API Key Configuration

1. **Using macOS Keychain (Recommended)**:
```bash
security add-generic-password -a "bill2csv" -s "gemini-api" -w "YOUR_API_KEY" -U
```

2. **Using Environment Variable**:
```bash
export GEMINI_API_KEY="your_api_key"
```

## Usage

### Basic Usage
```bash
bill2csv invoice.pdf
```

### With Options
```bash
# Specify output directory
bill2csv invoice.pdf --outdir ./output

# Generate metadata file
bill2csv invoice.pdf --meta

# Use specific Keychain credentials
bill2csv invoice.pdf --keychain-service gemini-api --keychain-account bill2csv

# Strict mode (fail on any invalid rows)
bill2csv invoice.pdf --strict

# Quiet mode (suppress logs)
bill2csv invoice.pdf --quiet
```

## Output Format

### CSV Output
- **Date**: DD-MM-YYYY format (e.g., 13-06-2018)
- **Description**: Transaction description (quoted if contains commas)
- **Amount**: Decimal with sign (negative for charges, positive for credits)
- **Category**: Automatically categorized (e.g., Food & Dining, Transportation, Shopping, etc.)

### Files Generated
- `<filename>.csv` - Main output with valid rows
- `<filename>.errors.csv` - Invalid rows (if any)
- `<filename>.meta.json` - Metadata (if --meta flag used)

## Requirements

- Python 3.9+
- macOS (for Keychain support)
- Gemini API key

## License

MIT