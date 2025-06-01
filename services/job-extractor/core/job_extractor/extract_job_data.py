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
import time
import random
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

def get_chrome_driver():
    """
    Create and configure an undetected Chrome driver instance.
    
    Returns:
        Configured Chrome driver instance
    """
    if not _HAS_SELENIUM:
        raise ImportError("Selenium or undetected_chromedriver is not installed")
        
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Use Chromium binary if available
    if os.environ.get('CHROME_BIN'):
        options.binary_location = os.environ['CHROME_BIN']
    
    # Add random user agent
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ]
    options.add_argument(f'--user-agent={random.choice(user_agents)}')
    
    # Use chromedriver path if available
    driver_path = os.environ.get('CHROMEDRIVER_PATH')
    if driver_path:
        return uc.Chrome(options=options, driver_executable_path=driver_path)
    return uc.Chrome(options=options)

def fetch_page(url: str) -> str:
    """
    Fetch HTML content from a URL using undetected-chromedriver for sites that block regular requests.
    
    Args:
        url: URL to fetch
        
    Returns:
        HTML content as string
        
    Raises:
        ValueError: If the URL is invalid or request fails
    """
    # First try with regular requests
    try:
        response = session.get(url, timeout=HTTP_REQUEST_TIMEOUT)
        if response.status_code == 200 and any(tag in response.text.lower() for tag in ['<html', '<body', '<div']):
            return response.text
    except Exception as e:
        logger.warning(f"Regular request failed: {str(e)}")
    
    # If Selenium is not available, we can't use browser emulation
    if not _HAS_SELENIUM:
        logger.error("Browser emulation is not available - request failed and fallback not possible")
        raise ValueError(f"Failed to fetch content from {url} and browser emulation is not available")
    
    # If regular request fails or returns invalid content, use browser emulation
    logger.info("Falling back to browser emulation")
    driver = None
    try:
        driver = get_chrome_driver()
        
        # Add random delay to simulate human behavior
        time.sleep(random.uniform(1, 3))
        
        # Navigate to the URL
        driver.get(url)
        
        # Wait for the page to load (wait for body to be present)
        WebDriverWait(driver, SELENIUM_PAGE_LOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional random delay to simulate reading
        time.sleep(random.uniform(2, 4))
        
        # Scroll down slowly to simulate human behavior
        total_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(0, total_height, random.randint(100, 200)):
            driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(random.uniform(0.1, 0.3))
        
        # Get the page source
        html_content = driver.page_source
        
        if not html_content.strip():
            raise ValueError(f"Empty response received from {url}")
            
        if not any(tag in html_content.lower() for tag in ['<html', '<body', '<div']):
            raise ValueError(f"Invalid HTML response received from {url}")
            
        return html_content
        
    except TimeoutException:
        error_msg = f"Timeout while loading page from {url}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    except WebDriverException as e:
        error_msg = f"Browser error when fetching {url}: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Error fetching page from URL: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f"Error closing browser: {str(e)}")

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
        
        # Process the job posting through the AI model
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
        
        # Use the doc_converters utility to extract text
        text_content, file_type = extract_text_from_document(file_io, f"file{file_extension}")
        logger.info(f"Successfully extracted text from {file_type} file (length: {len(text_content)} characters)")
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