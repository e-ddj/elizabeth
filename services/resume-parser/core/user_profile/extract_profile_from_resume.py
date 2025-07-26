"""
core/user_profile/extract_profile_from_resume.py

Primary path  : upload the resume (PDF / DOCX / DOC / TXT) to OpenAI's
                vision-capable GPT model and read JSON.
Fallback path : local text extraction → run_model() (old pipeline).
Both paths attach a base-64 head-shot to the result.
"""

from __future__ import annotations

# ────────── std-lib ──────────
import argparse
import base64
import inspect
import io
import json
import logging
import os
import re
import tempfile
import time
from pathlib import Path
from dataclasses import asdict, is_dataclass
from typing import Any, Optional, Tuple
import copy
import subprocess

# ────────── 3rd-party ──────────
import fitz  # PyMuPDF
import openai
from PIL import Image, ImageDraw, ImageFont
import docx  # python-docx  – pip install python-docx

from core.user_profile.types import UserData
from models.user_profile.model import run_model
from utils.files.doc_converters import extract_text_from_document
from utils.json_serializer import json_serializer
from utils.supabase.client import create_client
from utils.supabase.bucket import download_file

# ────────── logging ──────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ────────── regex helpers ──────────
_JSON_RE = re.compile(r"\{.*\}", re.S)  # greedy – finds the first {...}

# ────────── head-shot filter constants ──────────
_MAX_PIXELS = 2_200_000      # allow up to 2.2 MP
_MIN_PIXELS = 5_000          # minimum size to be considered a profile photo (e.g., 70x70)
_ASPECT_MIN = 0.66           # slightly more strict aspect ratio (portrait oriented)
_ASPECT_MAX = 1.5            # slightly more strict aspect ratio (less wide)

# Add face detection capability
try:
    # Add debug information to help diagnose OpenCV import issues
    logger.info("Attempting to import OpenCV")
    import cv2
    import numpy as np
    
    # Log OpenCV version to help with debugging
    cv2_version = cv2.__version__
    logger.info(f"OpenCV loaded successfully, version: {cv2_version}")
    
    # Verify OpenCV is working by attempting a simple operation
    test_img = np.zeros((10, 10, 3), dtype=np.uint8)
    gray_test = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
    
    _HAS_CV2 = True
    try:
        # Try to load the face cascade classifier
        _face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        logger.info(f"Loading face cascade from: {_face_cascade_path}")
        _face_cascade = cv2.CascadeClassifier(_face_cascade_path)
        
        # Verify the cascade loaded properly
        if _face_cascade.empty():
            logger.warning(f"Failed to load face cascade from {_face_cascade_path}")
            _HAS_CV2 = False
        else:
            logger.info("OpenCV face detection loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to load face cascade classifier: {e}")
        _HAS_CV2 = False
except ImportError as e:
    logger.warning(f"OpenCV not available - face detection will be disabled: {e}")
    _HAS_CV2 = False
except Exception as e:
    logger.warning(f"Error initializing OpenCV: {e}")
    _HAS_CV2 = False

# ────────── OpenAI setup ──────────
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_PARSER_MODEL", "gpt-4o-mini")

# ────────── vision-conversion constants ──────────
MAX_PAGES = int(os.getenv("CV_PAGES_LIMIT", 6))
DPI       = int(os.getenv("CV_DPI", 180))      # 180 dpi ≈ 1240 px wide A4

# Synthetic-page rendering (for DOCX / TXT)
_CHARS_PER_LINE = 110
_LINES_PER_PAGE = 60
_PAGE_PX        = (1240, 1754)    # A4 @ 180 dpi
_FONT_SIZE      = 20

# ──────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ──────────────────────────────────────────────────────────────────────────────
def _contains_face(b64_str: str) -> bool:
    """Check if the image contains a human face using OpenCV."""
    if not _HAS_CV2:
        logger.debug("OpenCV face detection not available, assuming image might be a face")
        return True  # If OpenCV isn't available, assume it might be a face
        
    try:
        # Convert base64 to image
        img_bytes = base64.b64decode(b64_str)
        img_array = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if img is None:
            logger.warning("Could not decode image for face detection")
            return False
            
        # Log image dimensions for debugging
        h, w, c = img.shape
        logger.debug(f"Face detection on image: {w}x{h} pixels, {c} channels")
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Track best face based on size and position (centered faces are better)
        best_face_score = 0
        best_face = None
        
        # Try multiple scale factors for better detection rates
        for scale_factor in [1.1, 1.2, 1.3]:
            for min_neighbors in [3, 5]:
                # Detect faces with varying parameters
                faces = _face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=scale_factor,
                    minNeighbors=min_neighbors,
                    minSize=(30, 30)
                )
                
                for (x, y, w, h) in faces:
                    # Calculate face size ratio (face area / image area)
                    face_size_ratio = (w * h) / (img.shape[0] * img.shape[1])
                    
                    # Calculate how centered the face is (1.0 = perfectly centered)
                    center_x, center_y = x + w/2, y + h/2
                    img_center_x, img_center_y = img.shape[1]/2, img.shape[0]/2
                    
                    # Distance from center (normalized to 0-1 range)
                    distance_from_center = np.sqrt(
                        ((center_x - img_center_x) / img.shape[1])**2 + 
                        ((center_y - img_center_y) / img.shape[0])**2
                    )
                    centering_score = 1.0 - min(distance_from_center, 1.0)
                    
                    # Score combines face size and centering (with size being more important)
                    face_score = (face_size_ratio * 0.7) + (centering_score * 0.3)
                    
                    if face_score > best_face_score:
                        best_face_score = face_score
                        best_face = (x, y, w, h)
        
        if best_face is not None:
            logger.info(f"Face detected with score={best_face_score:.2f}")
            
            # Additional checks for headshot vs document face:
            # 1. Face should occupy a reasonable portion of the image
            if best_face_score < 0.15:  # Face is too small relative to image
                logger.debug(f"Face too small relative to image size: {best_face_score:.2f}")
                return False
                
            # 2. Calculate skin tone distribution for face area
            x, y, w, h = best_face
            face_region = img[y:y+h, x:x+w]
            
            # Convert to HSV to detect skin tones
            face_hsv = cv2.cvtColor(face_region, cv2.COLOR_BGR2HSV)
            
            # Define range for skin tones (broad range to cover different ethnicities)
            lower_skin = np.array([0, 20, 70])
            upper_skin = np.array([35, 255, 255])
            skin_mask = cv2.inRange(face_hsv, lower_skin, upper_skin)
            
            # Calculate percentage of pixels in face region that are skin-colored
            skin_percentage = np.sum(skin_mask > 0) / (w * h)
            
            # Real headshots should have a significant percentage of skin tone
            if skin_percentage < 0.3:  # Less than 30% skin tone in face region
                logger.debug(f"Face region has insufficient skin tone: {skin_percentage:.2f}")
                return False
            
            return True
        
        # No faces found with any parameters
        logger.debug("No faces detected in image")
        return False
    except Exception as e:
        logger.warning(f"Error during face detection: {e}", exc_info=True)
        # If face detection fails, be permissive and assume it might be a face
        return True

