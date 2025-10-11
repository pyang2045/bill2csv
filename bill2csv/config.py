"""Centralized configuration for bill2csv"""

# Model Configuration
DEFAULT_MODEL = 'gemini-2.5-flash'  # Latest stable Flash model with thinking capabilities
MODEL_DESCRIPTION = "Gemini 2.5 Flash"

# API Configuration
MAX_OUTPUT_TOKENS = 65536  # Maximum tokens for model output (official limit for gemini-2.5-flash)
TEMPERATURE = 0.1  # Low temperature for deterministic output

# Retry Configuration
MAX_RETRIES = 3  # Maximum number of retry attempts
INITIAL_RETRY_DELAY = 2  # Initial delay in seconds
MAX_RETRY_DELAY = 32  # Maximum delay in seconds
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff factor

# File Processing Configuration
MAX_POLLING_ATTEMPTS = 60  # 30 seconds timeout (60 * 0.5s)
POLLING_INTERVAL = 0.5  # seconds
