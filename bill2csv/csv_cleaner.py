"""CSV response cleaning and parsing"""

import re
import csv
from io import StringIO
from typing import List, Dict


class CSVCleaner:
    """Clean and parse CSV responses from Gemini API"""
    
    @staticmethod
    def clean_response(raw_response: str) -> str:
        """
        Clean raw API response to extract CSV content
        
        Removes:
        - Markdown code fences (```csv ... ```)
        - Extra explanatory text
        - Leading/trailing whitespace
        
        Args:
            raw_response: Raw text response from API
            
        Returns:
            Cleaned CSV string starting with header
            
        Raises:
            ValueError: If no valid CSV content found
        """
        if not raw_response:
            raise ValueError("Empty response from API")
        
        # Remove markdown code fences if present
        # Pattern for ```csv ... ``` or ``` ... ```
        code_block_pattern = r"```(?:csv)?\s*\n(.*?)\n```"
        match = re.search(code_block_pattern, raw_response, re.DOTALL)
        if match:
            raw_response = match.group(1)
        
        # Split into lines and clean each
        lines = raw_response.strip().split('\n')
        cleaned_lines = []
        header_found = False
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Look for header line (now with Category)
            if not header_found:
                if "Date" in line and "Description" in line and "Amount" in line:
                    # Check if Category is included
                    if "Category" in line:
                        cleaned_lines.append("Date,Description,Amount,Category")
                    else:
                        cleaned_lines.append("Date,Description,Amount")
                    header_found = True
            else:
                # Add data lines after header
                # Skip lines that look like explanatory text
                if not line.startswith("#") and not line.startswith("//"):
                    cleaned_lines.append(line)
        
        if not header_found:
            # Try to find header in a different format
            for i, line in enumerate(lines):
                if "Date" in line and "Description" in line and "Amount" in line:
                    # Found header, use everything from this point
                    if "Category" in line:
                        cleaned_lines = ["Date,Description,Amount,Category"]
                    else:
                        cleaned_lines = ["Date,Description,Amount"]
                    cleaned_lines.extend(lines[i+1:])
                    header_found = True
                    break
        
        if not header_found or len(cleaned_lines) < 1:
            raise ValueError("No valid CSV content found in response")
        
        return '\n'.join(cleaned_lines)
    
    @staticmethod
    def parse_csv(csv_text: str) -> List[Dict[str, str]]:
        """
        Parse cleaned CSV text into list of dictionaries
        
        Args:
            csv_text: Cleaned CSV string with header
            
        Returns:
            List of dictionaries with Date, Description, Amount, and optionally Category keys
            
        Raises:
            ValueError: If CSV parsing fails
        """
        try:
            reader = csv.DictReader(StringIO(csv_text))
            rows = []
            
            for row in reader:
                # Handle potential variations in field names
                normalized_row = {}
                
                # Map various possible field names to standard names
                date_keys = ["Date", "date", "DATE", "Transaction Date", "Posting Date"]
                desc_keys = ["Description", "description", "DESC", "Details", "Merchant"]
                amount_keys = ["Amount", "amount", "AMT", "Total", "Value"]
                category_keys = ["Category", "category", "CAT", "Type", "Classification"]
                
                # Find and map Date
                for key in date_keys:
                    if key in row:
                        normalized_row["Date"] = row[key]
                        break
                
                # Find and map Description
                for key in desc_keys:
                    if key in row:
                        normalized_row["Description"] = row[key]
                        break
                
                # Find and map Amount
                for key in amount_keys:
                    if key in row:
                        normalized_row["Amount"] = row[key]
                        break
                
                # Find and map Category (optional)
                for key in category_keys:
                    if key in row:
                        normalized_row["Category"] = row[key]
                        break
                
                # Only add if we have all required fields
                if all(k in normalized_row for k in ["Date", "Description", "Amount"]):
                    rows.append(normalized_row)
            
            return rows
            
        except csv.Error as e:
            raise ValueError(f"CSV parsing error: {str(e)}")
    
    @classmethod
    def clean_and_parse(cls, raw_response: str) -> List[Dict[str, str]]:
        """
        Combined clean and parse operation
        
        Args:
            raw_response: Raw API response
            
        Returns:
            List of parsed CSV rows as dictionaries
        """
        cleaned_csv = cls.clean_response(raw_response)
        return cls.parse_csv(cleaned_csv)