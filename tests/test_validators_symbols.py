"""Unit tests for description symbol cleaning"""

import pytest
from bill2csv.validators import DescriptionValidator, ValidationError


class TestDescriptionSymbolCleaning:
    """Test description symbol replacement and normalization"""
    
    def setup_method(self):
        self.validator = DescriptionValidator()
    
    def test_hash_symbol_replacement(self):
        """Test that # symbols are replaced with spaces"""
        assert self.validator.validate_and_normalize("WALMART#1234") == "WALMART 1234"
        assert self.validator.validate_and_normalize("STORE#5678#NYC") == "STORE 5678 NYC"
    
    def test_underscore_replacement(self):
        """Test that underscores are replaced with spaces"""
        assert self.validator.validate_and_normalize("7-ELEVEN_STORE") == "7 ELEVEN STORE"
        assert self.validator.validate_and_normalize("BEST_BUY_ONLINE") == "BEST BUY ONLINE"
    
    def test_multiple_symbols_replacement(self):
        """Test multiple different symbols"""
        assert self.validator.validate_and_normalize("ABC*DEF@GHI") == "ABC DEF GHI"
        assert self.validator.validate_and_normalize("STORE&MORE") == "STORE MORE"
        assert self.validator.validate_and_normalize("ITEM/SERVICE") == "ITEM SERVICE"
    
    def test_preserve_basic_punctuation(self):
        """Test that basic punctuation is preserved"""
        assert self.validator.validate_and_normalize("McDonald's Restaurant") == "McDonald's Restaurant"
        assert self.validator.validate_and_normalize("Store Inc.") == "Store Inc."
        assert self.validator.validate_and_normalize("Item (Sale)") == "Item (Sale)"
    
    def test_complex_cleaning(self):
        """Test complex descriptions with multiple issues"""
        assert self.validator.validate_and_normalize("WALMART#1234***STORE@NYC") == "WALMART 1234 STORE NYC"
        assert self.validator.validate_and_normalize("7-11_#4567/Store") == "7 11 4567 Store"
    
    def test_dash_normalization(self):
        """Test that multiple dashes are replaced with single space"""
        assert self.validator.validate_and_normalize("STORE---LOCATION") == "STORE LOCATION"
        assert self.validator.validate_and_normalize("ITEM--SERVICE") == "ITEM SERVICE"
    
    def test_whitespace_collapse(self):
        """Test that multiple spaces are collapsed"""
        assert self.validator.validate_and_normalize("STORE    #1234    NYC") == "STORE 1234 NYC"
        assert self.validator.validate_and_normalize("  ITEM   SERVICE  ") == "ITEM SERVICE"
    
    def test_comma_quoting_with_symbols(self):
        """Test that cleaned descriptions with commas are quoted"""
        result = self.validator.validate_and_normalize("STORE#1, LOCATION@2")
        assert result == '"STORE 1, LOCATION 2"'
    
    def test_special_characters_in_real_descriptions(self):
        """Test real-world description examples"""
        assert self.validator.validate_and_normalize("AMZ*MKTP US*2Y4T85TN2") == "AMZ MKTP US 2Y4T85TN2"
        assert self.validator.validate_and_normalize("PAYPAL *EBAY_SELLER") == "PAYPAL EBAY SELLER"
        # Note: dots are preserved as they are part of domain names
        assert self.validator.validate_and_normalize("UBER *TRIP-HELP.UBER.COM") == "UBER TRIP HELP.UBER.COM"
        assert self.validator.validate_and_normalize("SQ *COFFEE_SHOP") == "SQ COFFEE SHOP"
    
    def test_bracket_removal(self):
        """Test that brackets are removed"""
        assert self.validator.validate_and_normalize("ITEM[123]") == "ITEM 123"
        assert self.validator.validate_and_normalize("SERVICE{ABC}") == "SERVICE ABC"
        assert self.validator.validate_and_normalize("PRODUCT<XYZ>") == "PRODUCT XYZ"