def _first_json_block(text: str) -> str:
    """Return the first {...} chunk found or raise ValueError."""
    m = _JSON_RE.search(text)
    if not m:
        raise ValueError("no JSON object found in model reply")
    return m.group(0)

def _looks_like_headshot(b64: str) -> bool:
    """Return True if the base-64 image is plausibly a face photo."""
    if not b64:
        return False
    try:
        with Image.open(io.BytesIO(base64.b64decode(b64))) as im:
            w, h = im.size
            pixel_count = w * h
            
            # Check dimensions and pixel count
            if pixel_count < _MIN_PIXELS:
                logger.debug(f"Image too small: {w}x{h} pixels")
                return False
                
            if pixel_count > _MAX_PIXELS:
                logger.debug(f"Image too large: {w}x{h} pixels")
                return False
                
            aspect = w / h if h else 1
            if not (_ASPECT_MIN <= aspect <= _ASPECT_MAX):
                logger.debug(f"Aspect ratio outside acceptable range: {aspect}")
                return False
            
            # Check for face content if OpenCV is available
            has_face = _contains_face(b64)
            if not has_face:
                logger.debug("No face detected in the image")
                return False

            # Additional screenshot detection: check if image has document-like characteristics
            # Screenshots often have white backgrounds and text-like patterns
            if _looks_like_document_screenshot(b64):
                logger.debug("Image appears to be a document screenshot rather than a headshot")
                return False
            
            return True
    except Exception as e:
        logger.warning(f"Error checking if image is a headshot: {e}")
        return False

def _looks_like_document_screenshot(b64: str) -> bool:
    """Detect if an image looks like a document screenshot rather than a headshot."""
    try:
        # Convert base64 to image
        img_bytes = base64.b64decode(b64)
        img_array = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if img is None:
            return False
        
        # 1. Check for large areas of white/light color (document background)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # Define range for white/light colors
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        white_mask = cv2.inRange(hsv, lower_white, upper_white)
        white_percentage = np.sum(white_mask > 0) / (img.shape[0] * img.shape[1])
        
        # 2. Check for text-like features (many horizontal/vertical edges)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_percentage = np.sum(edges > 0) / (img.shape[0] * img.shape[1])
        
        # 3. Check image complexity - profile photos typically have more varied colors
        unique_colors = len(np.unique(img.reshape(-1, 3), axis=0))
        max_colors = 256 * 256 * 256  # theoretical maximum
        color_ratio = unique_colors / max_colors
        
        # Screenshots typically have: high white percentage, many edges, fewer unique colors
        if white_percentage > 0.7 and edge_percentage > 0.1:
            logger.debug(f"Likely document screenshot: white={white_percentage:.2f}, edges={edge_percentage:.2f}")
            return True
            
        # Check the face size relative to the image
        if _HAS_CV2:
            face_area_ratio = _get_face_area_ratio(img)
            if face_area_ratio < 0.15:  # Face is too small compared to overall image
                logger.debug(f"Face too small relative to image size: {face_area_ratio:.2f}")
                return True
        
        return False
    except Exception as e:
        logger.warning(f"Error checking if image is a document screenshot: {e}")
        return False

def _get_face_area_ratio(img) -> float:
    """Calculate the ratio of the largest face area to the total image area."""
    try:
        if not _HAS_CV2:
            return 0.0
            
        h, w = img.shape[:2]
        total_area = h * w
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = _face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        if len(faces) == 0:
            return 0.0
            
        # Find the largest face
        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
        x, y, w, h = largest_face
        face_area = w * h
        
        return face_area / total_area
    except Exception as e:
        logger.warning(f"Error calculating face area ratio: {e}")
        return 0.0

