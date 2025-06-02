"""
Vision-based document extraction for handling image-based PDFs and scanned documents.
Uses OpenAI's vision API to extract text from documents that don't have extractable text.
"""

import io
import os
import base64
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# Import with fallbacks
try:
    import fitz  # PyMuPDF
    _HAS_PYMUPDF = True
except ImportError:
    _HAS_PYMUPDF = False
    logging.getLogger(__name__).warning("PyMuPDF not available - vision-based PDF processing will be disabled")

try:
    from PIL import Image, ImageDraw, ImageFont
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False
    logging.getLogger(__name__).warning("PIL not available - text rendering will be disabled")

from openai import OpenAI
from config.log_config import get_logger
from config.timeout_config import OPENAI_API_TIMEOUT

logger = get_logger()

# Vision conversion constants
MAX_PAGES = int(os.getenv("JOB_PAGES_LIMIT", 10))  # Process more pages for job postings
DPI = int(os.getenv("JOB_DPI", 150))  # Slightly lower DPI for faster processing
MIN_TEXT_LENGTH = 100  # Minimum text length to consider extraction successful

# OpenAI setup
MODEL_NAME = os.getenv("OPENAI_PARSER_MODEL", "gpt-4o-mini")

def create_vision_client() -> OpenAI:
    """Create and return an OpenAI client for vision API calls."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    return OpenAI(api_key=api_key, timeout=OPENAI_API_TIMEOUT)


def pdf_to_vision_chunks(pdf_bytes: bytes, max_pages: int = MAX_PAGES) -> List[Dict]:
    """
    Convert PDF pages to vision API chunks.
    
    Args:
        pdf_bytes: Raw PDF bytes
        max_pages: Maximum number of pages to process
        
    Returns:
        List of vision API chunks
        
    Raises:
        ValueError: If PDF processing fails
    """
    if not _HAS_PYMUPDF:
        raise ValueError("PyMuPDF is required for vision-based PDF processing")
    
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        chunks = []
        
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            
            # Render page to image
            pix = page.get_pixmap(dpi=DPI)
            img_bytes = pix.tobytes("png")
            
            # Convert to base64 data URL
            data_url = "data:image/png;base64," + base64.b64encode(img_bytes).decode()
            
            chunks.append({
                "type": "image_url",
                "image_url": {"url": data_url, "detail": "auto"}
            })
            
            logger.debug(f"Converted PDF page {i+1} to vision chunk")
        
        if not chunks:
            raise ValueError("Could not render any PDF pages to images")
            
        logger.info(f"Successfully converted {len(chunks)} PDF pages to vision chunks")
        return chunks
        
    except Exception as e:
        error_msg = f"Error converting PDF to vision chunks: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg)


def extract_text_with_vision(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF using OpenAI's vision API.
    
    Args:
        pdf_bytes: Raw PDF bytes
        
    Returns:
        Extracted text content
        
    Raises:
        ValueError: If vision extraction fails
    """
    try:
        # Convert PDF to vision chunks
        vision_chunks = pdf_to_vision_chunks(pdf_bytes)
        
        # Prepare the prompt
        system_message = """You are a text extraction assistant. Extract all text content from the provided document images.
        Focus on extracting job posting information including:
        - Job title and company
        - Job description and responsibilities
        - Requirements and qualifications
        - Benefits and compensation
        - Location and job type
        - Any other relevant job details
        
        Return ONLY the extracted text, preserving the structure and formatting as much as possible.
        Do not add any commentary or analysis."""
        
        user_content = vision_chunks + [
            {"type": "text", "text": "Extract all text from these document images."}
        ]
        
        # Create OpenAI client
        client = create_vision_client()
        
        # Call OpenAI vision API
        logger.info(f"Calling OpenAI vision API with {len(vision_chunks)} image chunks using model {MODEL_NAME}")
        
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                temperature=0,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_content}
                ]
            )
            
            extracted_text = response.choices[0].message.content
            
            if not extracted_text or len(extracted_text.strip()) < MIN_TEXT_LENGTH:
                raise ValueError("Vision API returned insufficient text content")
            
            logger.info(f"Successfully extracted {len(extracted_text)} characters using vision API")
            logger.info(f"Vision API usage: {len(vision_chunks)} pages processed, approximately {len(vision_chunks) * 0.01} USD cost estimate")
            return extracted_text
            
        except Exception as e:
            logger.error(f"Vision API call failed: {str(e)}")
            raise
        
    except Exception as e:
        error_msg = f"Vision-based text extraction failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg)


