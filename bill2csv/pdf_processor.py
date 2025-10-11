"""PDF processing using Gemini API"""

from google import genai
from google.genai import types
from google.genai import errors
from pathlib import Path
import time
import os
import random
from datetime import datetime

from . import config


class GeminiProcessor:
    """Process PDF files using Gemini 2.5 Flash API"""

    # Configuration constants from centralized config
    DEFAULT_MODEL = config.DEFAULT_MODEL
    MAX_POLLING_ATTEMPTS = config.MAX_POLLING_ATTEMPTS
    POLLING_INTERVAL = config.POLLING_INTERVAL

    # Retry configuration from centralized config
    MAX_RETRIES = config.MAX_RETRIES
    INITIAL_RETRY_DELAY = config.INITIAL_RETRY_DELAY
    MAX_RETRY_DELAY = config.MAX_RETRY_DELAY
    RETRY_BACKOFF_FACTOR = config.RETRY_BACKOFF_FACTOR
    
    # Cache for categories
    _categories_content = None
    _categories_file = None
    
    # Prompt v4 with Payee and hierarchical Category columns
    PROMPT_V2 = """You read the attached multi-page bill PDF and extract ONLY the EXPENSE DETAIL TABLE(S).
Ignore dashboards, charts/graphs, summaries, totals, advertisements, and cover pages.

Output ONLY raw CSV with this exact header:
Date,Description,Payee,Amount,Category

Mapping rules:
- Identify rows representing itemized expenses/charges or payments/credits.
- Column mapping:
  * Date: transaction date preferred (when the purchase/transaction occurred), otherwise use posting date
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
- Payee: extract the merchant/vendor name from description, preserving original language
  * Keep the original language/script from the description (Chinese, Japanese, etc.)
  * Remove store numbers, transaction codes, and extra details
  * Examples:
    - "WALMART#1234*STORE" → "Walmart"
    - "7-ELEVEN_STORE#567" → "7-Eleven"
    - "星巴克咖啡#12345" → "星巴克咖啡"
    - "麥當勞 STORE#567" → "麥當勞"
    - "セブンイレブン#1234" → "セブンイレブン"
    - "AMZ*MKTP US*2Y4T85TN2" → "Amazon Marketplace"
    - "PAYPAL *EBAY_SELLER" → "PayPal"
    - "TST* DOORDASH" → "DoorDash"
- Amount: signed decimal with '.' decimal separator; no thousands separators
  * Outflows/charges: NEGATIVE (e.g., -120.50)
  * Inflows/payments/credits/refunds: POSITIVE (e.g., 120.50)
- Category: Use ONLY the categories from the provided list below. Use hierarchical format with > separator when subcategories exist

Scope:
- Extract ALL rows from the expense detail table(s) across ALL pages.
- If multiple detail tables exist, include them all (one row per transaction).
- If the bill contains NO itemized rows, output ONE row using the total due as a charge (negative).

Constraints:
- If a field is unknown, leave it empty (no N/A).
- Output only CSV text. No explanations, no markdown, no code fences, no extra columns.

Header example:
Date,Description,Payee,Amount,Category"""

    def __init__(self, api_key: str, model: str = None, debug: bool = False):
        """
        Initialize Gemini processor

        Args:
            api_key: Gemini API key
            model: Model name (defaults to value from config.DEFAULT_MODEL)
            debug: Enable debug logging
        """
        self.api_key = api_key
        self.model_name = model or self.DEFAULT_MODEL
        self.debug = debug
        
        # Initialize the client with the new SDK
        self.client = genai.Client(api_key=api_key)
        
        # Load expense categories for context
        self._load_expense_categories()
    
    def _load_expense_categories(self):
        """Load expense categories from markdown file for API context"""
        if self._categories_content is not None:
            return  # Already loaded
        
        # Look for expense_categories.md in various locations
        possible_paths = [
            Path(os.getcwd()) / "expense_categories.md",
            Path.home() / ".bill2csv" / "expense_categories.md",
        ]
        
        for path in possible_paths:
            if path.exists():
                self._categories_file = path
                with open(path, 'r', encoding='utf-8') as f:
                    self._categories_content = f.read()
                break
        
        # If no file found, use a minimal default
        if self._categories_content is None:
            self._categories_content = """# Expense Categories
## Personal Expenses
- Food & Dining
- Transportation
- Shopping
- Entertainment
- Health & Wellness

## Home & Utilities
- Housing
- Utilities
- Maintenance

## Financial
- Banking
- Credit Cards
- Insurance

## Other
- Uncategorized
- Transfers"""
    
    def _write_debug_response(self, pdf_path: str, response_text: str):
        """Write raw LLM response to debug file for analysis"""
        try:
            # Create debug filename with timestamp
            pdf_name = Path(pdf_path).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_filename = f"{pdf_name}_llm_response_{timestamp}.txt"
            
            # Write to same directory as input PDF
            debug_path = Path(pdf_path).parent / debug_filename
            
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"LLM Response Debug Log\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"Model: {self.model_name}\n")
                f.write(f"PDF: {pdf_path}\n")
                f.write("=" * 80 + "\n\n")
                f.write("RAW RESPONSE:\n")
                f.write("-" * 40 + "\n")
                f.write(response_text)
                f.write("\n" + "-" * 40 + "\n")
                f.write(f"\nTotal characters: {len(response_text)}\n")
                f.write(f"Total lines: {len(response_text.splitlines())}\n")
                
                # Check for common issues
                f.write("\nQUICK ANALYSIS:\n")
                if "```" in response_text:
                    f.write("- Contains code fence markers (```)\n")
                if response_text.count(",") < 10:
                    f.write("- WARNING: Very few commas detected, might not be CSV\n")
                if "Date,Description" in response_text:
                    f.write("- Header line detected\n")
                if "Category" in response_text:
                    f.write("- Category column detected\n")
                if "Payee" in response_text:
                    f.write("- Payee column detected\n")
                
            print(f"Debug: LLM response written to {debug_path}")
            
        except Exception as e:
            print(f"Warning: Could not write debug file: {e}")
    
    def process_pdf(self, pdf_path: str) -> str:
        """
        Process PDF file and extract CSV data
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Raw CSV response from Gemini
            
        Raises:
            TimeoutError: If file processing times out
            ValueError: If file upload fails
            Exception: If API call fails
        """
        pdf_file = None
        
        try:
            # Upload the PDF file using new SDK
            pdf_file = self.client.files.upload(file=pdf_path)
            
            # With new SDK, files are typically ready immediately after upload
            # But we can add a small delay to ensure processing
            time.sleep(1.0)
            
            # Combine prompt with categories for clearer context
            full_prompt = (
                self.PROMPT_V2 + 
                "\n\n## Available Categories\n" +
                "Use ONLY these categories for the Category column:\n\n" +
                self._categories_content
            )
            
            # Use new SDK pattern for content generation with retry logic
            retry_count = 0
            retry_delay = self.INITIAL_RETRY_DELAY
            response = None
            last_error = None
            
            while retry_count <= self.MAX_RETRIES:
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=[
                            full_prompt,  # Text instruction
                            pdf_file,     # Uploaded file
                        ],
                        config=types.GenerateContentConfig(
                            temperature=config.TEMPERATURE,
                            max_output_tokens=config.MAX_OUTPUT_TOKENS,
                            candidate_count=1,
                            safety_settings=[
                                types.SafetySetting(
                                    category="HARM_CATEGORY_HARASSMENT",
                                    threshold="BLOCK_NONE"
                                ),
                                types.SafetySetting(
                                    category="HARM_CATEGORY_HATE_SPEECH",
                                    threshold="BLOCK_NONE"
                                ),
                                types.SafetySetting(
                                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                                    threshold="BLOCK_NONE"
                                ),
                                types.SafetySetting(
                                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                                    threshold="BLOCK_NONE"
                                ),
                            ]
                        )
                    )
                    # Success! Break out of retry loop
                    break
                    
                except errors.APIError as e:
                    last_error = e
                    
                    # Check if it's a retryable error (503, 429, 500, 502)
                    if hasattr(e, 'code') and e.code in [503, 429, 500, 502]:
                        if retry_count < self.MAX_RETRIES:
                            # Add jitter to prevent thundering herd
                            jittered_delay = retry_delay + random.uniform(0, 1)
                            
                            print(f"API temporarily unavailable (error {e.code}). "
                                  f"Retrying in {jittered_delay:.1f} seconds... "
                                  f"(attempt {retry_count + 1}/{self.MAX_RETRIES})")
                            
                            time.sleep(jittered_delay)
                            
                            # Exponential backoff with cap
                            retry_delay = min(retry_delay * self.RETRY_BACKOFF_FACTOR, self.MAX_RETRY_DELAY)
                            retry_count += 1
                        else:
                            # Max retries exceeded
                            self.client.files.delete(name=pdf_file.name)
                            raise ValueError(
                                f"API temporarily unavailable after {self.MAX_RETRIES} retries. "
                                f"Error: {str(e)}. Please try again in a few minutes."
                            )
                    else:
                        # Non-retryable error, raise immediately
                        self.client.files.delete(name=pdf_file.name)
                        raise
                        
                except Exception as e:
                    # Unexpected error, don't retry
                    self.client.files.delete(name=pdf_file.name)
                    raise
            
            # Check if we got a response
            if response is None:
                self.client.files.delete(name=pdf_file.name)
                raise ValueError(f"Failed to get response after retries. Last error: {last_error}")
            
            # Check if response was blocked or has no valid candidates
            if not response.candidates:
                # Clean up file before raising error
                self.client.files.delete(name=pdf_file.name)
                raise ValueError("API response was blocked or empty. No candidates returned.")
            
            # Check the first candidate for finish_reason
            candidate = response.candidates[0]
            
            # Check finish_reason - handle both numeric and enum values
            if hasattr(candidate, 'finish_reason'):
                finish_reason = candidate.finish_reason
                
                # Convert enum to string if needed
                if hasattr(finish_reason, 'name'):
                    finish_reason_name = finish_reason.name
                    finish_reason_value = finish_reason.value if hasattr(finish_reason, 'value') else None
                else:
                    finish_reason_name = str(finish_reason)
                    finish_reason_value = finish_reason
                
                # Check if it's not a normal completion
                if finish_reason_name not in ['STOP', '1', 1]:
                    # Special handling for MAX_TOKENS
                    if 'MAX_TOKENS' in finish_reason_name:
                        # For MAX_TOKENS, we might have partial content - try to use it
                        if candidate.content and candidate.content.parts:
                            # Log warning but try to continue with partial response
                            print("Warning: Response hit token limit. Results may be incomplete.")
                            # Don't raise error, try to return partial content
                        else:
                            # No content at all, must raise error
                            self.client.files.delete(name=pdf_file.name)
                            raise ValueError(
                                "Response exceeded token limit with no content. "
                                "The PDF may be too large or complex. "
                                "Try processing a smaller section or simpler document."
                            )
                    else:
                        # Other finish reasons are errors
                        self.client.files.delete(name=pdf_file.name)
                        
                        reason_map = {
                            'SAFETY': "Content was blocked by safety filters",
                            'RECITATION': "Response resembles training data too closely",
                            'OTHER': "Response blocked for other reasons",
                            'BLOCKLIST': "Content blocked by blocklist",
                            'PROHIBITED_CONTENT': "Content contains prohibited material",
                            'SPII': "Content contains sensitive personally identifiable information"
                        }
                        
                        reason = reason_map.get(finish_reason_name, f"Unknown reason: {finish_reason_name}")
                        
                        # Try to get safety ratings if available
                        safety_info = ""
                        if hasattr(candidate, 'safety_ratings'):
                            safety_info = f" Safety ratings: {candidate.safety_ratings}"
                        
                        raise ValueError(f"API response was blocked. Reason: {reason}.{safety_info}")
            
            # Check if the candidate has valid content
            if not candidate.content or not candidate.content.parts:
                # Clean up file before raising error
                self.client.files.delete(name=pdf_file.name)
                raise ValueError("API response has no valid content parts.")
            
            # Delete the uploaded file
            self.client.files.delete(name=pdf_file.name)
            
            # Get the response text
            response_text = response.text
            
            # Debug logging - write raw LLM response to file
            if self.debug or os.environ.get('BILL2CSV_DEBUG'):
                self._write_debug_response(pdf_path, response_text)
            
            # Return the response
            return response_text
            
        except TimeoutError:
            # Clean up and re-raise timeout error
            if pdf_file:
                try:
                    self.client.files.delete(name=pdf_file.name)
                except:
                    pass
            raise
            
        except ValueError:
            # Clean up and re-raise value error
            if pdf_file:
                try:
                    self.client.files.delete(name=pdf_file.name)
                except:
                    pass
            raise
            
        except Exception as e:
            # Clean up file on any error
            if pdf_file:
                try:
                    self.client.files.delete(name=pdf_file.name)
                except:
                    pass
            
            # Provide more specific error messages
            error_msg = str(e).lower()
            if "not found" in error_msg:
                raise ValueError(f"File not found or inaccessible: {pdf_path}")
            elif "authentication" in error_msg or "api key" in error_msg:
                raise ValueError("API authentication failed. Please check your API key.")
            elif "quota" in error_msg or "rate" in error_msg:
                raise ValueError("API rate limit exceeded. Please wait and try again.")
            else:
                raise Exception(f"Gemini API error: {str(e)}")