def _extract_headshot_base64(pdf_bytes: bytes, fmt: str = "png") -> Optional[str]:
    """Try to pull a single ≈portrait image from a PDF that contains a face."""
    if not pdf_bytes:
        logger.warning("No PDF bytes provided for headshot extraction")
        return None
        
    # Check if the file starts with the PDF magic number '%PDF'
    if not pdf_bytes.startswith(b'%PDF'):
        logger.warning("File does not appear to be a valid PDF (missing magic number)")
        return None
        
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Verify we have a valid document with pages
        if doc.page_count == 0:
            logger.warning("PDF has no pages")
            return None
        
        # First pass: look for images that contain faces    
        potential_headshots = []
        
        for page in doc:
            logger.debug(f"Scanning page {page.number + 1}/{doc.page_count} for images")
            images = page.get_images(full=True)
            logger.debug(f"Found {len(images)} images on page {page.number + 1}")
            
            for img in images:
                try:
                    pix = fitz.Pixmap(doc, img[0])
                    if pix.n > 4:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    
                    w, h = pix.width, pix.height
                    pixel_count = w * h
                    
                    # Skip very small or very large images
                    if pixel_count < _MIN_PIXELS or pixel_count > _MAX_PIXELS:
                        logger.debug(f"Skipping image due to size: {w}x{h} ({pixel_count} pixels)")
                        continue
                        
                    # Calculate aspect ratio
                    aspect = w / h if h else 1
                    
                    # Skip images with aspect ratios outside our range
                    if not (_ASPECT_MIN <= aspect <= _ASPECT_MAX):
                        logger.debug(f"Skipping image due to aspect ratio: {aspect}")
                        continue
                    
                    # Get the image bytes and encode as base64
                    img_bytes = pix.tobytes(fmt)
                    encoded = base64.b64encode(img_bytes).decode('ascii', errors='ignore')
                    
                    # Check for document screenshot characteristics
                    if _HAS_CV2 and _looks_like_document_screenshot(encoded):
                        logger.debug(f"Skipping image that appears to be a document screenshot")
                        continue
                    
                    # If OpenCV is available, check if this image contains a face
                    if _contains_face(encoded):
                        logger.info(f"Found potential headshot on page {page.number + 1}: {w}x{h}")
                        
                        # If OpenCV is available, extract just the face region
                        if _HAS_CV2:
                            cropped_face = _crop_to_face(encoded)
                            if cropped_face:
                                encoded = cropped_face
                                logger.info("Successfully cropped to face region")
                        
                        # Found a face! Store size info with the image
                        potential_headshots.append({
                            "encoded": encoded,
                            "size": pixel_count,
                            "aspect": aspect,
                            "page": page.number  # Earlier pages are often more likely to have profile pics
                        })
                except Exception as img_err:
                    logger.debug(f"Error processing specific image in PDF: {img_err}")
                    continue
        
        # If we found potential headshots, use the best one
        if potential_headshots:
            logger.info(f"Found {len(potential_headshots)} potential headshots, selecting best one")
            # Sort by page number (ascending), then size (descending) for appropriate size profile photos
            potential_headshots.sort(key=lambda x: (x["page"], -x["size"]))
            return potential_headshots[0]["encoded"]
        else:
            logger.info("No headshots with faces detected in PDF")
            return None
    except fitz.FileDataError:
        logger.warning("Invalid PDF data structure - failed to open PDF stream")
        return None
    except Exception as e:
        logger.exception(f"Head-shot extraction failed: {str(e)}")
        return None

def _crop_to_face(b64: str) -> Optional[str]:
    """Crop image to just the face region with a small border."""
    if not _HAS_CV2:
        return None
        
    try:
        # Save the original image for debugging
        _save_debug_image(b64, "before_crop")
        
        # Convert base64 to image
        img_bytes = base64.b64decode(b64)
        img_array = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if img is None:
            return None
            
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = _face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        if len(faces) == 0:
            return None
            
        # Find the largest face
        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
        x, y, w, h = largest_face
        
        # Add a border around the face (20% of face size)
        border = int(max(w, h) * 0.2)
        x = max(0, x - border)
        y = max(0, y - border)
        w = min(img.shape[1] - x, w + 2 * border)
        h = min(img.shape[0] - y, h + 2 * border)
        
        # Crop to the face region
        face_img = img[y:y+h, x:x+w]
        
        # Make it square by padding the shorter dimension
        if w > h:
            diff = w - h
            pad_top = diff // 2
            pad_bottom = diff - pad_top
            face_img = cv2.copyMakeBorder(face_img, pad_top, pad_bottom, 0, 0, cv2.BORDER_CONSTANT, value=[255, 255, 255])
        elif h > w:
            diff = h - w
            pad_left = diff // 2
            pad_right = diff - pad_left
            face_img = cv2.copyMakeBorder(face_img, 0, 0, pad_left, pad_right, cv2.BORDER_CONSTANT, value=[255, 255, 255])
        
        # Resize if needed to ensure dimensions don't exceed 400px
        max_dim = 400
        height, width = face_img.shape[:2]
        if height > max_dim or width > max_dim:
            scale = max_dim / max(height, width)
            face_img = cv2.resize(face_img, (int(width * scale), int(height * scale)))
        
        # Convert back to base64
        success, buffer = cv2.imencode(".png", face_img)
        if not success:
            return None
            
        result = base64.b64encode(buffer).decode('ascii', errors='ignore')
        _save_debug_image(result, "after_crop")
        return result
    except Exception as e:
        logger.warning(f"Error cropping to face: {e}")
        return None

# ────────── Extract and enhance profile photo ──────────
def _extract_best_profile_photo(file_bytes: bytes, openai_photo: Optional[str] = None) -> Optional[str]:
    """Extract the best profile photo directly from the document, ignoring any OpenAI provided photo."""
    # Always extract directly from the document
    logger.info("Extracting headshot directly from document...")
    try:
        # For PDF, try to extract directly
        if file_bytes.startswith(b'%PDF'):
            photo = _extract_headshot_base64(file_bytes)
            if photo:
                _save_debug_image(photo, "pdf_extracted")
                
                if _looks_like_headshot(photo):
                    logger.info("Successfully extracted valid headshot from PDF")
                    return photo
                else:
                    logger.warning("Extracted image from PDF failed headshot validation")
                
        # TODO: Add support for other file types if needed
        
        logger.warning("Could not extract a valid profile photo from the document")
        return None
    except Exception as e:
        logger.exception(f"Error while trying to extract profile photo: {e}")
        return None

