# bill2csv Design Document

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [System Components](#system-components)
4. [Data Flow](#data-flow)
5. [Module Specifications](#module-specifications)
6. [Data Schemas](#data-schemas)
7. [Security Considerations](#security-considerations)
8. [Error Handling](#error-handling)
9. [Performance Considerations](#performance-considerations)
10. [Future Enhancements](#future-enhancements)

## Overview

### Purpose
bill2csv is a command-line tool that converts PDF bills into structured CSV format using Google's Gemini 2.5 Flash API. It extracts expense detail tables from multi-page PDFs and produces normalized, categorized transaction data.

### Goals
- **Accuracy**: Reliable extraction of transaction data from various bill formats
- **Usability**: Simple CLI interface with sensible defaults
- **Security**: Secure API key management without exposing credentials
- **Flexibility**: Customizable categories and output options
- **Maintainability**: Clean, modular architecture for easy updates

### Non-Goals
- Web interface or GUI
- Direct database integration
- Real-time processing
- OCR implementation (delegated to Gemini API)

## Architecture

### High-Level Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   PDF File  │────▶│   bill2csv   │────▶│  CSV Output │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Gemini API  │
                    └──────────────┘
```

### Component Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      CLI Layer                           │
│                    (cli.py, __main__.py)                 │
└──────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────────────────────────────────────┐
│                   Core Processing Layer                   │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  API Key    │  │ PDF Processor│  │ CSV Cleaner  │   │
│  │  Manager    │  │              │  │              │   │
│  └─────────────┘  └──────────────┘  └──────────────┘   │
└──────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────────────────────────────────────┐
│                   Validation Layer                        │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐     │
│  │   Date   │ │  Amount  │ │ Payee  │ │ Category │     │
│  │Validator │ │Validator │ │Validator│ │Validator │     │
│  └──────────┘ └──────────┘ └────────┘ └──────────┘     │
└──────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────────────────────────────────────┐
│                     Output Layer                          │
│           (OutputManager, ConsoleLogger)                  │
└──────────────────────────────────────────────────────────┘
```

## System Components

### Core Modules

#### 1. CLI Module (`cli.py`)
**Purpose**: Parse and validate command-line arguments

**Responsibilities**:
- Argument parsing with argparse
- Path validation
- Option handling (--outdir, --meta, --quiet, etc.)
- Input validation

**Key Functions**:
```python
parse_args(args=None) -> Namespace
```

#### 2. API Key Manager (`api_key.py`)
**Purpose**: Secure API key retrieval

**Responsibilities**:
- macOS Keychain integration
- Environment variable fallback
- Secure error handling without key exposure

**Priority Order**:
1. macOS Keychain (if specified)
2. Environment variable
3. Error if not found

#### 3. PDF Processor (`pdf_processor.py`)
**Purpose**: Interface with Gemini API for PDF processing

**Responsibilities**:
- PDF upload to Gemini
- Prompt management
- Response retrieval
- Error handling

**Key Configuration**:
- Model: `gemini-2.5-flash`
- Temperature: 0.1 (for consistency)
- Max tokens: 32768 (to handle larger bills)

#### 4. CSV Cleaner (`csv_cleaner.py`)
**Purpose**: Clean and parse API responses

**Responsibilities**:
- Remove markdown/code fences
- Extract CSV content
- Handle various header formats
- Parse into structured data

#### 5. Validators (`validators.py`)
**Purpose**: Normalize and validate data fields

**Components**:
- **DateValidator**: DD-MM-YYYY normalization
- **AmountValidator**: Decimal formatting, sign handling
- **DescriptionValidator**: Symbol replacement, quoting
- **PayeeValidator**: Merchant name extraction
- **CategoryValidator**: Hierarchical category validation
- **RowValidator**: Complete row validation

#### 6. Output Manager (`output.py`)
**Purpose**: File generation and writing

**Outputs**:
- Main CSV file (`.csv`)
- Error file (`.errors.csv`)
- Metadata file (`.meta.json`)

## Data Flow

### Processing Pipeline

```
1. Input Stage
   PDF File → Argument Parsing → API Key Retrieval

2. Processing Stage
   PDF → Gemini API → Raw CSV Response

3. Cleaning Stage
   Raw Response → Strip Markdown → Extract CSV → Parse Rows

4. Validation Stage
   For each row:
   ├── Validate Date → Normalize to DD-MM-YYYY
   ├── Validate Description → Clean symbols
   ├── Validate Payee → Extract merchant name
   ├── Validate Amount → Normalize decimal
   └── Validate Category → Apply hierarchy

5. Output Stage
   Valid Rows → CSV File
   Invalid Rows → Error File
   Statistics → Metadata File (optional)
```

### Error Flow

```
Invalid Rows → Error Collection → .errors.csv
                     │
                     └── Format: row,reason,raw_data
```

## Data Schemas

### Input Schema (Gemini Prompt)
```
Date,Description,Payee,Amount,Category
```

### Output CSV Schema
```csv
Date,Description,Payee,Amount,Category
DD-MM-YYYY,Text,Merchant,±Decimal,Category > Subcategory
```

### Field Specifications

#### Date
- **Format**: DD-MM-YYYY
- **Example**: 13-06-2018
- **Source Priority**: Transaction Date preferred (when purchase occurred), Posting Date as fallback
- **Validation**: Multiple format support, normalized output

#### Description
- **Format**: Cleaned text, symbols replaced with spaces
- **Example**: "WALMART 1234 STORE"
- **Processing**: Remove #, *, @, &, /, \, etc.

#### Payee
- **Format**: Merchant name preserving original language
- **Examples**: 
  - "Walmart" (English)
  - "星巴克咖啡" (Chinese - Starbucks)
  - "セブンイレブン" (Japanese - 7-Eleven)
- **Processing**: 
  - Preserve original language/script from description
  - Remove store numbers, transaction IDs
  - Keep native text for non-English merchants

#### Amount
- **Format**: Signed decimal
- **Examples**: -120.50 (charge), 50.00 (credit)
- **Sign Convention**: 
  - Negative: Charges/expenses
  - Positive: Credits/payments

#### Category
- **Format**: Hierarchical with ">" separator
- **Examples**: 
  - "Food & Dining"
  - "Food & Dining > Restaurants"
- **Source**: expense_categories.md file

### Error CSV Schema
```csv
row,reason,raw
3,"Date error: Invalid format","06/2018,Rent,-500.00"
```

### Metadata JSON Schema
```json
{
  "source_file": "bill.pdf",
  "model": "gemini-2.0-flash-exp",
  "timestamp": "2025-09-05T14:25:00+08:00",
  "pages": 4,
  "rows": 15,
  "errors": 1
}
```

## Security Considerations

### API Key Management

#### Storage Options
1. **macOS Keychain (Preferred)**
   ```bash
   security add-generic-password -a "bill2csv" -s "gemini-api" -w "KEY" -U
   ```

2. **Environment Variable**
   ```bash
   export GEMINI_API_KEY="your_key"
   ```

#### Security Principles
- Never log API keys
- Never store in source code
- Clear error messages without key exposure
- Secure subprocess calls for Keychain

### Data Privacy
- No logging of bill content
- No transmission of data except to Gemini API
- Local processing only
- Temporary file cleanup

## Error Handling

### Error Categories

#### 1. Input Errors
- Missing PDF file
- Invalid file format
- Unreadable file

#### 2. API Errors
- Authentication failure
- Rate limiting
- Network issues
- Processing failures

#### 3. Validation Errors
- Invalid date formats
- Malformed amounts
- Missing required fields

#### 4. System Errors
- Permission issues
- Disk space
- Memory constraints

### Error Strategies

#### Graceful Degradation
- Invalid rows isolated, valid rows processed
- Partial success allowed (unless --strict)
- Clear error reporting

#### Recovery Mechanisms
- **API retry logic**:
  - Max retries: 3 attempts
  - Initial delay: 2 seconds
  - Exponential backoff: 2x multiplier (up to 32 seconds)
  - Jitter: Random 0-1 second added to prevent thundering herd
  - Retryable errors: 503 (Service Unavailable), 429 (Rate Limit), 500 (Internal Error), 502 (Bad Gateway)
- Alternative date format parsing
- Fallback category assignment

## Performance Considerations

### Optimization Strategies

#### Memory Management
- Stream processing for large files
- Efficient regex compilation
- Minimal data duplication

#### API Efficiency
- Single API call per PDF
- Optimized prompt for accuracy
- Appropriate temperature setting

#### File I/O
- Buffered writing
- Atomic file operations
- Cleanup of temporary files

### Scalability Limits
- Single PDF processing (by design)
- API token limits (32768 for gemini-2.5-flash)
- Local file system constraints

## Future Enhancements

### Planned Features

#### Short-term
- Batch processing support
- Configuration file support
- Additional output formats (JSON, Excel)
- Custom prompt templates

#### Medium-term
- Web interface
- Database integration
- Multi-language support
- Advanced categorization rules

#### Long-term
- Machine learning for categorization
- Receipt image support
- Bank statement integration
- Automated reconciliation

### Extension Points

#### Plugin Architecture
- Custom validators
- Output format plugins
- Category providers
- API backends

#### Integration Opportunities
- Accounting software APIs
- Cloud storage services
- Expense management systems
- Business intelligence tools

## Testing Strategy

### Unit Tests
- Individual validator functions
- CSV parsing logic
- API key retrieval
- Symbol cleaning

### Integration Tests
- End-to-end processing
- Error handling paths
- File generation
- API interaction

### Test Coverage Areas
- Date format variations
- Amount normalization
- Payee extraction
- Category hierarchy
- Error isolation

## Deployment

### Installation Methods
```bash
# Development
pip install -e .

# Production
pip install bill2csv

# From source
python setup.py install
```

### Dependencies
- Python 3.9+
- google-generativeai
- pypdf
- Standard library modules

### Platform Support
- Primary: macOS (Keychain support)
- Secondary: Linux/Windows (ENV variables only)

## Maintenance

### Code Organization
```
bill2csv/
├── bill2csv/          # Main package
│   ├── __init__.py    # Package initialization
│   ├── __main__.py    # Entry point
│   ├── cli.py         # CLI handling
│   ├── api_key.py     # Security
│   ├── pdf_processor.py # API interface
│   ├── csv_cleaner.py # Data cleaning
│   ├── validators.py  # Validation logic
│   ├── output.py      # File generation
│   └── utils.py       # Utilities
├── tests/             # Test suite
├── expense_categories.md # Category definitions
└── setup.py           # Package configuration
```

### Version Management
- Semantic versioning (MAJOR.MINOR.PATCH)
- Changelog maintenance
- API compatibility tracking

## Conclusion

bill2csv provides a robust, secure, and extensible solution for converting PDF bills to structured CSV data. The modular architecture ensures maintainability, while the focus on security and data validation ensures reliable operation. The system is designed to be both user-friendly for end users and developer-friendly for future enhancements.