"""Output file management for bill2csv"""

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import pypdf


class OutputManager:
    """Manages writing output files (CSV, errors, metadata)"""
    
    def __init__(self, pdf_path: str, outdir: str):
        """
        Initialize output manager
        
        Args:
            pdf_path: Path to source PDF file
            outdir: Output directory path
        """
        self.pdf_path = Path(pdf_path)
        self.outdir = Path(outdir)
        self.stem = self.pdf_path.stem
        
        # Define output paths
        self.csv_path = self.outdir / f"{self.stem}.csv"
        self.errors_path = self.outdir / f"{self.stem}.errors.csv"
        self.meta_path = self.outdir / f"{self.stem}.meta.json"
        
        # Ensure output directory exists
        self.outdir.mkdir(parents=True, exist_ok=True)
    
    def write_csv(self, rows: List[Dict[str, str]]) -> None:
        """
        Write valid rows to CSV file
        
        Args:
            rows: List of validated row dictionaries
        """
        # Determine fieldnames based on which optional columns are present
        fieldnames = ["Date", "Description"]
        
        if rows:
            # Check for Payee column
            if "Payee" in rows[0]:
                fieldnames.append("Payee")
            
            fieldnames.append("Amount")
            
            # Check for Category column
            if "Category" in rows[0]:
                fieldnames.append("Category")
        else:
            # Default order if no rows
            fieldnames = ["Date", "Description", "Payee", "Amount", "Category"]
        
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    
    def write_errors(self, errors: List[Dict]) -> None:
        """
        Write error rows to errors CSV file
        
        Args:
            errors: List of error dictionaries with row, reason, raw fields
        """
        if not errors:
            return
        
        with open(self.errors_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["row", "reason", "raw"])
            
            for error in errors:
                raw_fields = [
                    error["raw"].get("Date") or "",
                    error["raw"].get("Description") or "",
                ]
                # Include Payee if present
                if "Payee" in error["raw"]:
                    raw_fields.append(error["raw"].get("Payee") or "")
                
                raw_fields.append(error["raw"].get("Amount") or "")
                
                # Include Category if present
                if "Category" in error["raw"]:
                    raw_fields.append(error["raw"].get("Category") or "")
                raw_str = ",".join(raw_fields)
                writer.writerow([error["row"], error["reason"], raw_str])
    
    def write_metadata(self, 
                      row_count: int, 
                      error_count: int,
                      model: str = "gemini-2.5-flash") -> None:
        """
        Write metadata JSON file
        
        Args:
            row_count: Number of valid rows
            error_count: Number of error rows
            model: Model name used for processing
        """
        # Get PDF page count
        try:
            with open(self.pdf_path, 'rb') as f:
                pdf_reader = pypdf.PdfReader(f)
                page_count = len(pdf_reader.pages)
        except:
            page_count = 0
        
        metadata = {
            "source_file": self.pdf_path.name,
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "pages": page_count,
            "rows": row_count,
            "errors": error_count
        }
        
        with open(self.meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
    def get_output_summary(self) -> Dict[str, str]:
        """
        Get summary of output files created
        
        Returns:
            Dictionary with file paths and status
        """
        summary = {
            "csv": str(self.csv_path),
            "csv_exists": self.csv_path.exists(),
        }
        
        if self.errors_path.exists():
            summary["errors"] = str(self.errors_path)
            summary["errors_exists"] = True
        
        if self.meta_path.exists():
            summary["metadata"] = str(self.meta_path)
            summary["metadata_exists"] = True
        
        return summary