# ────────── PDF → vision chunks ──────────
def _pdf_pages_to_vision_chunks(pdf_bytes: bytes) -> list[dict]:
    """Render the first MAX_PAGES of the PDF to PNG & wrap as vision-chunks."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    chunks: list[dict] = []

    for i, page in enumerate(doc):
        if i >= MAX_PAGES:
            break

        pix = page.get_pixmap(dpi=DPI)  # crisp text, small file
        data_url = "data:image/png;base64," + base64.b64encode(
            pix.tobytes("png")
        ).decode()

        chunks.append(
            {
                "type": "image_url",
                "image_url": {"url": data_url, "detail": "auto"},
            }
        )

    if not chunks:
        raise RuntimeError("could not render any page to image")
    return chunks


# ────────── Text pagination & rendering (DOCX / TXT) ──────────
def _text_to_pages(
    text: str,
    chars_per_line: int = _CHARS_PER_LINE,
    lines_per_page: int = _LINES_PER_PAGE,
) -> list[str]:
    """Split free-flowing text into roughly A4-sized pages of plain text."""
    words: list[str] = text.split()
    line, lines, pages = "", [], []

    for w in words:
        if len(line) + len(w) + 1 > chars_per_line:
            lines.append(line)
            line = w
        else:
            line += (" " if line else "") + w
    if line:
        lines.append(line)

    for i in range(0, len(lines), lines_per_page):
        pages.append("\n".join(lines[i : i + lines_per_page]))
    return pages or [text]  # guarantee at least one page


def _render_text_page_to_png(
    text: str,
    size: tuple[int, int] = _PAGE_PX,
    font_size: int = _FONT_SIZE,
) -> bytes:
    """Render a page of text onto a white PNG and return raw bytes."""
    img = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(img)

    try:
        # Try to use a system font that's likely to be available
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows
            "DejaVuSans.ttf"  # Local fallback
        ]
        
        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except Exception:
                continue
                
        if font is None:
            font = ImageFont.load_default()
            logger.warning("Using default font as no system fonts were found")
    except Exception as e:
        logger.warning(f"Error loading font: {e}")
        font = ImageFont.load_default()

    # Calculate margins and line spacing
    margin = 40
    line_spacing = font_size + 6
    max_width = size[0] - (2 * margin)
    
    # Split text into words and create lines
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        # Test if adding this word would exceed the line width
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))

    # Draw the text
    y = margin
    for line in lines:
        if y + line_spacing > size[1] - margin:
            break
        draw.text((margin, y), line, font=font, fill="black")
        y += line_spacing

    # Save to PNG
    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    return buf.getvalue()


# ────────── Generic resume → vision chunks ──────────
def _file_bytes_to_vision_chunks(blob: bytes, suffix: str) -> list[dict]:
    """
    Convert *any* supported resume format to vision chunks.
    • PDF  → identical to old behaviour
    • DOCX → convert to PDF then render to images
    • DOC  → try libreoffice → PDF path; else textract
    • TXT  → direct text → images
    """
    suffix = suffix.lower()
    if suffix == ".pdf":
        return _pdf_pages_to_vision_chunks(blob)

    if suffix in (".docx", ".doc", ".txt"):
        # For DOCX and DOC, first try to convert to PDF using libreoffice
        if suffix in (".docx", ".doc"):
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    # Save the original file
                    input_path = Path(tmp) / f"input{suffix}"
                    input_path.write_bytes(blob)
                    logger.info(f"Saved input file to: {input_path}")
                    
                    # Convert to PDF
                    output_path = Path(tmp) / "input.pdf"  # LibreOffice keeps the same name but changes extension
                    logger.info(f"Converting {suffix} to PDF using libreoffice...")
                    
                    # Use headless libreoffice to convert with more robust options
                    cmd = [
                        "libreoffice",
                        "--headless",
                        "--convert-to", "pdf",
                        "--outdir", str(tmp),
                        "--norestore",
                        "--nofirststartwizard",
                        "--nologo",
                        str(input_path)
                    ]
                    
                    # Log the full command for debugging
                    logger.debug(f"Running command: {' '.join(cmd)}")
                    
                    # Run the command and capture output
                    process = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    # Log the command output for debugging
                    if process.stdout:
                        logger.debug(f"LibreOffice stdout: {process.stdout}")
                    if process.stderr:
                        logger.debug(f"LibreOffice stderr: {process.stderr}")
                    
                    # Check if conversion was successful
                    if process.returncode == 0:
                        # List all files in the temp directory to debug
                        logger.debug(f"Files in temp directory: {list(Path(tmp).glob('*'))}")
                        
                        if output_path.exists():
                            logger.info(f"Successfully converted document to PDF: {output_path}")
                            pdf_bytes = output_path.read_bytes()
                            logger.info(f"PDF size: {len(pdf_bytes)} bytes")
                            return _pdf_pages_to_vision_chunks(pdf_bytes)
                        else:
                            error_msg = f"PDF file not found at expected path: {output_path}"
                            logger.warning(error_msg)
                            raise RuntimeError(error_msg)
                    else:
                        error_msg = f"LibreOffice conversion failed with return code {process.returncode}"
                        if process.stderr:
                            error_msg += f": {process.stderr}"
                        logger.warning(error_msg)
                        raise RuntimeError(error_msg)
                        
            except Exception as e:
                logger.warning(f"Failed to convert {suffix} to PDF: {e}")
                # Fall back to text extraction for DOC files
                if suffix == ".doc":
                    import textract
                    text = textract.process(None, buffer=blob).decode(errors="ignore")
                else:
                    # For DOCX, use python-docx as fallback
                    doc = docx.Document(io.BytesIO(blob))
                    text = "\n".join(p.text for p in doc.paragraphs)
        else:  # .txt
            text = blob.decode(errors="ignore")

        if not text.strip():
            raise RuntimeError("no text extracted")

        # ── 2 paginate + render ─────────────────────────────────────────
        chunks: list[dict] = []
        for pg in _text_to_pages(text)[:MAX_PAGES]:
            png = _render_text_page_to_png(pg)
            data_url = "data:image/png;base64," + base64.b64encode(png).decode()
            chunks.append(
                {
                    "type": "image_url",
                    "image_url": {"url": data_url, "detail": "auto"},
                }
            )
        if chunks:
            return chunks
        raise RuntimeError("could not render text to images")

    raise ValueError(f"unsupported file extension {suffix}")


# cv_parser_prompt.py
# ---------------------------------------------------------------------
# Prompt definition for the résumé‑parsing LLM/agent
# ---------------------------------------------------------------------

SYSTEM_MESSAGE = """
You are an expert CV-parser. The attached PDF file may contain text or be image-based. First, evaluate if the PDF contains extractable text or requires Optical Character Recognition (OCR) for text extraction. **Then perform an image pass** (see Photo-extraction workflow below). After extracting the text, carefully parse the content and provide the output as a single JSON object with the following structure:

