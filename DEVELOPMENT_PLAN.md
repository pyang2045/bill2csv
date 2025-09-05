# bill2csv Development Plan

## Executive Summary
Step-by-step development plan for building a CLI tool that converts PDF bills to CSV format using Gemini 2.5 Flash API.

## Development Phases

### Phase 1: Project Setup (Day 1)
**Goal**: Establish project foundation and structure

**Tasks**:
1. Create directory structure
2. Initialize Python package
3. Set up dependencies (requirements.txt)
4. Configure setup.py for installation
5. Create entry point for CLI command

**Deliverables**:
- Working package structure
- Installable via `pip install -e .`
- Basic `bill2csv` command available

### Phase 2: Core Infrastructure (Days 2-3)
**Goal**: Build foundational components

**CLI Module (`cli.py`)**:
- Argument parser with all options
- Help text and version display
- Input validation

**API Key Module (`api_key.py`)**:
- macOS Keychain integration
- Environment variable support
- Secure error handling

**Validation Module (`validators.py`)**:
- Date normalization (DD-MM-YYYY)
- Amount validation and formatting
- Description cleaning and quoting

### Phase 3: API Integration (Day 4)
**Goal**: Connect to Gemini API for PDF processing

**PDF Processor (`pdf_processor.py`)**:
- Gemini client configuration
- PDF upload functionality
- Prompt integration (v2 from spec)
- Response handling

**Key Features**:
- Timeout handling
- Error recovery
- Response validation

### Phase 4: Data Processing (Days 5-6)
**Goal**: Clean and validate API responses

**CSV Cleaner (`csv_cleaner.py`)**:
- Strip markdown/code blocks
- Extract CSV content
- Parse into structured data

**Row Processor**:
- Individual row validation
- Error collection
- Data normalization

### Phase 5: Output Generation (Day 7)
**Goal**: Create output files and user feedback

**Output Manager (`output.py`)**:
- CSV file writer
- Error CSV generator
- Metadata JSON creator

**Console Logger (`utils.py`)**:
- Progress indicators
- Summary formatting
- Error reporting

### Phase 6: Integration (Day 8)
**Goal**: Wire all components together

**Main Orchestrator (`__main__.py`)**:
- Component initialization
- Execution flow control
- Error handling
- Exit code management

### Phase 7: Testing (Days 9-10)
**Goal**: Ensure reliability and correctness

**Unit Tests**:
- Validator functions
- CSV parsing
- API key retrieval

**Integration Tests**:
- End-to-end workflow
- Sample PDF processing
- Error scenarios

### Phase 8: Documentation (Day 11)
**Goal**: Complete user and developer docs

**Documentation**:
- README with examples
- API documentation
- Code comments
- User guide

## Critical Path Items

### Must-Have Features (MVP)
1. ✅ PDF to CSV conversion via Gemini
2. ✅ Secure API key handling
3. ✅ Date/Amount/Description validation
4. ✅ Error row isolation
5. ✅ Basic console output

### Should-Have Features
1. ✅ Metadata generation (--meta)
2. ✅ Quiet mode (--quiet)
3. ✅ Custom output directory
4. ✅ Strict validation mode

### Nice-to-Have Features
1. ⏸ Progress bar for large files
2. ⏸ Batch processing multiple PDFs
3. ⏸ Configuration file support

## Technical Decisions

### Architecture
- **Design Pattern**: Command pattern with service classes
- **Error Strategy**: Fail gracefully, isolate errors
- **Logging**: Minimal by default, verbose on request

### Technology Choices
- **Python 3.9+**: Modern features, type hints
- **google-generativeai**: Official SDK
- **CSV module**: Standard library for reliability
- **subprocess**: Secure Keychain access

### Code Standards
- Type hints for all functions
- Docstrings for public APIs
- Error messages with solutions
- No hard-coded values

## Risk Management

### High-Risk Areas
1. **Gemini API stability**: Implement retries and fallbacks
2. **PDF format variations**: Robust error handling
3. **CSV parsing edge cases**: Comprehensive validation

### Mitigation Strategies
- Extensive input validation
- Clear error messages
- Graceful degradation
- Comprehensive testing

## Quality Gates

### Before Each Phase
- [ ] Requirements clear
- [ ] Dependencies available
- [ ] Design reviewed

### After Each Phase
- [ ] Code works as expected
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Code reviewed (self)

### Final Checklist
- [ ] All CLI options functional
- [ ] Security requirements met
- [ ] Error handling complete
- [ ] Tests provide >80% coverage
- [ ] Documentation comprehensive
- [ ] Performance acceptable

## Resource Requirements

### Development Environment
- macOS (for Keychain testing)
- Python 3.9+
- Gemini API key
- Sample PDF bills

### Time Estimates
- **Total Duration**: 11 working days
- **Effort**: ~35 hours
- **Testing**: Additional 5-10 hours

## Success Metrics

### Functional Success
- Processes multi-page PDFs correctly
- Produces valid CSV output
- Handles errors gracefully
- Secure API key management

### Quality Success
- No critical bugs
- Clear error messages
- Fast performance (<5s for typical PDF)
- Clean, maintainable code

### User Success
- Intuitive CLI interface
- Helpful documentation
- Reliable operation
- Clear feedback

## Next Steps

1. **Immediate**: Set up project structure
2. **Short-term**: Implement core validation logic
3. **Medium-term**: Integrate Gemini API
4. **Long-term**: Polish and optimize

## Notes for Implementation

### Priority Order
1. Get basic flow working (PDF → API → CSV)
2. Add validation and error handling
3. Implement all CLI options
4. Add tests and documentation
5. Optimize and polish

### Key Considerations
- Security first (never log sensitive data)
- User experience (clear feedback)
- Maintainability (clean code)
- Reliability (handle edge cases)