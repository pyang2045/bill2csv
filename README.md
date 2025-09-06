# bill2csv

Convert PDF bills to CSV format using Google's Gemini 2.5 Flash API.

## Features

- Extracts expense detail tables from multi-page PDF bills
- Outputs structured CSV with Date, Description, Payee, Amount, and Category columns
- Automatic payee/merchant extraction from transaction descriptions
- Hierarchical categorization support (e.g., "Food & Dining > Restaurants")
- Customizable categories via external markdown file
- Secure API key management via macOS Keychain or environment variables
- Validates and normalizes data (dates, amounts, descriptions, payees, categories)
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

# Use custom categories file
bill2csv invoice.pdf --categories-file ~/my_categories.md
```

## Output Format

### CSV Output
- **Date**: DD-MM-YYYY format (e.g., 13-06-2018)
- **Description**: Cleaned transaction description with symbols replaced by spaces
  - Example: `WALMART#1234` → `WALMART 1234`
  - Example: `7-ELEVEN_STORE` → `7 ELEVEN STORE`
  - Quoted if contains commas
- **Payee**: Extracted merchant/vendor name from description
  - Example: `WALMART#1234*STORE` → `Walmart`
  - Example: `AMZ*MKTP US*2Y4T85TN2` → `Amazon`
  - Example: `STARBUCKS STORE #12345` → `Starbucks`
- **Amount**: Decimal with sign (negative for charges, positive for credits)
- **Category**: Hierarchical categories with > separator
  - Main level: `Food & Dining`, `Transportation`, `Shopping`
  - Sub-categories: `Food & Dining > Restaurants`, `Transportation > Gas & Fuel`

### Files Generated
- `<filename>.csv` - Main output with valid rows
- `<filename>.errors.csv` - Invalid rows (if any)
- `<filename>.meta.json` - Metadata (if --meta flag used)

## Requirements

- Python 3.9+
- macOS (for Keychain support)
- Gemini API key

## Customizing Categories

The tool uses hierarchical categories defined in `expense_categories.md`. You can:

1. Edit the default file in the project directory
2. Create your own categories file and specify it with `--categories-file`
3. Place a custom file at `~/.bill2csv/expense_categories.md`

### Category File Format

Categories are defined in markdown with indentation indicating hierarchy:

```markdown
## Personal Expenses
- Food & Dining
  - Restaurants
  - Groceries
  - Coffee Shops
- Transportation
  - Gas & Fuel
  - Public Transit
  - Rideshare & Taxi
```

In CSV output, sub-categories appear as: `Food & Dining > Restaurants`

## Documentation

- **[Design Document](DESIGN_DOCUMENT.md)** - Technical architecture and implementation details
- **[Specification](bill2csv_spec.md)** - Original product requirements and specifications
- **[Categories Configuration](expense_categories.md)** - Default expense category hierarchy

## License

MIT