- `detected_language`: The primary language of the resume (e.g., "English", "Spanish", "Chinese", "Arabic", etc.)
- `was_translated`: Boolean indicating if translation was performed (true if resume was not in English, false otherwise)
- `profile`: Personal information (see detailed field list below).
- `experiences`: Job-experience items (see detailed field list below).
- `educations`: Degree or certificate items (see detailed field list below).
- `languages`: Spoken languages.
- `certifications`: Professional certificates and licences.
- `publications`: Research publications.
- `awards`: List of prizes, medals, scholarships, fellowships or other distinctions.
- `scores`: **must always be present** (see scoring logic below).

**LANGUAGE DETECTION AND TRANSLATION**:
1. First, detect the primary language of the resume content
2. If the resume is not in English, translate ALL content to English during extraction
3. When translating:
   - Translate job titles, descriptions, and all narrative text to English
   - For proper nouns (organization names, university names, etc.), provide the English translation but you may also include the original name in parentheses if it adds clarity
   - Ensure all extracted data in the JSON response is in English
   - Set `was_translated` to true and specify the `detected_language`
4. If the resume is already in English, set `was_translated` to false and `detected_language` to "English"

**IMPORTANT**: DO NOT extract or include any profile pictures in your response. The `photo_base64` field will be handled separately by the system. Leave this field empty ("") in your response.

**IMPORTANT**: All country names must use full standard names, never abbreviations. For example:
- "USA", "US", "U.S.A", "U.S.", "America" → "United States"
- "UK", "U.K.", "Great Britain", "Britain", "England" → "United Kingdom" 
- "UAE", "U.A.E." → "United Arab Emirates"
- "KSA", "Saudi" → "Saudi Arabia"
- "Aussie", "AUS" → "Australia"
- "ROK", "Korea", "S. Korea"  → "South Korea"
- "PRC", "Mainland China" → "China"
- "Holland", "The Netherlands" → "Netherlands"

Follow these country standardization rules for all fields that include a country (profile, experiences, educations, certifications, awards). Always convert any country code or abbreviation to its full official name in English.


- `profile`: Contains personal information like:
    - `title`: The title (e.g., "Dr.", "Mr.", "Ms.").
    - `first_name`: The first name of the individual.
    - `last_name`: The last name of the individual.
    - `position`: The current job position of the individual.
    - `street`: The street address (if available).
    - `city`: The city of the individual (if available).
    - `country`: The country of the individual (if available). Use the full standard country name, not abbreviations.
    - `phone`: The phone number (if available).
    - `citizenships`: The citizenship(s) of the individual (if available). Use full country names, not abbreviations.
    - `about_me`: A brief description of the individual (if available). If this is missing from the resume, generate a professional and concise "about me" summary based on the job title, field, and any other available information in the resume. Never fabricate informations that are not available.

- `experiences`: List of job experiences, including:
    - `job_title`: The job title.
    - `organization`: The name of the organization or institution.
    - `city`: The city where the job is located.
    - `country`: The country of the job location. Use the full standard country name, not abbreviations. If no country is provided, leave this field with the value null. 
    - `start_date`: Start date of the job in `MM/DD/YYYY` format.
    - `end_date`: End date of the job in `MM/DD/YYYY` format, or `"present"` if ongoing.
    - `description`: A concise description of the job role, responsibilities, or achievements. If no description is available in the resume, generate a description based on the job title, organization, and relevant details from the resume.

- `educations`: List of degrees with the following structure (always use this exact format for each education item):
    - `degree_name`: The full title of the degree or certificate (e.g., "Certificate in Medical Laboratory Techniques").
    - `degree_type`: The type of degree (e.g., "Certificate").
    - `description`: A short description of the degree or certificate (if available). If no description is provided, leave this field empty ("").
    - `start_date`: graduation date of the degree program in `YYYY` format.
    - `school_name`: The name of the institution where the degree was awarded.
    - `city`: The city where the educational institution is located (if available).
    - `country`: The country where the educational institution is located (if available). Use the full standard country name, not abbreviations. If no country is provided, leave this field with the value null. 

- `languages`: List of spoken languages (empty if none).

- `certifications`: List of certifications, including:
    - `title`: The name of the certificate.
    - `issuing_organization`: The organization issuing the certificate.
    - `city`: City where the certificate was issued (if available).
    - `country`: Country where the certificate was issued (if available). Use the full standard country name, not abbreviations. If no country is provided, leave this field with the value null. 
    - `issue_date`: Date the certificate was issued in `MM/DD/YYYY` format.

