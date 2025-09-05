# bill2csv Implementation Plan

## Phase 1: Foundation (Core Structure)

### 1.1 Project Setup
**File: `setup.py` / `pyproject.toml`**
- Configure package metadata
- Define dependencies: `google-generativeai`, Python 3.9+
- Set up entry point for `bill2csv` command

### 1.2 Project Structure
```
bill2csv/
├── bill2csv/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── cli.py               # CLI argument parsing
│   ├── api_key.py           # Secure API key retrieval
│   ├── pdf_processor.py     # Gemini API integration
│   ├── csv_cleaner.py       # CSV cleaning and parsing
│   ├── validators.py        # Validation functions
│   ├── output.py            # File output handlers
│   └── utils.py             # Utility functions
├── tests/
│   ├── test_validators.py
│   ├── test_csv_cleaner.py
│   └── test_api_key.py
├── setup.py
├── requirements.txt
└── README.md
```

## Phase 2: Core Modules

### 2.1 CLI Argument Parser (`cli.py`)
```python
# Key arguments to implement:
- pdf_path (positional, required)
- --outdir (default: input file directory)
- --meta (flag for metadata generation)
- --quiet (suppress logs)
- --api-key-env (default: GEMINI_API_KEY)
- --keychain-service, --keychain-account
- --strict (fail on invalid rows)
- --version
- -h/--help
```

### 2.2 API Key Manager (`api_key.py`)
```python
class APIKeyManager:
    def get_api_key(args) -> str:
        # Priority order:
        # 1. Try macOS Keychain if args provided
        # 2. Fall back to environment variable
        # 3. Raise error if not found
```

### 2.3 PDF Processor (`pdf_processor.py`)
```python
class GeminiProcessor:
    PROMPT_V2 = """..."""  # Exact prompt from spec
    
    def process_pdf(pdf_path: str, api_key: str) -> str:
        # 1. Configure Gemini client
        # 2. Upload PDF
        # 3. Send with prompt
        # 4. Return raw CSV response
```

## Phase 3: Data Processing

### 3.1 CSV Cleaner (`csv_cleaner.py`)
```python
class CSVCleaner:
    def clean_response(raw_response: str) -> str:
        # 1. Strip markdown/code fences
        # 2. Find first "Date,Description,Amount"
        # 3. Keep everything after header
        # 4. Return cleaned CSV text
```

### 3.2 Validators (`validators.py`)
```python
class DateValidator:
    def validate_and_normalize(date_str: str) -> str:
        # Try formats: DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD
        # Return DD-MM-YYYY or raise ValidationError

class AmountValidator:
    def validate_and_normalize(amount_str: str) -> str:
        # Handle Unicode minus (−), remove thousands separators
        # Ensure decimal point notation
        # Return normalized amount or raise ValidationError

class DescriptionValidator:
    def validate_and_normalize(desc_str: str) -> str:
        # Collapse whitespace, ensure single line
        # Quote if contains commas
        # Return normalized description
```

### 3.3 Row Validator (`validators.py`)
```python
class RowValidator:
    def validate_row(row: dict) -> tuple[bool, str, dict]:
        # Returns: (is_valid, error_reason, normalized_row)
        # Validates all three fields
        # Returns normalized values if valid
```

## Phase 4: Output Management

### 4.1 File Writers (`output.py`)
```python
class OutputManager:
    def __init__(self, stem: str, outdir: str):
        self.csv_path = f"{outdir}/{stem}.csv"
        self.errors_path = f"{outdir}/{stem}.errors.csv"
        self.meta_path = f"{outdir}/{stem}.meta.json"
    
    def write_csv(rows: list[dict]):
        # Write valid rows to CSV
    
    def write_errors(errors: list[dict]):
        # Write error rows with format: row,reason,raw
    
    def write_metadata(metadata: dict):
        # Write JSON metadata file
```

### 4.2 Console Logger (`utils.py`)
```python
class ConsoleLogger:
    def __init__(self, quiet: bool):
        self.quiet = quiet
    
    def log_summary(source: str, dest: str, rows: int, errors: int):
        # Format: ✅ bill.pdf → bill.csv (15 rows, 1 error)
    
    def log_error(message: str):
        # Always show errors, even in quiet mode
```

## Phase 5: Main Orchestration

### 5.1 Main Logic (`__main__.py`)
```python
def main():
    # 1. Parse arguments
    args = parse_args()
    
    # 2. Get API key
    api_key = APIKeyManager.get_api_key(args)
    
    # 3. Process PDF with Gemini
    raw_csv = GeminiProcessor.process_pdf(args.pdf_path, api_key)
    
    # 4. Clean response
    cleaned_csv = CSVCleaner.clean_response(raw_csv)
    
    # 5. Parse and validate rows
    valid_rows = []
    error_rows = []
    for row_num, row in enumerate(csv.DictReader(cleaned_csv)):
        is_valid, error, normalized = RowValidator.validate_row(row)
        if is_valid:
            valid_rows.append(normalized)
        else:
            error_rows.append({
                'row': row_num,
                'reason': error,
                'raw': row
            })
    
    # 6. Handle strict mode
    if args.strict and error_rows:
        sys.exit(f"Validation failed: {len(error_rows)} invalid rows")
    
    # 7. Write outputs
    output_mgr = OutputManager(stem, args.outdir)
    output_mgr.write_csv(valid_rows)
    if error_rows:
        output_mgr.write_errors(error_rows)
    if args.meta:
        output_mgr.write_metadata(metadata)
    
    # 8. Log summary
    logger.log_summary(args.pdf_path, output_path, len(valid_rows), len(error_rows))
```

## Phase 6: Testing

### 6.1 Unit Tests
- Test date validation with various formats
- Test amount normalization (Unicode, thousands)
- Test description quoting logic
- Test API key retrieval methods
- Test CSV cleaning (markdown stripping)

### 6.2 Integration Tests
- Create sample PDF with known content
- Test full pipeline execution
- Verify output file generation
- Test error handling paths

## Phase 7: Packaging & Documentation

### 7.1 Executable Setup
- Configure entry point in setup.py
- Ensure shebang line for direct execution
- Test installation with pip

### 7.2 Documentation
- Complete README with usage examples
- Add docstrings to all public functions
- Include sample PDFs for testing

## Implementation Order

1. **Start with CLI and project structure** (Phase 1-2.1)
2. **Implement validators** (Phase 3.2) - can test independently
3. **Add API key retrieval** (Phase 2.2)
4. **Build Gemini integration** (Phase 2.3)
5. **Implement CSV cleaning** (Phase 3.1)
6. **Create output handlers** (Phase 4)
7. **Wire up main logic** (Phase 5)
8. **Add tests** (Phase 6)
9. **Package and document** (Phase 7)

## Key Considerations

### Security
- Never log API keys or bill content
- Use subprocess for secure Keychain access
- Validate all external inputs

### Error Handling
- Graceful failures with clear error messages
- Separate error CSV for invalid rows
- Non-zero exit codes for failures

### Performance
- Stream CSV processing for large files
- Efficient regex patterns for validation
- Minimal memory footprint

### User Experience
- Clear progress indicators
- Helpful error messages
- Intuitive CLI interface
- Summary output showing success/errors