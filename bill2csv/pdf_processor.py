"""PDF processing using Gemini API"""

import google.generativeai as genai
from pathlib import Path
import time


class GeminiProcessor:
    """Process PDF files using Gemini 2.5 Flash API"""
    
    # Prompt v4 with Payee and hierarchical Category columns
    PROMPT_V2 = """You read the attached multi-page bill PDF and extract ONLY the EXPENSE DETAIL TABLE(S).
Ignore dashboards, charts/graphs, summaries, totals, advertisements, and cover pages.

Output ONLY raw CSV with this exact header:
Date,Description,Payee,Amount,Category

Mapping rules:
- Identify rows representing itemized expenses/charges or payments/credits.
- Column mapping:
  * Date: posting date or transaction date for each row
  * Description: the full transaction description/details as shown in the bill
  * Payee: extract the merchant/vendor/payee name from the description (clean, simplified name)
  * Amount: numeric value for the row
  * Category: intelligently categorize based on the description and context

Normalization:
- Date: DD-MM-YYYY (numeric day-month-year, e.g., 13-06-2018)
- Description: clean text with spaces instead of symbols; one line; if it contains commas, quote the field
  * Replace symbols like *, #, @, &, /, \\, |, <, >, ~, `, ^, _, +, =, [, ], {, } with spaces
  * Keep letters, numbers, and basic punctuation (. , ; : ' " ( ))
  * Example: "WALMART#1234*STORE" becomes "WALMART 1234 STORE", "7-ELEVEN_STORE" becomes "7 ELEVEN STORE"
- Payee: extract and simplify the merchant/vendor name from description
  * Remove store numbers, transaction codes, and extra details
  * Examples:
    - "WALMART#1234*STORE" → "Walmart"
    - "7-ELEVEN_STORE#567" → "7-Eleven"
    - "AMZ*MKTP US*2Y4T85TN2" → "Amazon Marketplace"
    - "PAYPAL *EBAY_SELLER" → "PayPal"
    - "STARBUCKS STORE #12345" → "Starbucks"
    - "TST* DOORDASH" → "DoorDash"
- Amount: signed decimal with '.' decimal separator; no thousands separators
  * Outflows/charges: NEGATIVE (e.g., -120.50)
  * Inflows/payments/credits/refunds: POSITIVE (e.g., 120.50)
- Category: Use hierarchical categorization with > separator. Examples:
  * For main categories: "Food & Dining", "Transportation", "Shopping"
  * For sub-categories: "Food & Dining > Restaurants", "Transportation > Gas & Fuel"
  * Common categories include:
    - Personal: Food & Dining, Transportation, Shopping, Entertainment, Health & Wellness
    - Home: Housing, Utilities, Maintenance
    - Financial: Banking, Credit Cards, Insurance
    - Business: Office, Professional, Marketing
    - Income: Salary, Refunds, Credits
    - Other: Uncategorized, Cash Withdrawal, Transfers

Scope:
- Extract ALL rows from the expense detail table(s) across ALL pages.
- If multiple detail tables exist, include them all (one row per transaction).
- If the bill contains NO itemized rows, output ONE row using the total due as a charge (negative).

Constraints:
- If a field is unknown, leave it empty (no N/A).
- Output only CSV text. No explanations, no markdown, no code fences, no extra columns.

Header example:
Date,Description,Payee,Amount,Category"""

    def __init__(self, api_key: str):
        """
        Initialize Gemini processor
        
        Args:
            api_key: Gemini API key
        """
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def process_pdf(self, pdf_path: str) -> str:
        """
        Process PDF file and extract CSV data
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Raw CSV response from Gemini
            
        Raises:
            Exception: If API call fails
        """
        # Upload the PDF file
        pdf_file = genai.upload_file(pdf_path, mime_type="application/pdf")
        
        # Wait for file to be processed
        while pdf_file.state.name == "PROCESSING":
            time.sleep(0.5)
            pdf_file = genai.get_file(pdf_file.name)
        
        if pdf_file.state.name != "ACTIVE":
            raise Exception(f"File upload failed with state: {pdf_file.state.name}")
        
        try:
            # Generate content with the prompt
            response = self.model.generate_content(
                [pdf_file, self.PROMPT_V2],
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 8192,
                }
            )
            
            # Delete the uploaded file
            genai.delete_file(pdf_file.name)
            
            return response.text
            
        except Exception as e:
            # Clean up file on error
            try:
                genai.delete_file(pdf_file.name)
            except:
                pass
            raise Exception(f"Gemini API error: {str(e)}")