"""Validation functions for bill2csv data processing"""

import re
from datetime import datetime
from typing import Tuple, Dict, Optional


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class DateValidator:
    """Validates and normalizes date strings to DD-MM-YYYY format"""
    
    @staticmethod
    def validate_and_normalize(date_str: str) -> str:
        """
        Convert various date formats to DD-MM-YYYY
        
        Supported formats:
        - DD-MM-YYYY
        - DD/MM/YYYY
        - YYYY-MM-DD
        - D-M-YYYY
        - D/M/YYYY
        
        Args:
            date_str: Input date string
            
        Returns:
            Normalized date in DD-MM-YYYY format
            
        Raises:
            ValidationError: If date cannot be parsed
        """
        if not date_str or not date_str.strip():
            raise ValidationError("Date cannot be empty")
        
        date_str = date_str.strip()
        
        # Try different date formats
        formats = [
            ("%d-%m-%Y", "-"),
            ("%d/%m/%Y", "/"),
            ("%Y-%m-%d", "-"),
            ("%d-%m-%y", "-"),
            ("%d/%m/%y", "/"),
            ("%Y/%m/%d", "/"),
        ]
        
        for fmt, sep in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # Return in DD-MM-YYYY format
                return dt.strftime("%d-%m-%Y")
            except ValueError:
                continue
        
        # If no format matched, raise error
        raise ValidationError(f"Invalid date format: {date_str}")


class AmountValidator:
    """Validates and normalizes amount strings"""
    
    @staticmethod
    def validate_and_normalize(amount_str: str) -> str:
        """
        Normalize amount to standard decimal format
        
        Handles:
        - Unicode minus sign (−) → ASCII minus (-)
        - Thousands separators (,) → removed
        - Parentheses for negatives
        - Currency symbols
        
        Args:
            amount_str: Input amount string
            
        Returns:
            Normalized amount string
            
        Raises:
            ValidationError: If amount is invalid
        """
        if not amount_str or not amount_str.strip():
            raise ValidationError("Amount cannot be empty")
        
        amount_str = amount_str.strip()
        
        # Replace Unicode minus with ASCII minus
        amount_str = amount_str.replace("−", "-")
        amount_str = amount_str.replace("–", "-")
        
        # Handle parentheses for negative numbers
        if amount_str.startswith("(") and amount_str.endswith(")"):
            amount_str = "-" + amount_str[1:-1]
        
        # Remove currency symbols
        amount_str = re.sub(r"[$£€¥₹¢]", "", amount_str)
        
        # Remove thousands separators
        amount_str = amount_str.replace(",", "")
        
        # Remove any spaces
        amount_str = amount_str.replace(" ", "")
        
        # Validate the result is a valid number
        if not re.match(r"^-?\d+(\.\d+)?$", amount_str):
            raise ValidationError(f"Invalid amount format: {amount_str}")
        
        # Ensure decimal point (not comma)
        amount_str = amount_str.replace(",", ".")
        
        # Format to ensure proper decimal representation
        try:
            amount = float(amount_str)
            # Keep original precision but ensure consistent format
            if "." in amount_str:
                decimal_places = len(amount_str.split(".")[-1])
                return f"{amount:.{decimal_places}f}"
            else:
                return str(int(amount))
        except ValueError:
            raise ValidationError(f"Cannot parse amount: {amount_str}")


class DescriptionValidator:
    """Validates and normalizes description strings"""
    
    @staticmethod
    def validate_and_normalize(desc_str: str) -> str:
        """
        Normalize description text
        
        - Collapse whitespace
        - Ensure single line
        - Quote if contains commas
        
        Args:
            desc_str: Input description string
            
        Returns:
            Normalized description string
            
        Raises:
            ValidationError: If description is invalid
        """
        if not desc_str or not desc_str.strip():
            raise ValidationError("Description cannot be empty")
        
        # Collapse whitespace and ensure single line
        desc_str = " ".join(desc_str.split())
        
        # Remove any newlines or carriage returns
        desc_str = desc_str.replace("\n", " ").replace("\r", " ")
        
        # Quote if contains commas
        if "," in desc_str:
            # Escape any existing quotes
            desc_str = desc_str.replace('"', '""')
            desc_str = f'"{desc_str}"'
        
        return desc_str


class CategoryValidator:
    """Validates and normalizes category strings"""
    
    VALID_CATEGORIES = [
        "Food & Dining",
        "Transportation", 
        "Shopping",
        "Entertainment",
        "Bills & Utilities",
        "Healthcare",
        "Education",
        "Travel",
        "Fees & Charges",
        "Income/Credit",
        "Other"
    ]
    
    @classmethod
    def validate_and_normalize(cls, category_str: str) -> str:
        """
        Validate and normalize category
        
        Args:
            category_str: Input category string
            
        Returns:
            Normalized category string
            
        Raises:
            ValidationError: If category is invalid
        """
        if not category_str or not category_str.strip():
            # Category is optional, return "Other" as default
            return "Other"
        
        category_str = category_str.strip()
        
        # Check if it's a valid category (case-insensitive)
        for valid_cat in cls.VALID_CATEGORIES:
            if category_str.lower() == valid_cat.lower():
                return valid_cat
        
        # If not in valid categories, default to "Other"
        return "Other"


class RowValidator:
    """Validates complete CSV rows"""
    
    def __init__(self):
        self.date_validator = DateValidator()
        self.amount_validator = AmountValidator()
        self.description_validator = DescriptionValidator()
        self.category_validator = CategoryValidator()
    
    def validate_row(self, row: Dict[str, str]) -> Tuple[bool, Optional[str], Dict[str, str]]:
        """
        Validate a complete CSV row
        
        Args:
            row: Dictionary with Date, Description, Amount, and optionally Category keys
            
        Returns:
            Tuple of (is_valid, error_message, normalized_row)
        """
        normalized = {}
        
        # Check required fields
        required_fields = ["Date", "Description", "Amount"]
        for field in required_fields:
            if field not in row:
                return False, f"Missing field: {field}", row
        
        # Validate Date
        try:
            normalized["Date"] = self.date_validator.validate_and_normalize(row["Date"])
        except ValidationError as e:
            return False, f"Date error: {e}", row
        
        # Validate Description
        try:
            normalized["Description"] = self.description_validator.validate_and_normalize(row["Description"])
        except ValidationError as e:
            return False, f"Description error: {e}", row
        
        # Validate Amount
        try:
            normalized["Amount"] = self.amount_validator.validate_and_normalize(row["Amount"])
        except ValidationError as e:
            return False, f"Amount error: {e}", row
        
        # Validate Category (optional field)
        if "Category" in row:
            try:
                normalized["Category"] = self.category_validator.validate_and_normalize(row["Category"])
            except ValidationError as e:
                return False, f"Category error: {e}", row
        
        return True, None, normalized