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
            
            # Look for header line (now with Payee and Category)
            if not header_found:
                if "Date" in line and "Description" in line and "Amount" in line:
                    # Check which optional columns are included
                    if "Payee" in line and "Category" in line:
                        cleaned_lines.append("Date,Description,Payee,Amount,Category")
                    elif "Payee" in line:
                        cleaned_lines.append("Date,Description,Payee,Amount")
                    elif "Category" in line:
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
                    if "Payee" in line and "Category" in line:
                        cleaned_lines = ["Date,Description,Payee,Amount,Category"]
                    elif "Payee" in line:
                        cleaned_lines = ["Date,Description,Payee,Amount"]
                    elif "Category" in line:
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
    def _fix_unquoted_commas(csv_text: str) -> str:
        """
        Fix CSV lines where fields containing commas are not properly quoted.

        This is a safety net for when the LLM doesn't properly quote fields.

        Args:
            csv_text: Raw CSV text

        Returns:
            Fixed CSV text with proper quoting
        """
        lines = csv_text.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            if i == 0:  # Header line, keep as-is
                fixed_lines.append(line)
                continue

            if not line.strip():
                continue

            # Try to parse with standard parser first
            try:
                reader = csv.reader(StringIO(line))
                parsed = list(reader)[0]

                # Check expected column count (should be 5: Date, Description, Payee, Amount, Category)
                # or 4 if no Category, or 3 if old format
                if len(parsed) == 5 or len(parsed) == 4 or len(parsed) == 3:
                    # Line is fine, keep it
                    fixed_lines.append(line)
                    continue
            except:
                pass

            # Line has issues, try to fix it
            # Strategy: Parse manually and re-quote fields that need it
            try:
                reader = csv.reader(StringIO(line))
                fields = list(reader)[0]

                # If we have too many fields, it means some fields with commas aren't quoted
                # Try to intelligently merge fields
                if len(fields) > 5:
                    # Expected format: Date, Description, Payee, Amount, Category
                    # Amount should be a number (possibly negative)
                    # Category might have > separator

                    # Find the amount field (should match number pattern)
                    amount_pattern = re.compile(r'^-?\d+\.?\d*$')
                    amount_idx = None

                    for idx in range(len(fields) - 1, -1, -1):  # Search from right
                        if amount_pattern.match(fields[idx].strip()):
                            amount_idx = idx
                            break

                    if amount_idx is not None and amount_idx >= 3:
                        # Reconstruct: Date (0), Description (1..?), Payee (?..amount_idx-1), Amount, Category
                        date = fields[0]

                        # Strategy: Payee is usually 1-2 fields before Amount
                        # Description is usually 1-2 fields after Date
                        # If we have many fields, most are likely from Description or Payee

                        # Conservative approach:
                        # - Date is always first
                        # - Description is second (might contain commas)
                        # - Payee is the field(s) right before Amount (might contain commas)
                        # - Amount is identified
                        # - Category is after Amount

                        # For now, assume Description is just field[1], and everything
                        # between field[1] and amount is Payee (more common issue)
                        description = fields[1]

                        # Everything between description and amount is Payee
                        payee_parts = fields[2:amount_idx]
                        payee = ','.join(payee_parts) if payee_parts else ''

                        amount = fields[amount_idx]
                        category = ','.join(fields[amount_idx + 1:]) if amount_idx + 1 < len(fields) else ''

                        # Re-construct line with proper quoting
                        reconstructed = []
                        reconstructed.append(date)
                        reconstructed.append(f'"{description}"' if ',' in description else description)
                        reconstructed.append(f'"{payee}"' if ',' in payee else payee)
                        reconstructed.append(amount)
                        if category:
                            reconstructed.append(f'"{category}"' if ',' in category and '>' not in category else category)

                        fixed_lines.append(','.join(reconstructed))
                        continue
            except:
                pass

            # If all else fails, keep the original line
            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

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
            # Apply fix for unquoted commas
            csv_text = CSVCleaner._fix_unquoted_commas(csv_text)

            # Use a more lenient CSV parser that handles edge cases
            reader = csv.DictReader(StringIO(csv_text), skipinitialspace=True)
            rows = []

            for row in reader:
                # Handle potential variations in field names
                normalized_row = {}
                
                # Map various possible field names to standard names
                date_keys = ["Date", "date", "DATE", "Transaction Date", "Posting Date"]
                desc_keys = ["Description", "description", "DESC", "Details", "Transaction"]
                payee_keys = ["Payee", "payee", "Merchant", "Vendor", "Company"]
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
                
                # Find and map Payee (optional)
                for key in payee_keys:
                    if key in row:
                        normalized_row["Payee"] = row[key]
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