def check_pdf_has_text(pdf_bytes: bytes) -> bool:
    """
    Check if a PDF has extractable text.
    
    Args:
        pdf_bytes: Raw PDF bytes
        
    Returns:
        True if PDF has extractable text, False otherwise
    """
    if not _HAS_PYMUPDF:
        return False
    
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Check first few pages for text
        for i, page in enumerate(doc):
            if i >= 3:  # Check first 3 pages
                break
            
            text = page.get_text().strip()
            if len(text) > MIN_TEXT_LENGTH:
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking PDF for text: {e}")
        return False


def extract_text_from_pdf_with_fallback(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF with vision API fallback for image-based PDFs.
    
    Args:
        pdf_bytes: Raw PDF bytes
        
    Returns:
        Extracted text content
        
    Raises:
        ValueError: If text extraction fails
    """
    # First, try regular text extraction
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []
        
        for page in doc:
            text_parts.append(page.get_text())
        
        text = "\n".join(text_parts).strip()
        
        # Check if we got meaningful text
        if text and len(text) > MIN_TEXT_LENGTH:
            logger.info(f"Successfully extracted {len(text)} characters using direct text extraction")
            return text
        else:
            logger.info("Direct text extraction yielded insufficient content, falling back to vision API")
            
    except Exception as e:
        logger.warning(f"Direct text extraction failed: {e}, falling back to vision API")
    
    # Fall back to vision API
    logger.info("Using vision API for text extraction")
    return extract_text_with_vision(pdf_bytes)


def render_text_to_image(text: str, page_size: Tuple[int, int] = (1240, 1754)) -> bytes:
    """
    Render plain text as an image for vision processing.
    
    Args:
        text: Text content to render
        page_size: Size of the page in pixels (width, height)
        
    Returns:
        PNG image bytes
    """
    if not _HAS_PIL:
        raise ValueError("PIL is required for text rendering")
    
    # Create white background
    img = Image.new('RGB', page_size, 'white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a good font
    font_size = 16
    font = None
    try:
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
                break
    except Exception:
        pass
    
    if font is None:
        font = ImageFont.load_default()
    
    # Calculate text layout
    margin = 50
    line_height = font_size + 4
    y = margin
    x = margin
    max_width = page_size[0] - (2 * margin)
    
    # Split text into lines
    lines = text.split('\n')
    
    for line in lines:
        if y + line_height > page_size[1] - margin:
            break  # Page full
            
        # Simple word wrapping
        words = line.split()
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    draw.text((x, y), ' '.join(current_line), fill='black', font=font)
                    y += line_height
                current_line = [word]
        
        if current_line:
            draw.text((x, y), ' '.join(current_line), fill='black', font=font)
            y += line_height
    
    # Save to bytes
    output = io.BytesIO()
    img.save(output, format='PNG')
    return output.getvalue()


def file_to_vision_chunks(file_bytes: bytes, file_extension: str) -> List[Dict]:
    """
    Convert any supported file format to vision chunks.
    
    Args:
        file_bytes: Raw file bytes
        file_extension: File extension (e.g., ".pdf", ".docx", ".txt")
        
    Returns:
        List of vision API chunks
    """
    file_extension = file_extension.lower()
    
    if file_extension == ".pdf":
        return pdf_to_vision_chunks(file_bytes)
    
    elif file_extension in [".txt", ".docx"]:
        # For text files, we need to extract text first then render as images
        text_content = ""
        
        if file_extension == ".txt":
            text_content = file_bytes.decode('utf-8', errors='ignore')
        elif file_extension == ".docx":
            # Extract text from DOCX using existing method
            try:
                from .doc_converters import extract_text_from_docx
                file_io = io.BytesIO(file_bytes)
                text_content = extract_text_from_docx(file_io)
            except Exception as e:
                logger.error(f"Failed to extract text from DOCX: {e}")
                raise ValueError(f"Failed to process DOCX file: {e}")
        
        if not text_content:
            raise ValueError("No text content found in file")
        
        # Split text into pages and render
        chunks = []
        lines_per_page = 60
        
        # Simple pagination
        lines = text_content.split('\n')
        pages = []
        
        for i in range(0, len(lines), lines_per_page):
            page_lines = lines[i:i + lines_per_page]
            pages.append('\n'.join(page_lines))
        
        # Render each page
        for page_text in pages[:MAX_PAGES]:
            try:
                img_bytes = render_text_to_image(page_text)
                data_url = "data:image/png;base64," + base64.b64encode(img_bytes).decode()
                chunks.append({
                    "type": "image_url",
                    "image_url": {"url": data_url, "detail": "auto"}
                })
            except Exception as e:
                logger.warning(f"Failed to render text page: {e}")
                continue
        
        if not chunks:
            raise ValueError("Failed to render any text pages")
        
        return chunks
    
    else:
        raise ValueError(f"Unsupported file type for vision processing: {file_extension}")