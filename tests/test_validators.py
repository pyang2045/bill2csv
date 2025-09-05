"""Unit tests for validators module"""

import pytest
from bill2csv.validators import (
    DateValidator, 
    AmountValidator, 
    DescriptionValidator,
    RowValidator,
    ValidationError
)


class TestDateValidator:
    """Test date validation and normalization"""
    
    def setup_method(self):
        self.validator = DateValidator()
    
    def test_valid_dd_mm_yyyy(self):
        assert self.validator.validate_and_normalize("13-06-2018") == "13-06-2018"
        assert self.validator.validate_and_normalize("01-01-2020") == "01-01-2020"
        assert self.validator.validate_and_normalize("31-12-2023") == "31-12-2023"
    
    def test_valid_dd_mm_yyyy_slash(self):
        assert self.validator.validate_and_normalize("13/06/2018") == "13-06-2018"
        assert self.validator.validate_and_normalize("01/01/2020") == "01-01-2020"
    
    def test_valid_yyyy_mm_dd(self):
        assert self.validator.validate_and_normalize("2018-06-13") == "13-06-2018"
        assert self.validator.validate_and_normalize("2020-01-01") == "01-01-2020"
    
    def test_empty_date(self):
        with pytest.raises(ValidationError, match="Date cannot be empty"):
            self.validator.validate_and_normalize("")
        with pytest.raises(ValidationError, match="Date cannot be empty"):
            self.validator.validate_and_normalize("  ")
    
    def test_invalid_format(self):
        with pytest.raises(ValidationError, match="Invalid date format"):
            self.validator.validate_and_normalize("06-2018")
        with pytest.raises(ValidationError, match="Invalid date format"):
            self.validator.validate_and_normalize("June 13, 2018")
        with pytest.raises(ValidationError, match="Invalid date format"):
            self.validator.validate_and_normalize("13.06.2018")


class TestAmountValidator:
    """Test amount validation and normalization"""
    
    def setup_method(self):
        self.validator = AmountValidator()
    
    def test_valid_positive(self):
        assert self.validator.validate_and_normalize("120.50") == "120.50"
        assert self.validator.validate_and_normalize("1000") == "1000"
        assert self.validator.validate_and_normalize("0.99") == "0.99"
    
    def test_valid_negative(self):
        assert self.validator.validate_and_normalize("-120.50") == "-120.50"
        assert self.validator.validate_and_normalize("-1000") == "-1000"
        assert self.validator.validate_and_normalize("-0.99") == "-0.99"
    
    def test_unicode_minus(self):
        assert self.validator.validate_and_normalize("−120.50") == "-120.50"
        assert self.validator.validate_and_normalize("–50") == "-50"
    
    def test_thousands_separator(self):
        assert self.validator.validate_and_normalize("1,234.56") == "1234.56"
        assert self.validator.validate_and_normalize("-1,000,000") == "-1000000"
    
    def test_parentheses_negative(self):
        assert self.validator.validate_and_normalize("(120.50)") == "-120.50"
        assert self.validator.validate_and_normalize("(1000)") == "-1000"
    
    def test_currency_symbols(self):
        assert self.validator.validate_and_normalize("$120.50") == "120.50"
        assert self.validator.validate_and_normalize("£50") == "50"
        assert self.validator.validate_and_normalize("€-30.00") == "-30.00"
    
    def test_empty_amount(self):
        with pytest.raises(ValidationError, match="Amount cannot be empty"):
            self.validator.validate_and_normalize("")
        with pytest.raises(ValidationError, match="Amount cannot be empty"):
            self.validator.validate_and_normalize("  ")
    
    def test_invalid_format(self):
        with pytest.raises(ValidationError, match="Invalid amount format"):
            self.validator.validate_and_normalize("abc")
        with pytest.raises(ValidationError, match="Invalid amount format"):
            self.validator.validate_and_normalize("12.34.56")


class TestDescriptionValidator:
    """Test description validation and normalization"""
    
    def setup_method(self):
        self.validator = DescriptionValidator()
    
    def test_simple_description(self):
        assert self.validator.validate_and_normalize("Monthly subscription") == "Monthly subscription"
        assert self.validator.validate_and_normalize("Payment received") == "Payment received"
    
    def test_whitespace_collapse(self):
        assert self.validator.validate_and_normalize("Multiple   spaces") == "Multiple spaces"
        assert self.validator.validate_and_normalize("  Leading and trailing  ") == "Leading and trailing"
        assert self.validator.validate_and_normalize("Tab\tseparated") == "Tab separated"
    
    def test_newline_removal(self):
        assert self.validator.validate_and_normalize("Line\nbreak") == "Line break"
        assert self.validator.validate_and_normalize("Carriage\rreturn") == "Carriage return"
    
    def test_comma_quoting(self):
        assert self.validator.validate_and_normalize("Item, with comma") == '"Item, with comma"'
        assert self.validator.validate_and_normalize("A, B, C") == '"A, B, C"'
    
    def test_quote_escaping(self):
        assert self.validator.validate_and_normalize('Item "quoted", here') == '"Item ""quoted"", here"'
    
    def test_empty_description(self):
        with pytest.raises(ValidationError, match="Description cannot be empty"):
            self.validator.validate_and_normalize("")
        with pytest.raises(ValidationError, match="Description cannot be empty"):
            self.validator.validate_and_normalize("  ")


class TestRowValidator:
    """Test complete row validation"""
    
    def setup_method(self):
        self.validator = RowValidator()
    
    def test_valid_row(self):
        row = {
            "Date": "13/06/2018",
            "Description": "Monthly subscription",
            "Amount": "-120.50"
        }
        is_valid, error, normalized = self.validator.validate_row(row)
        assert is_valid is True
        assert error is None
        assert normalized == {
            "Date": "13-06-2018",
            "Description": "Monthly subscription",
            "Amount": "-120.50"
        }
    
    def test_row_with_comma_description(self):
        row = {
            "Date": "01-01-2020",
            "Description": "Item, with comma",
            "Amount": "50.00"
        }
        is_valid, error, normalized = self.validator.validate_row(row)
        assert is_valid is True
        assert normalized["Description"] == '"Item, with comma"'
    
    def test_missing_field(self):
        row = {
            "Date": "13-06-2018",
            "Description": "Test"
        }
        is_valid, error, normalized = self.validator.validate_row(row)
        assert is_valid is False
        assert "Missing field: Amount" in error
    
    def test_invalid_date(self):
        row = {
            "Date": "June 13, 2018",
            "Description": "Test",
            "Amount": "100"
        }
        is_valid, error, normalized = self.validator.validate_row(row)
        assert is_valid is False
        assert "Date error" in error
    
    def test_invalid_amount(self):
        row = {
            "Date": "13-06-2018",
            "Description": "Test",
            "Amount": "abc"
        }
        is_valid, error, normalized = self.validator.validate_row(row)
        assert is_valid is False
        assert "Amount error" in error
    
    def test_empty_description(self):
        row = {
            "Date": "13-06-2018",
            "Description": "",
            "Amount": "100"
        }
        is_valid, error, normalized = self.validator.validate_row(row)
        assert is_valid is False
        assert "Description error" in error