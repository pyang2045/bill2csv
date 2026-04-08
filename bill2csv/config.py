"""Centralized configuration for bill2csv"""

# Model Configuration
DEFAULT_MODEL = 'gemini-3.1-pro-preview'  # Gemini 3.1 Pro preview model
MODEL_DESCRIPTION = "Gemini 3.1 Pro Preview"

# API Configuration
MAX_OUTPUT_TOKENS = 65536  # Maximum tokens for model output
TEMPERATURE = 0.1  # Low temperature for deterministic output

# Retry Configuration
MAX_RETRIES = 3  # Maximum number of retry attempts
INITIAL_RETRY_DELAY = 2  # Initial delay in seconds
MAX_RETRY_DELAY = 32  # Maximum delay in seconds
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff factor

# HTTP Timeout Configuration
HTTP_TIMEOUT_MS = 300_000  # 5 minutes in milliseconds for API requests

# File Processing Configuration
MAX_POLLING_ATTEMPTS = 60  # 30 seconds timeout (60 * 0.5s)
POLLING_INTERVAL = 0.5  # seconds
