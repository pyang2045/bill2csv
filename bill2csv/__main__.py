#!/usr/bin/env python3
"""Main entry point for bill2csv command-line tool"""

import sys
import traceback
from pathlib import Path

from .cli import parse_args
from .api_key import APIKeyManager
from .pdf_processor import GeminiProcessor
from .csv_cleaner import CSVCleaner
from .validators import RowValidator, CategoryValidator
from .output import OutputManager
from .utils import ConsoleLogger, get_file_info
from . import config


def main():
    """Main entry point for bill2csv"""
    try:
        # Parse command-line arguments
        args = parse_args()
        
        # Initialize logger
        logger = ConsoleLogger(quiet=args.quiet)
        
        # Set custom categories file if provided
        if args.categories_file:
            CategoryValidator.set_categories_file(args.categories_file)
            logger.progress(f"Using categories file: {args.categories_file}")
        
        # Get file info
        file_info = get_file_info(args.pdf_path)
        if not file_info["exists"]:
            logger.error(f"PDF file not found: {args.pdf_path}")
            return 1
        
        logger.progress(f"Processing {file_info['name']} ({file_info['size_formatted']})")
        
        # Get API key
        logger.progress("Retrieving API key...")
        try:
            api_key = APIKeyManager.get_api_key(args)
        except RuntimeError as e:
            logger.error(str(e))
            return 1
        
        # Process PDF with Gemini
        logger.progress("Sending PDF to Gemini API...")
        try:
            processor = GeminiProcessor(api_key, debug=args.debug)
            raw_response = processor.process_pdf(args.pdf_path)
        except Exception as e:
            logger.error(f"Failed to process PDF: {str(e)}")
            return 1
        
        # Clean and parse CSV response
        logger.progress("Parsing CSV response...")
        try:
            rows = CSVCleaner.clean_and_parse(raw_response)
        except ValueError as e:
            logger.error(f"Failed to parse CSV: {str(e)}")
            return 1
        
        if not rows:
            logger.error("No data rows found in response")
            return 1
        
        # Validate rows
        logger.progress(f"Validating {len(rows)} rows...")
        validator = RowValidator()
        valid_rows = []
        error_rows = []
        
        for i, row in enumerate(rows, start=2):  # Start at 2 (header is line 1)
            is_valid, error_msg, normalized_row = validator.validate_row(row)
            
            if is_valid:
                valid_rows.append(normalized_row)
            else:
                error_rows.append({
                    "row": i,
                    "reason": error_msg,
                    "raw": row
                })
        
        # Handle strict mode
        if args.strict and error_rows:
            logger.error(f"Validation failed in strict mode: {len(error_rows)} invalid rows")
            for error in error_rows[:5]:  # Show first 5 errors
                logger.error(f"  Row {error['row']}: {error['reason']}")
            if len(error_rows) > 5:
                logger.error(f"  ... and {len(error_rows) - 5} more errors")
            return 1
        
        # Write output files
        logger.progress("Writing output files...")
        output_mgr = OutputManager(args.pdf_path, args.outdir)
        
        # Write valid rows to CSV
        output_mgr.write_csv(valid_rows)
        
        # Write error rows if any
        if error_rows:
            output_mgr.write_errors(error_rows)
            logger.warning(f"Found {len(error_rows)} invalid rows, written to {output_mgr.errors_path.name}")
        
        # Write metadata if requested
        if args.meta:
            output_mgr.write_metadata(
                row_count=len(valid_rows),
                error_count=len(error_rows),
                model=processor.model_name
            )
            logger.progress(f"Metadata written to {output_mgr.meta_path.name}")
        
        # Log success summary
        logger.success(
            args.pdf_path,
            str(output_mgr.csv_path),
            len(valid_rows),
            len(error_rows)
        )
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        if "--debug" in sys.argv:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())