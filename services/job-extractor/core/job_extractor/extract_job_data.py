"""
Core functionality for extracting structured data from job posting HTML/text.
"""

import json
import logging
from typing import Dict, Any, Optional, BinaryIO, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
# Removed unused imports for performance
import os
import io
from pathlib import Path

# Conditional imports for browser automation
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    _HAS_SELENIUM = True
except ImportError:
    _HAS_SELENIUM = False
    logger = logging.getLogger(__name__)
    logger.warning("Selenium or undetected_chromedriver not available - browser emulation will be disabled")

# Global driver instance for reuse (much faster than creating new instances)
_global_driver = None

# Import document processing utilities
from utils.files.doc_converters import extract_text_from_document, _HAS_PYMUPDF, _HAS_DOCX

from models.job_extractor.model import process_job_posting
from models.job_extractor.enrich_job import enrich_job_field
from config.log_config import get_logger
from config.timeout_config import HTTP_REQUEST_TIMEOUT, SELENIUM_PAGE_LOAD_TIMEOUT, MAX_CONTENT_LENGTH

logger = get_logger()

# Create a session with retry logic and browser-like headers
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=0.3,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Set browser-like headers
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1"
})

def get_or_create_driver():
    """
    Get or create a global Chrome driver instance for reuse (much faster than creating new instances).
    
    Returns:
        Reusable Chrome driver instance optimized for speed
    """
    global _global_driver
    
    if not _HAS_SELENIUM:
        raise ImportError("Selenium or undetected_chromedriver is not installed")
    
    # Return existing driver if available and still functional
    if _global_driver is not None:
        try:
            # Quick test to see if driver is still alive
            _global_driver.current_url
            return _global_driver
        except Exception:
            # Driver is dead, create a new one
            _global_driver = None
    
    # Create new optimized driver
    options = uc.ChromeOptions()
    # Ultra-minimal configuration for maximum speed
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--memory-pressure-off')  # Prevent Chrome from throttling due to low memory
    options.add_argument('--max_old_space_size=512')  # Limit V8 heap for container
    options.add_argument('--disable-blink-features=AutomationControlled')  # Hide automation
    options.add_argument('--disable-features=TranslateUI')  # Disable translate
    options.add_argument('--disable-ipc-flooding-protection')  # Better performance in containers
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280,720')  # Standard size for proper rendering
    options.add_argument('--disable-images')
    # Enable JavaScript as many job sites require it for content rendering
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-logging')
    options.add_argument('--silent')
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-hang-monitor')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-sync')
    options.add_argument('--metrics-recording-only')
    options.add_argument('--no-zygote')  # Faster startup
    
    # Disable automation features for speed  
    options.add_argument('--disable-automation')
    
    # Use Chromium binary if available
    if os.environ.get('CHROME_BIN'):
        options.binary_location = os.environ['CHROME_BIN']
    
    # Simple user agent
    options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
    
    try:
        driver_path = os.environ.get('CHROMEDRIVER_PATH')
        if driver_path:
            _global_driver = uc.Chrome(options=options, driver_executable_path=driver_path)
        else:
            _global_driver = uc.Chrome(options=options)
        
        # Set reasonable timeouts balancing speed and reliability
        _global_driver.set_page_load_timeout(60)  # Max 60 seconds to load for complex JS sites
        _global_driver.implicitly_wait(10)  # Max 10 seconds to find elements
        
        return _global_driver
    except Exception as e:
        logger.error(f"Failed to create Chrome driver: {e}")
        raise

def fetch_page(url: str) -> str:
    """
    Fetch HTML content from a URL using optimized browser emulation with driver reuse.
    
    Args:
        url: URL to fetch
        
    Returns:
        HTML content as string
        
    Raises:
        ValueError: If the URL is invalid or request fails
    """
    # Try regular requests first (fastest option)
    try:
        response = session.get(url, timeout=5)  # Shorter timeout for speed
        if response.status_code == 200 and len(response.text) > 1000:  # Basic content check
            return response.text
    except Exception:
        pass  # Fail silently and try browser
    
    # If Selenium is not available, return error
    if not _HAS_SELENIUM:
        raise ValueError(f"Failed to fetch content from {url} - browser emulation not available")
    
    # Use reusable browser instance (much faster)
    logger.info("Using browser emulation")
    try:
        driver = get_or_create_driver()
        
        # Navigate and get content quickly
        driver.get(url)
        
        # Wait for page to be ready with JavaScript content
        try:
            # For JobStreet, wait for specific job content elements
            if "jobstreet" in url.lower():
                try:
                    # Wait for job title or content wrapper to be present
                    WebDriverWait(driver, 20).until(
                        lambda d: d.find_elements(By.CLASS_NAME, "job-title") or 
                                 d.find_elements(By.ID, "job-detail") or
                                 d.find_elements(By.CLASS_NAME, "job-description") or
                                 len(d.page_source) > 10000
                    )
                except:
                    pass  # Continue with what we have
            else:
                # Generic wait for other sites
                WebDriverWait(driver, 20).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            
            # Small additional wait for AJAX content
            driver.implicitly_wait(3)
            
        except TimeoutException:
            logger.warning("Page load timeout - proceeding with available content")
        
        html_content = driver.page_source
        
        if len(html_content) < 500:  # Minimal content check
            raise ValueError(f"Insufficient content received from {url}")
            
        return html_content
        
    except Exception as e:
        # If driver fails, create a new one and try once more
        global _global_driver
        if _global_driver:
            try:
                _global_driver.quit()
            except:
                pass
            _global_driver = None
            
        error_msg = f"Browser emulation failed for {url}: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