- `awards`: List of prizes, medals, scholarships, fellowships or other distinctions. For each award provide:
    - `title`: The name of the award (e.g., "Lee Kuan Yew Gold Medal").
    - `awarding_organization`: The body that conferred the award (e.g., "National University of Singapore").
    - `city`: City where the award was given (if available).
    - `country`: Country where the award was given (if available). Use the full standard country name, not abbreviations. If no country is provided, leave this field with the value null. 
    - `date`: The year the award was received in `YYYY` format, or full date in `MM/DD/YYYY` if available.
    - `description`: Short optional context (leave `""` if not given).

- `publications`: List of research publications, including:
    - `title`: The title of the publication.
    - `journal`: The journal where it was published.
    - `date`: The year of publication in `YYYY` format.

Empty sections should be represented as an empty list (`[]`) or an empty dictionary (`{}`) as appropriate. If no profile picture is found, set `photo_base64` to an empty string. If a value cannot be found **verbatim or by unambiguous inference** inside the document, leave it empty (""), `null`, or `[]` as required — **never fabricate or guess**.

**Ensure that the degree type is always included** and **map the degree name to a generic degree type** (e.g., "Ph.D." → "PhD", "Bachelor of Medicine & Bachelor of Surgery" → "MBBS").  
- If the degree is **BSc (Bachelor of Science)**, map it to **BS** in the **degree_type** field.  
- The **degree_name** field should combine the **degree type** and **description** into a concise short name (e.g., "PhD in Crystallography", "MBBS, Medicine & Surgery").  
- The **description** field should explain what the degree was about, its focus or specialization, if available.

First, evaluate the document to determine whether the text is directly extractable or if OCR is required, and then proceed with parsing and extraction as described above.

Append a top-level key called `"scores"` to your final JSON, with this structure:

    "scores": {
        "completion_score":      0,   // integer 0–100
        "data_strength_score":   0,   // integer 0–100
        "healthcare_confidence": 0,   // integer 0–100
        "messages": []               // array of short user-facing strings
    }

- **completion_score** – percentage of mandatory atomic fields that were successfully filled (rounded to nearest integer).  
- **data_strength_score** – start from *completion_score* then subtract up to 30 points:  
    –5 if dates lack month/day, –5 if addresses lack country, –10 if OCR quality poor, –10 if descriptions had to be generated. (Floor = 0)  
- **healthcare_confidence** – start at 0 and adjust:  
    +25 if most-recent job_title is healthcare-related; +15 for each earlier healthcare role (max +30); +20 if any degree_type is MD/MBBS/BPharm/BSN/MSN/DPT/DDS/DMD/DVM/etc.; +10 if certifications contain medical licence; –20 if no healthcare evidence at all. Clamp 0–100.  
- **messages** – add in order:  
    - If completion_score < 70 → "Your resume is missing key fields. Please check the highlighted gaps."  
    - If data_strength_score < 60 → "Some data could not be reliably extracted; manual review advised."  
    - If healthcare_confidence < 50 → "We could not confirm that this resume belongs to a healthcare professional."  
    - If healthcare_confidence ≥ 50 **and** completion_score ≥ 70 → "Profile looks good — you can proceed to the next step."  

**Before finalizing your response**, verify that all country names are standardized according to the rules above. This is especially important for internationalized resumes where country names might appear in various formats.

Return **one** JSON object only — no markdown fencing, no extra keys:

{
  "detected_language": "English",
  "was_translated": false,
  "profile": { ... },
  "experiences": [ ... ],
  "educations": [ ... ],
  "languages": [ ... ],
  "certifications": [ ... ],
  "awards": [ ... ],
  "publications": [ ... ],
  "scores": {
      "completion_score": 0,
      "data_strength_score": 0,
      "healthcare_confidence": 0,
      "messages": []
  }
}
"""

USER_INSTRUCTIONS = (
    "Parse the attached CV and output the JSON schema described, "
    "considering whether the document contains extractable text or requires OCR. "
    "Detect the language of the resume and translate to English if necessary. "
    "Make sure to extract and include the city and country for both the education and professional experience items, "
    "where available, and follow the provided structure for the education section."
)


def _upload_png_for_vision(img_bytes: bytes, name: str, timeout: float = 30) -> str:
    """(Unused in current flow, kept for completeness.)"""
    import time

    file_obj = openai.files.create(
        file=(name, img_bytes, "image/png"),
        purpose="vision",
    )
    fid = file_obj.id

    t0 = time.monotonic()
    while file_obj.status != "processed":
        if time.monotonic() - t0 > timeout:
            raise TimeoutError(f"file {fid} not processed after {timeout}s")
        time.sleep(0.5)
        file_obj = openai.files.retrieve(fid)
    return fid


def _ask_openai_with_images(file_bytes: bytes, suffix: str) -> dict:
    """Primary path – send images + instructions to a vision-capable GPT model."""
    try:
        vision_chunks = _file_bytes_to_vision_chunks(file_bytes, suffix)

        user_content = vision_chunks + [
            {"type": "text", "text": USER_INSTRUCTIONS},
        ]

        chat = openai.chat.completions.create(
            model=MODEL_NAME,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": user_content},
            ],
        )

        content = chat.choices[0].message.content
        try:
            result = json.loads(content)  # fast path – pure JSON
        except json.JSONDecodeError:
            result = json.loads(_first_json_block(content))
            
        # Remove any photo_base64 field from OpenAI's response as we'll use our own
        if "photo_base64" in result:
            logger.info("Removing photo_base64 from OpenAI response as we'll extract it ourselves")
            result["photo_base64"] = ""
            
        # Also remove from profile sub-object if present
        if isinstance(result.get("profile"), dict) and "photo_base64" in result["profile"]:
            result["profile"]["photo_base64"] = ""
            
        return result
    except Exception as e:
        logger.exception("OpenAI parse failed: %s", e)
        return {}


def _attach_photo(obj: dict, photo_b64: Optional[str]) -> None:
    """Mirror the chosen head-shot into all required fields."""
    # Set photo_base64 to empty string if no photo was found
    photo_to_set = photo_b64 if photo_b64 else ""
    
    # Ensure required fields exist
    for field in ["photo_base64", "experiences", "educations", "languages", "certifications", "publications", "awards"]:
        if field not in obj:
            obj[field] = [] if field != "photo_base64" else ""
    
    # Set the top-level photo_base64 field
    obj["photo_base64"] = photo_to_set
    
    # Set the avatarPreviewUrl field if a photo exists
    if photo_to_set:
        obj["avatarPreviewUrl"] = f"data:image/png;base64,{photo_to_set}"
    else:
        obj["avatarPreviewUrl"] = ""
    
    # Set the profile.photo_base64 field if profile exists
    if isinstance(obj.get("profile"), dict):
        obj["profile"]["photo_base64"] = photo_to_set
        
    logger.debug(f"Photo attached to response object: {'set' if photo_to_set else 'empty string'}")


def _upload_file_to_openai(data: bytes, filename: str) -> str:
    return openai.files.create(
        file=(filename, data, "application/pdf"), purpose="assistants"
    ).id


def _clean_json_block(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[A-Za-z0-9]*", "", text).strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    return text


def _dataclass_from_dict(dc_type, data: Any):
    if not is_dataclass(dc_type):
        return data
    kwargs = {}
    for fld in dc_type.__dataclass_fields__.values():
        val = data.get(fld.name)
        if is_dataclass(fld.type) and isinstance(val, dict):
            val = _dataclass_from_dict(fld.type, val)
        elif getattr(fld.type, "__origin__", None) is list and isinstance(val, list):
            inner = fld.type.__args__[0]
            val = [_dataclass_from_dict(inner, v) for v in val]
        kwargs[fld.name] = val
    return dc_type(**kwargs)


# ────────── local fallback (unchanged) ──────────
def _local_parse(file_bytes: bytes, supabase) -> dict:
    logger.info("🔄  Falling back to local extraction pipeline")
    resume_text, _ = extract_text_from_document(
        file=io.BytesIO(file_bytes), file_path="resume"
    )
    if not resume_text.strip():
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            resume_text = "\n".join(p.get_text() for p in doc)
        except Exception:
            resume_text = ""

    ros = supabase.table("medical_specialty_rosetta").select("*").execute()
    loc = supabase.table("medical_specialty").select("*").execute()

    kwargs = dict(
        resume_text=resume_text,
        rosetta_medical_specialties=ros,
        local_medical_specialties=loc,
    )
    if "resume_image_base64" in inspect.signature(run_model).parameters:
        # only PDF pages currently scanned for head-shot
        kwargs["resume_image_base64"] = _extract_headshot_base64(file_bytes) or ""

    data: UserData = run_model(**kwargs)  # type: ignore[arg-type]
    raw = asdict(data)

    # normalise missing sections to lists
    for key in (
        "experiences",
        "educations",
        "languages",
        "certifications",
        "publications",
        "scores",
    ):
        raw.setdefault(key, [])
        if raw[key] is None:
            raw[key] = []

    return raw


# ────────── public entry point ──────────
def extract_profile_from_resume(file_path: str, environment: str = None) -> Tuple[None, dict]:
    logger.info(f"Starting extract_profile_from_resume for file: {file_path}, environment: {environment or 'default'}")
    
    # Verify environment variables first
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_PRIVATE_SERVICE_ROLE_KEY")
    
    if not supabase_url:
        error_msg = "SUPABASE_URL environment variable is not set"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    if not supabase_key:
        error_msg = "SUPABASE_PRIVATE_SERVICE_ROLE_KEY environment variable is not set"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Supabase URL is set: {supabase_url[:8]}...{supabase_url[-4:] if len(supabase_url) > 8 else ''}")
    logger.info(f"Supabase key is set: {supabase_key[:5]}...{supabase_key[-4:] if len(supabase_key) > 8 else ''}")
    
    try:
        supabase = create_client(options={"admin": True}, environment=environment)
        logger.info("Supabase client created successfully")
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}", exc_info=True)
        raise

    try:
        # Try to list buckets to verify connectivity
        try:
            buckets = supabase.storage.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            logger.info(f"Successfully connected to Supabase. Available buckets: {bucket_names}")
        except Exception as e:
            logger.error(f"Failed to list Supabase buckets: {e}", exc_info=True)
        
        blob = download_file(supabase, file_path)
        if blob is None:
            logger.error(f"File not found in Supabase: {file_path}")
            raise FileNotFoundError(file_path)
        logger.info(f"Successfully downloaded file from Supabase, size: {len(blob.getvalue())} bytes")
    except Exception as e:
        logger.error(f"Error downloading file from Supabase: {e}", exc_info=True)
        raise

    file_bytes = blob.getvalue()
    suffix = Path(file_path).suffix.lower()
    logger.info(f"Processing file with extension: {suffix}")

    # ── 1 Vision/GPT pipeline ───────────
    # The OpenAI model will detect the language and translate non-English resumes to English
    # This is handled in the SYSTEM_MESSAGE prompt which instructs the model to:
    # 1. Detect the resume's language
    # 2. Translate all content to English if needed
    # 3. Set detected_language and was_translated fields accordingly
    raw_openai_data = {} # Initialize in case of exception
    try:
        raw_openai_data = _ask_openai_with_images(file_bytes, suffix)
        logger.info(f"OpenAI vision processing {'succeeded' if raw_openai_data and raw_openai_data.get('profile') else 'failed'}")
        logger.debug(f"Raw data from OpenAI: {json.dumps(raw_openai_data, indent=2)}")
    except Exception as e:
        logger.error(f"OpenAI vision processing error: {e}", exc_info=True)
        # raw_openai_data will be {} if an error occurs during OpenAI call

    # ── 4 Pick / validate head‑shot using our own extraction only, ignoring any OpenAI provided photo
    # Extract a profile photo using our own logic, ignoring any OpenAI provided photo
    photo_b64 = _extract_best_profile_photo(file_bytes)
    logger.info(f"Profile photo extraction {'succeeded' if photo_b64 else 'failed'}")

    # Attach the photo to the response
    _attach_photo(raw_openai_data, photo_b64)
    logger.info(f"After photo attachment, photo_base64 is {'set' if photo_b64 else 'not set'}")

    # Log structured information about key fields for debugging
    _log_key_fields(raw_openai_data)
    
    # Log the final data that will be sent to the frontend
    # Remove the actual photo content from the log to avoid excessive log size
    log_data = copy.deepcopy(raw_openai_data)
    if "photo_base64" in log_data and log_data["photo_base64"]:
        log_data["photo_base64"] = f"[BASE64 IMAGE: {len(log_data['photo_base64'])} chars]"
    if "avatarPreviewUrl" in log_data and log_data["avatarPreviewUrl"]:
        log_data["avatarPreviewUrl"] = "[IMAGE URL]"
    if "profile" in log_data and isinstance(log_data["profile"], dict) and "photo_base64" in log_data["profile"] and log_data["profile"]["photo_base64"]:
        log_data["profile"]["photo_base64"] = f"[BASE64 IMAGE: {len(log_data['profile']['photo_base64'])} chars]"
    
    logger.info("Data being sent to frontend:")
    logger.info(json.dumps(log_data, indent=2, default=json_serializer))
    
    # Return the (potentially photo-augmented) OpenAI data directly
    return None, raw_openai_data


def _log_key_fields(data: dict) -> None:
    """Log key fields from the extracted data for debugging purposes."""
    # Check if data exists
    if not data:
        logger.warning("No data available to log key fields")
        return
    
    try:
        # Log language detection information
        if "detected_language" in data:
            logger.info(f"Detected language: {data.get('detected_language', 'Not specified')}")
            logger.info(f"Translation performed: {data.get('was_translated', False)}")
        
        # Log profile information
        if "profile" in data and isinstance(data["profile"], dict):
            profile = data["profile"]
            name_parts = []
            if profile.get("title"):
                name_parts.append(profile["title"])
            if profile.get("first_name"):
                name_parts.append(profile["first_name"])
            if profile.get("last_name"):
                name_parts.append(profile["last_name"])
            
            logger.info(f"Profile: {' '.join(name_parts)}")
            if profile.get("position"):
                logger.info(f"Position: {profile.get('position')}")
            if profile.get("country"):
                logger.info(f"Country: {profile.get('country')}")
            if profile.get("citizenships"):
                logger.info(f"Citizenship(s): {profile.get('citizenships')}")
                
        # Log number of experiences and countries
        if "experiences" in data and isinstance(data["experiences"], list):
            exp_count = len(data["experiences"])
            countries = set()
            
            for exp in data["experiences"]:
                if isinstance(exp, dict) and exp.get("country"):
                    countries.add(exp["country"])
                    
            logger.info(f"Experiences: {exp_count}, Countries: {', '.join(countries) if countries else 'None'}")
        
        # Log number of educations and countries
        if "educations" in data and isinstance(data["educations"], list):
            edu_count = len(data["educations"])
            countries = set()
            degree_types = set()
            
            for edu in data["educations"]:
                if isinstance(edu, dict):
                    if edu.get("country"):
                        countries.add(edu["country"])
                    if edu.get("degree_type"):
                        degree_types.add(edu["degree_type"])
                    
            logger.info(f"Educations: {edu_count}, Countries: {', '.join(countries) if countries else 'None'}")
            logger.info(f"Degree types: {', '.join(degree_types) if degree_types else 'None'}")
        
        # Log scores if available
        if "scores" in data and isinstance(data["scores"], dict):
            scores = data["scores"]
            logger.info(f"Scores - Completion: {scores.get('completion_score', 'N/A')}, " 
                       f"Data Strength: {scores.get('data_strength_score', 'N/A')}, "
                       f"Healthcare Confidence: {scores.get('healthcare_confidence', 'N/A')}")
            
            if "messages" in scores and isinstance(scores["messages"], list):
                for msg in scores["messages"]:
                    logger.info(f"Score message: {msg}")
    
    except Exception as e:
        logger.warning(f"Error logging key fields: {e}")


# ────────── CLI convenience ──────────
def main():
    p = argparse.ArgumentParser(description="Parse a resume into structured JSON.")
    p.add_argument("file_path", help="Path inside Supabase storage")
    args = p.parse_args()
    _, profile = extract_profile_from_resume(args.file_path)
    print(json.dumps(profile, indent=2))


# Add a debugging helper to save images for inspection
def _save_debug_image(b64_str: str, label: str) -> None:
    """Save a base64 image to a file for debugging purposes. Only active if DEBUG_IMAGES=1 env var is set."""
    if not os.environ.get("DEBUG_IMAGES", "0") == "1":
        return
    
    try:
        debug_dir = os.path.join(os.getcwd(), "debug_images")
        os.makedirs(debug_dir, exist_ok=True)
        
        # Create a unique filename based on timestamp
        timestamp = int(time.time() * 1000)
        filename = os.path.join(debug_dir, f"{label}_{timestamp}.png")
        
        # Decode and save the image
        with open(filename, "wb") as f:
            f.write(base64.b64decode(b64_str))
            
        logger.debug(f"Saved debug image to {filename}")
    except Exception as e:
        logger.debug(f"Failed to save debug image: {e}")


if __name__ == "__main__":
    main()