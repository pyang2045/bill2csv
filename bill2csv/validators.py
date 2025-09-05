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
        
        - Replace common symbols with spaces
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
        
        # Replace common symbols with spaces
        # Keep alphanumeric, spaces, and some punctuation
        import re
        # Replace multiple symbols with space
        desc_str = re.sub(r'[*#@&/\\|<>~`^_+=\[\]{}]', ' ', desc_str)
        # Replace multiple dashes/underscores with single space
        desc_str = re.sub(r'[-_]+', ' ', desc_str)
        
        # Collapse whitespace and ensure single line
        desc_str = " ".join(desc_str.split())
        
        # Remove any newlines or carriage returns
        desc_str = desc_str.replace("\n", " ").replace("\r", " ")
        
        # Final cleanup of multiple spaces
        desc_str = re.sub(r'\s+', ' ', desc_str)  # Collapse multiple spaces
        
        # Quote if contains commas
        if "," in desc_str:
            # Escape any existing quotes
            desc_str = desc_str.replace('"', '""')
            desc_str = f'"{desc_str}"'
        
        return desc_str.strip()


class PayeeValidator:
    """Validates and normalizes payee/merchant names"""
    
    @staticmethod
    def validate_and_normalize(payee_str: str) -> str:
        """
        Normalize payee/merchant name
        
        - Clean up formatting
        - Remove extra whitespace
        - Proper capitalization
        - Quote if contains commas
        
        Args:
            payee_str: Input payee string
            
        Returns:
            Normalized payee string
            
        Raises:
            ValidationError: If payee is invalid
        """
        if not payee_str or not payee_str.strip():
            # Payee can be empty
            return ""
        
        import re
        
        # Clean up the payee name
        payee_str = payee_str.strip()
        
        # Remove extra whitespace
        payee_str = " ".join(payee_str.split())
        
        # Handle common prefixes/suffixes
        # Remove TST*, SQ *, etc.
        payee_str = re.sub(r'^(TST\*|SQ\s*\*|SP\s*\*)\s*', '', payee_str, flags=re.IGNORECASE)
        
        # Remove trailing store numbers like #1234
        payee_str = re.sub(r'\s*#\d+$', '', payee_str)
        
        # Remove trailing transaction IDs
        payee_str = re.sub(r'\s*\*[A-Z0-9]+$', '', payee_str)
        
        # Proper case for known companies (customize as needed)
        known_companies = {
            'walmart': 'Walmart',
            'amazon': 'Amazon',
            'paypal': 'PayPal',
            'ebay': 'eBay',
            'uber': 'Uber',
            'lyft': 'Lyft',
            'doordash': 'DoorDash',
            'grubhub': 'GrubHub',
            'starbucks': 'Starbucks',
            'mcdonalds': "McDonald's",
            'target': 'Target',
            'costco': 'Costco',
            '7-eleven': '7-Eleven',
            '7 eleven': '7-Eleven',
        }
        
        # Check if it matches a known company (case-insensitive)
        lower_payee = payee_str.lower()
        for pattern, proper_name in known_companies.items():
            if pattern in lower_payee:
                payee_str = proper_name
                break
        
        # Quote if contains commas
        if "," in payee_str:
            # Escape any existing quotes
            payee_str = payee_str.replace('"', '""')
            payee_str = f'"{payee_str}"'
        
        return payee_str