def extract_job_data(job_url: str) -> Dict[str, Any]:
    """
    Extract structured data from a job posting URL.
    
    Args:
        job_url: URL of the job posting
        
    Returns:
        Dictionary containing structured job data
        
    Raises:
        ValueError: If the URL is invalid or job data extraction fails
    """
    logger.info(f"Starting job data extraction for URL: {job_url}")
    
    # Validate URL
    if not job_url.startswith(("http://", "https://")):
        error_msg = "Invalid URL format - must start with http:// or https://"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        # Fetch job posting HTML
        html_content = fetch_page(job_url)
        logger.info(f"Successfully fetched HTML content from URL (length: {len(html_content)} characters)")
        
        # Clean and optimize the HTML content for processing
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unnecessary elements to reduce content size
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            element.decompose()
        
        # Get text content with some structure preserved
        cleaned_content = soup.get_text(separator='\n', strip=True)
        
        # Limit content size to prevent excessive processing time
        if len(cleaned_content) > MAX_CONTENT_LENGTH:
            cleaned_content = cleaned_content[:MAX_CONTENT_LENGTH] + "\n[Content truncated for processing efficiency]"
            logger.info(f"Content truncated to {MAX_CONTENT_LENGTH} characters for processing efficiency")
        
        logger.info(f"Processed content length: {len(cleaned_content)} characters")
        
        # Process the job posting through the AI model with aggressive content limits
        if len(cleaned_content) > 8000:  # Even more aggressive limit
            cleaned_content = cleaned_content[:8000] + "\n[Content truncated for speed]"
            
        job_data = process_job_posting(cleaned_content)
        
        if not job_data:
            error_msg = "Failed to extract job data - no data returned from model"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        logger.info("Successfully extracted structured job data")
        return job_data
        
    except ValueError as e:
        # Re-raise ValueError as is since it's already properly formatted
        raise
    except Exception as e:
        error_msg = f"Error processing job posting: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise

def extract_text_from_file(file_bytes: bytes, file_extension: str) -> str:
    """
    Extract text content from a file based on its extension.
    
    Args:
        file_bytes: The raw bytes of the file
        file_extension: The file extension (e.g., ".pdf", ".docx")
        
    Returns:
        Extracted text content
        
    Raises:
        ValueError: If text extraction fails or the file format is unsupported
    """
    logger.info(f"Extracting text from file with extension: {file_extension}")
    
    try:
        # Create a BytesIO object from the file bytes
        file_io = io.BytesIO(file_bytes)
        
        # Log file details
        logger.info(f"Processing file: extension={file_extension}, size={len(file_bytes)} bytes")
        
        # Use the doc_converters utility to extract text
        text_content, file_type = extract_text_from_document(file_io, f"file{file_extension}")
        logger.info(f"Successfully extracted text from {file_type} file (length: {len(text_content)} characters)")
        
        # Log if vision API was used
        if len(text_content) > 0:
            logger.info(f"Text extraction successful - first 100 chars: {text_content[:100]}...")
        
        return text_content
        
    except ValueError as e:
        # Re-raise ValueError with the original error message
        error_msg = str(e)
        logger.error(f"ValueError extracting text from file: {error_msg}")
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Error extracting text from file: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg)

def extract_job_data_from_file(file_bytes: bytes, file_extension: str) -> Dict[str, Any]:
    """
    Extract structured job data from an uploaded file.
    
    Args:
        file_bytes: The raw bytes of the uploaded file
        file_extension: The file extension (e.g., ".pdf", ".docx")
        
    Returns:
        Dictionary containing structured job data
        
    Raises:
        ValueError: If text extraction fails or job data extraction fails
    """
    logger.info(f"Starting job data extraction from file with extension: {file_extension}")
    
    try:
        # Extract text from the file
        text_content = extract_text_from_file(file_bytes, file_extension)
        logger.info(f"Successfully extracted text content from file (length: {len(text_content)} characters)")
        
        if not text_content.strip():
            error_msg = "Failed to extract text from file - empty content"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Process the text content through the AI model
        job_data = process_job_posting(text_content)
        
        if not job_data:
            error_msg = "Failed to extract job data - no data returned from model"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        logger.info("Successfully extracted structured job data from file")
        return job_data
        
    except ValueError as e:
        # Re-raise ValueError as is since it's already properly formatted
        raise
    except Exception as e:
        error_msg = f"Error processing job posting from file: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise

def cleanup_driver():
    """
    Clean up the global driver instance.
    """
    global _global_driver
    if _global_driver:
        try:
            _global_driver.quit()
        except Exception:
            pass
        _global_driver = None

def enrich_field(job_data: Dict[str, Any], field_name: str) -> Dict[str, Any]:
    """
    Enrich a specific field in the job data using AI enhancement.
    
    Args:
        job_data: The extracted job data dictionary
        field_name: The name of the field to enrich
        
    Returns:
        Dictionary containing the updated job data with enriched field
        
    Raises:
        ValueError: If the field name is invalid or enrichment fails
    """
    logger.info(f"Enriching job field: {field_name}")
    
    if field_name not in job_data:
        error_msg = f"Invalid field name: {field_name}. Field not found in job data."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        # Get the original field value
        original_value = job_data[field_name]
        
        # Call the enrichment model
        enriched_value = enrich_job_field(
            field_name=field_name,
            field_value=original_value,
            context=job_data
        )
        
        # Update the job data with the enriched value
        job_data[field_name] = enriched_value
        
        logger.info(f"Successfully enriched field: {field_name}")
        return job_data
        
    except Exception as e:
        error_msg = f"Error enriching job field {field_name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg)