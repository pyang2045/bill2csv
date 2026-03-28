# CLAUDE.md

## Project Overview

bill2csv converts PDF bills to CSV format using Google's Gemini API. It extracts expense tables from PDFs and outputs structured CSV with Date, Description, Payee, Amount, and Category columns.

## Tech Stack

- Python 3.9+
- Google GenAI SDK (`google-genai`)
- pypdf for PDF handling
- macOS Keychain for API key storage (optional)

## Project Structure

- `bill2csv/` - Main package
  - `cli.py` - CLI argument parsing and entry point
  - `pdf_processor.py` - PDF upload and Gemini API interaction
  - `csv_cleaner.py` - CSV parsing and cleaning
  - `validators.py` - Data validation (dates, amounts, descriptions, payees, categories)
  - `output.py` - File output handling
  - `config.py` - Centralized configuration constants
  - `api_key.py` - API key retrieval (Keychain / env var)
  - `utils.py` - Shared utilities
- `tests/` - Unit tests
- `expense_categories.md` - Default category hierarchy
- `bill2csv_spec.md` - Product specification
- `DESIGN_DOCUMENT.md` - Technical architecture

## Common Commands

```bash
# Install in development mode
pip install -e .

# Run the tool
bill2csv <file.pdf>

# Run tests
python -m pytest tests/

# Run a specific test
python -m pytest tests/test_validators.py
```

## Key Conventions

- Model config lives in `bill2csv/config.py` (currently Gemini 3 Pro Preview)
- CSV date format: DD-MM-YYYY
- Categories use hierarchical format with ` > ` separator (e.g., "Food & Dining > Restaurants")
- Payee names preserve original language/script (Chinese, Japanese, etc.)
- Invalid rows go to a separate `.errors.csv` file rather than failing