class CategoryValidator:
    """Validates and normalizes category strings with hierarchical support"""
    
    _categories = None
    _categories_file = None
    _custom_categories_file = None
    
    @classmethod
    def set_categories_file(cls, file_path):
        """Set a custom categories file path"""
        if file_path:
            cls._custom_categories_file = Path(file_path)
            cls._categories = None  # Force reload
    
    @classmethod
    def _load_categories(cls):
        """Load categories from expense_categories.md file"""
        if cls._categories is not None:
            return cls._categories
        
        cls._categories = set()
        
        # Try to find the categories file
        from pathlib import Path
        import os
        
        # Look for expense_categories.md in various locations
        possible_paths = []
        
        # First check if custom file is specified
        if cls._custom_categories_file:
            possible_paths.append(cls._custom_categories_file)
        
        # Then check default locations
        possible_paths.extend([
            Path(__file__).parent.parent / "expense_categories.md",
            Path(os.getcwd()) / "expense_categories.md",
            Path.home() / ".bill2csv" / "expense_categories.md",
        ])
        
        categories_content = None
        for path in possible_paths:
            if path.exists():
                cls._categories_file = path
                with open(path, 'r', encoding='utf-8') as f:
                    categories_content = f.read()
                break
        
        if not categories_content:
            # Fallback to default categories if file not found
            cls._categories = {
                "Food & Dining",
                "Transportation", 
                "Shopping",
                "Entertainment",
                "Home & Utilities",
                "Financial",
                "Travel",
                "Business",
                "Education",
                "Income",
                "Other"
            }
            return cls._categories
        
        # Parse the markdown file
        current_main = None
        current_sub = None
        
        for line in categories_content.split('\n'):
            line = line.strip()
            
            if line.startswith('## '):
                # Main section header (not a category itself)
                continue
            elif line.startswith('- '):
                # Category (could be main or sub)
                category = line[2:].strip()
                indent_level = len(line) - len(line.lstrip())
                
                if indent_level == 0:  # Main category
                    current_main = category
                    current_sub = None
                    cls._categories.add(category)
                elif current_main:  # Sub-category
                    # Add both the sub-category alone and with hierarchy
                    cls._categories.add(category)
                    cls._categories.add(f"{current_main} > {category}")
                    
                    # For third-level categories
                    if indent_level > 2:
                        current_sub = category
                    elif current_sub:
                        cls._categories.add(f"{current_main} > {current_sub} > {category}")
        
        return cls._categories
    
    @classmethod
    def validate_and_normalize(cls, category_str: str) -> str:
        """
        Validate and normalize category with hierarchical support
        
        Args:
            category_str: Input category string (can be hierarchical with >)
            
        Returns:
            Normalized category string
            
        Raises:
            ValidationError: If category is invalid
        """
        if not category_str or not category_str.strip():
            # Category is optional, return "Other > Uncategorized" as default
            return "Other > Uncategorized"
        
        category_str = category_str.strip()
        
        # Load categories if not already loaded
        valid_categories = cls._load_categories()
        
        # Check exact match (case-insensitive)
        for valid_cat in valid_categories:
            if category_str.lower() == valid_cat.lower():
                return valid_cat
        
        # Check if it's a hierarchical category with different formatting
        # e.g., "Food/Dining" or "Food - Dining" should match "Food & Dining"
        normalized = category_str.replace('/', ' > ').replace(' - ', ' > ').replace(' & ', ' > ')
        for valid_cat in valid_categories:
            if normalized.lower() == valid_cat.lower():
                return valid_cat
        
        # If not in valid categories, default to "Other > Uncategorized"
        return "Other > Uncategorized"
    
    @classmethod
    def get_all_categories(cls):
        """Get all valid categories for reference"""
        return sorted(cls._load_categories())


class RowValidator:
    """Validates complete CSV rows"""
    
    def __init__(self):
        self.date_validator = DateValidator()
        self.amount_validator = AmountValidator()
        self.description_validator = DescriptionValidator()
        self.payee_validator = PayeeValidator()
        self.category_validator = CategoryValidator()
    
    def validate_row(self, row: Dict[str, str]) -> Tuple[bool, Optional[str], Dict[str, str]]:
        """
        Validate a complete CSV row
        
        Args:
            row: Dictionary with Date, Description, Amount, and optionally Payee and Category keys
            
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
        
        # Validate Payee (optional field)
        if "Payee" in row:
            try:
                normalized["Payee"] = self.payee_validator.validate_and_normalize(row["Payee"])
            except ValidationError as e:
                return False, f"Payee error: {e}", row
        
        # Validate Category (optional field)
        if "Category" in row:
            try:
                normalized["Category"] = self.category_validator.validate_and_normalize(row["Category"])
            except ValidationError as e:
                return False, f"Category error: {e}", row
        
        return True, None, normalized