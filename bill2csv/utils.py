"""Utility functions for bill2csv"""

import sys
from pathlib import Path
from typing import Optional
import logging


class ConsoleLogger:
    """Handles console output and logging"""
    
    def __init__(self, quiet: bool = False):
        """
        Initialize console logger
        
        Args:
            quiet: If True, suppress non-error output
        """
        self.quiet = quiet
        
        # Set up logging for debug/error tracking
        logging.basicConfig(
            level=logging.WARNING if quiet else logging.INFO,
            format='%(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def log(self, message: str) -> None:
        """
        Log informational message
        
        Args:
            message: Message to log
        """
        if not self.quiet:
            print(message)
    
    def error(self, message: str) -> None:
        """
        Log error message (always shown, even in quiet mode)
        
        Args:
            message: Error message to log
        """
        print(f"Error: {message}", file=sys.stderr)
    
    def warning(self, message: str) -> None:
        """
        Log warning message
        
        Args:
            message: Warning message to log
        """
        if not self.quiet:
            print(f"Warning: {message}", file=sys.stderr)
    
    def success(self, source: str, dest: str, rows: int, errors: int) -> None:
        """
        Log success summary
        
        Args:
            source: Source PDF filename
            dest: Destination CSV filename
            rows: Number of valid rows processed
            errors: Number of error rows
        """
        source_name = Path(source).name
        dest_name = Path(dest).name
        
        if errors > 0:
            message = f"✅ {source_name} → {dest_name} ({rows} rows, {errors} errors)"
        else:
            message = f"✅ {source_name} → {dest_name} ({rows} rows)"
        
        self.log(message)
    
    def progress(self, message: str) -> None:
        """
        Log progress message
        
        Args:
            message: Progress message
        """
        if not self.quiet:
            print(f"  {message}")


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_file_info(file_path: str) -> dict:
    """
    Get basic file information
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file info
    """
    path = Path(file_path)
    if not path.exists():
        return {"exists": False}
    
    return {
        "exists": True,
        "size": path.stat().st_size,
        "size_formatted": format_file_size(path.stat().st_size),
        "name": path.name,
        "extension": path.suffix,
    }