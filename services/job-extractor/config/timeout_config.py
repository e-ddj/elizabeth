"""
Timeout configuration for the job extractor service.
"""

import os

# HTTP request timeouts (reduced for speed)
HTTP_REQUEST_TIMEOUT = int(os.getenv("HTTP_REQUEST_TIMEOUT", "5"))  # seconds

# Selenium WebDriver timeouts (reduced for speed)
SELENIUM_PAGE_LOAD_TIMEOUT = int(os.getenv("SELENIUM_PAGE_LOAD_TIMEOUT", "10"))  # seconds

# OpenAI API timeout (reduced for speed)
OPENAI_API_TIMEOUT = float(os.getenv("OPENAI_API_TIMEOUT", "30.0"))  # seconds

# Gunicorn worker timeout (kept high for ALB compatibility)
GUNICORN_TIMEOUT = int(os.getenv("GUNICORN_TIMEOUT", "1800"))  # seconds

# Content processing limits (aggressively reduced for speed)
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "8000"))  # characters

# Frontend should set their timeout higher than GUNICORN_TIMEOUT
RECOMMENDED_FRONTEND_TIMEOUT = GUNICORN_TIMEOUT + 30  # Add 30 seconds buffer 