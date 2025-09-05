"""Unit tests for CSV cleaner module"""

import pytest
from bill2csv.csv_cleaner import CSVCleaner


class TestCSVCleaner:
    """Test CSV response cleaning and parsing"""
    
    def setup_method(self):
        self.cleaner = CSVCleaner()
    
    def test_clean_simple_csv(self):
        raw = """Date,Description,Amount
13-06-2018,Monthly subscription,-120.50
14-06-2018,Payment received,500.00"""
        
        cleaned = self.cleaner.clean_response(raw)
        assert cleaned == """Date,Description,Amount
13-06-2018,Monthly subscription,-120.50
14-06-2018,Payment received,500.00"""
    
    def test_clean_with_markdown_fences(self):
        raw = """Here is the CSV output:
```csv
Date,Description,Amount
13-06-2018,Monthly subscription,-120.50
14-06-2018,Payment received,500.00
```
That's all the data."""
        
        cleaned = self.cleaner.clean_response(raw)
        assert cleaned.startswith("Date,Description,Amount")
        assert "13-06-2018,Monthly subscription,-120.50" in cleaned
        assert "```" not in cleaned
    
    def test_clean_with_plain_fences(self):
        raw = """```
Date,Description,Amount
13-06-2018,Test,-100
```"""
        
        cleaned = self.cleaner.clean_response(raw)
        assert cleaned == """Date,Description,Amount
13-06-2018,Test,-100"""
    
    def test_clean_with_extra_text(self):
        raw = """I've extracted the following data:

Date,Description,Amount
13-06-2018,Item 1,-50
14-06-2018,Item 2,-75

Total: -125"""
        
        cleaned = self.cleaner.clean_response(raw)
        assert cleaned == """Date,Description,Amount
13-06-2018,Item 1,-50
14-06-2018,Item 2,-75"""
    
    def test_parse_csv(self):
        csv_text = """Date,Description,Amount
13-06-2018,Monthly subscription,-120.50
14-06-2018,Payment received,500.00"""
        
        rows = self.cleaner.parse_csv(csv_text)
        assert len(rows) == 2
        assert rows[0] == {
            "Date": "13-06-2018",
            "Description": "Monthly subscription",
            "Amount": "-120.50"
        }
        assert rows[1] == {
            "Date": "14-06-2018",
            "Description": "Payment received",
            "Amount": "500.00"
        }
    
    def test_parse_csv_with_quotes(self):
        csv_text = """Date,Description,Amount
13-06-2018,"Item, with comma",-50
14-06-2018,"Another ""quoted"" item",100"""
        
        rows = self.cleaner.parse_csv(csv_text)
        assert len(rows) == 2
        assert rows[0]["Description"] == "Item, with comma"
        assert rows[1]["Description"] == 'Another "quoted" item'
    
    def test_clean_and_parse_combined(self):
        raw = """```csv
Date,Description,Amount
13-06-2018,Test item,-25.50
```"""
        
        rows = self.cleaner.clean_and_parse(raw)
        assert len(rows) == 1
        assert rows[0] == {
            "Date": "13-06-2018",
            "Description": "Test item",
            "Amount": "-25.50"
        }
    
    def test_empty_response_error(self):
        with pytest.raises(ValueError, match="Empty response"):
            self.cleaner.clean_response("")
    
    def test_no_csv_content_error(self):
        raw = "This is just text with no CSV data"
        with pytest.raises(ValueError, match="No valid CSV content"):
            self.cleaner.clean_response(raw)
    
    def test_case_insensitive_header(self):
        raw = """date,description,amount
13-06-2018,Test,-100"""
        
        cleaned = self.cleaner.clean_response(raw)
        assert cleaned.startswith("Date,Description,Amount")