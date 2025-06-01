"""
Timeout configuration for the job extractor service.
"""

import os

# HTTP request timeouts
HTTP_REQUEST_TIMEOUT = int(os.getenv("HTTP_REQUEST_TIMEOUT", "30"))  # seconds

# Selenium WebDriver timeouts
SELENIUM_PAGE_LOAD_TIMEOUT = int(os.getenv("SELENIUM_PAGE_LOAD_TIMEOUT", "30"))  # seconds

# OpenAI API timeout
OPENAI_API_TIMEOUT = float(os.getenv("OPENAI_API_TIMEOUT", "60.0"))  # seconds

# Gunicorn worker timeout (should be higher than the longest expected request)
GUNICORN_TIMEOUT = int(os.getenv("GUNICORN_TIMEOUT", "120"))  # seconds

# Content processing limits
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "50000"))  # characters

# Frontend should set their timeout higher than GUNICORN_TIMEOUT
RECOMMENDED_FRONTEND_TIMEOUT = GUNICORN_TIMEOUT + 30  # Add 30 seconds buffer 