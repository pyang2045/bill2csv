"""Command-line interface for bill2csv"""

import argparse
import sys
from pathlib import Path
from . import __version__


def parse_args(args=None):
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        prog="bill2csv",
        description="Convert PDF bills to CSV using Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  bill2csv invoice.pdf
  bill2csv invoice.pdf --outdir ./output
  bill2csv invoice.pdf --meta --quiet
  bill2csv invoice.pdf --keychain-service gemini-api --keychain-account bill2csv
        """,
    )
    
    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to the PDF file to convert",
    )
    
    parser.add_argument(
        "--outdir",
        type=str,
        default=None,
        help="Output directory (default: same as input file)",
    )
    
    parser.add_argument(
        "--meta",
        action="store_true",
        help="Generate metadata JSON file",
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console logs (errors still shown)",
    )
    
    parser.add_argument(
        "--api-key-env",
        type=str,
        default="GEMINI_API_KEY",
        help="Environment variable name for API key (default: GEMINI_API_KEY)",
    )
    
    parser.add_argument(
        "--keychain-service",
        type=str,
        help="macOS Keychain service name",
    )
    
    parser.add_argument(
        "--keychain-account",
        type=str,
        help="macOS Keychain account name",
    )
    
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if any invalid row (instead of writing .errors.csv)",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    
    parsed_args = parser.parse_args(args)
    
    # Validate PDF path
    pdf_path = Path(parsed_args.pdf_path)
    if not pdf_path.exists():
        parser.error(f"PDF file not found: {parsed_args.pdf_path}")
    if not pdf_path.is_file():
        parser.error(f"Path is not a file: {parsed_args.pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        parser.error(f"File is not a PDF: {parsed_args.pdf_path}")
    
    # Validate keychain arguments
    if parsed_args.keychain_service and not parsed_args.keychain_account:
        parser.error("--keychain-account required when using --keychain-service")
    if parsed_args.keychain_account and not parsed_args.keychain_service:
        parser.error("--keychain-service required when using --keychain-account")
    
    # Set default output directory
    if parsed_args.outdir is None:
        parsed_args.outdir = str(pdf_path.parent)
    else:
        outdir = Path(parsed_args.outdir)
        if not outdir.exists():
            try:
                outdir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                parser.error(f"Cannot create output directory: {e}")
        elif not outdir.is_dir():
            parser.error(f"Output path is not a directory: {parsed_args.outdir}")
    
    # Convert pdf_path to absolute path
    parsed_args.pdf_path = str(pdf_path.absolute())
    parsed_args.outdir = str(Path(parsed_args.outdir).absolute())
    
    return parsed_args