# bill2csv

Convert PDF bills to CSV format using Google's Gemini 2.5 Flash API for intelligent extraction and categorization of financial transactions.

## Features

- Extracts expense detail tables from multi-page PDF bills
- Outputs structured CSV with Date, Description, Payee, Amount, and Category columns
- Automatic payee/merchant extraction from transaction descriptions
- **Multi-language support**: Preserves original language in payee names (Chinese, Japanese, etc.)
- **Smart date extraction**: Prioritizes transaction date over posting date
- Hierarchical categorization support (e.g., "Food & Dining > Restaurants")
- Customizable categories via external markdown file
- Secure API key management via macOS Keychain or environment variables
- Validates and normalizes data (dates, amounts, descriptions, payees, categories)
- Isolates invalid rows in separate error file
- Optional metadata generation
- Debug mode for troubleshooting API responses
- Automatic retry logic for API resilience

## Installation

### From Source (Development)
```bash
git clone https://github.com/yourusername/bill2csv.git
cd bill2csv
pip install -e .
```

### From PyPI (Coming Soon)
```bash
pip install bill2csv
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
bill2csv invoice.pdf --categories ~/my_categories.md

# Debug mode (saves raw API response)
bill2csv invoice.pdf --debug
```

## Output Format

### CSV Output
- **Date**: DD-MM-YYYY format (e.g., 13-06-2018)
  - Uses transaction date when available (when purchase occurred)
  - Falls back to posting date if transaction date not found
- **Description**: Cleaned transaction description with symbols replaced by spaces
  - Example: `WALMART#1234` → `WALMART 1234`
  - Example: `7-ELEVEN_STORE` → `7 ELEVEN STORE`
  - Quoted if contains commas
- **Payee**: Extracted merchant/vendor name from description
  - Preserves original language/script from description
  - Example: `WALMART#1234*STORE` → `Walmart`
  - Example: `星巴克咖啡#12345` → `星巴克咖啡` (Chinese)
  - Example: `セブンイレブン#1234` → `セブンイレブン` (Japanese)
  - Example: `AMZ*MKTP US*2Y4T85TN2` → `Amazon Marketplace`
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
- macOS (for Keychain support, optional)
- Gemini API key
- Dependencies: `google-genai>=0.1.0`, `pypdf>=3.17.0`

## Customizing Categories

The tool uses hierarchical categories defined in `expense_categories.md`. The file is searched in this order:

1. Custom file specified with `--categories` flag
2. Current working directory: `./expense_categories.md`
3. User config directory: `~/.bill2csv/expense_categories.md`
4. Falls back to built-in defaults if not found

### Category File Format

Categories are defined in markdown with indentation indicating hierarchy:

```markdown
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

## API Details

- **Model**: Gemini 2.5 Flash (gemini-2.5-flash)
- **Temperature**: 0.1 for consistent results
- **Max Tokens**: 32768 (supports large bills)
- **Retry Logic**: Automatic retry with exponential backoff for API errors

## Documentation

- **[Design Document](DESIGN_DOCUMENT.md)** - Technical architecture and implementation details
- **[Specification](bill2csv_spec.md)** - Original product requirements and specifications
- **[Categories Configuration](expense_categories.md)** - Default expense category hierarchy

## License

MIT