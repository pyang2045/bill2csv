"""Unit tests for PayeeValidator"""

import pytest
from bill2csv.validators import PayeeValidator


class TestPayeeValidator:
    """Test payee extraction and normalization"""
    
    def setup_method(self):
        self.validator = PayeeValidator()
    
    def test_empty_payee(self):
        """Test that empty payee returns empty string"""
        assert self.validator.validate_and_normalize("") == ""
        assert self.validator.validate_and_normalize("  ") == ""
        assert self.validator.validate_and_normalize(None) == ""
    
    def test_simple_payee(self):
        """Test simple payee names"""
        assert self.validator.validate_and_normalize("Starbucks") == "Starbucks"
        assert self.validator.validate_and_normalize("Target") == "Target"
        assert self.validator.validate_and_normalize("Costco") == "Costco"
    
    def test_store_number_removal(self):
        """Test removal of store numbers"""
        assert self.validator.validate_and_normalize("Starbucks #1234") == "Starbucks"
        assert self.validator.validate_and_normalize("WALMART #567") == "Walmart"
        assert self.validator.validate_and_normalize("Target Store #890") == "Target"
    
    def test_transaction_id_removal(self):
        """Test removal of transaction IDs"""
        assert self.validator.validate_and_normalize("Amazon *ABC123") == "Amazon"
        assert self.validator.validate_and_normalize("Walmart *XYZ789") == "Walmart"
    
    def test_prefix_removal(self):
        """Test removal of common prefixes"""
        assert self.validator.validate_and_normalize("TST* DOORDASH") == "DoorDash"
        assert self.validator.validate_and_normalize("SQ *COFFEE SHOP") == "COFFEE SHOP"
        assert self.validator.validate_and_normalize("SP * UBER") == "Uber"
    
    def test_known_company_normalization(self):
        """Test normalization of known companies"""
        assert self.validator.validate_and_normalize("walmart") == "Walmart"
        assert self.validator.validate_and_normalize("WALMART") == "Walmart"
        assert self.validator.validate_and_normalize("amazon marketplace") == "Amazon"
        assert self.validator.validate_and_normalize("paypal payment") == "PayPal"
        assert self.validator.validate_and_normalize("7-eleven") == "7-Eleven"
        assert self.validator.validate_and_normalize("7 eleven") == "7-Eleven"
        assert self.validator.validate_and_normalize("mcdonalds") == "McDonald's"
    
    def test_complex_payee_extraction(self):
        """Test complex payee extraction scenarios"""
        assert self.validator.validate_and_normalize("TST* DOORDASH #1234") == "DoorDash"
        assert self.validator.validate_and_normalize("SQ *STARBUCKS STORE #567") == "Starbucks"
        assert self.validator.validate_and_normalize("WALMART #123 *STORE") == "Walmart"
    
    def test_whitespace_normalization(self):
        """Test whitespace normalization"""
        assert self.validator.validate_and_normalize("  Starbucks  ") == "Starbucks"
        assert self.validator.validate_and_normalize("Target   Store") == "Target"
        assert self.validator.validate_and_normalize("Best    Buy") == "Best Buy"
    
    def test_comma_quoting(self):
        """Test that payees with commas are quoted"""
        assert self.validator.validate_and_normalize("Smith, John Store") == '"Smith, John Store"'
        assert self.validator.validate_and_normalize("ABC, Inc.") == '"ABC, Inc."'
    
    def test_quote_escaping(self):
        """Test that existing quotes are escaped when quoting"""
        assert self.validator.validate_and_normalize('Store "ABC", Inc.') == '"Store ""ABC"", Inc."'