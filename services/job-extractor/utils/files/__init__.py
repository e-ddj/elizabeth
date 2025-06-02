"""
File utility modules for handling and processing various document formats.
"""

from .doc_converters import (
    extract_text_from_document,
    extract_text_from_pdf,
    extract_text_from_docx,
    get_file_extension
)

# Vision-based extraction (optional import)
try:
    from .vision_extractor import (
        extract_text_with_vision,
        extract_text_from_pdf_with_fallback,
        pdf_to_vision_chunks,
        file_to_vision_chunks
    )
except ImportError:
    # Vision extractor is optional
    pass