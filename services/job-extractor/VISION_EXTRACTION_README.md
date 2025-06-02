# Vision-Based PDF Extraction for Job Extractor

## Overview

This enhancement adds robust PDF extraction capabilities to the job-extractor service, including support for image-based PDFs (scanned documents) using OpenAI's Vision API.

## Changes Made

### 1. New Vision Extractor Module (`utils/files/vision_extractor.py`)
- Converts PDF pages to images for vision processing
- Uses OpenAI's `gpt-4o-mini` model for text extraction from images
- Supports rendering text files and DOCX as images for consistent processing
- Implements smart fallback: tries direct text extraction first, falls back to vision API only when needed

### 2. Enhanced PDF Extraction (`utils/files/doc_converters.py`)
- Modified `extract_text_from_pdf()` to automatically fall back to vision API when direct text extraction yields insufficient content
- Maintains backward compatibility - works exactly as before for text-based PDFs
- Only uses vision API when necessary (cost-efficient)

### 3. Dependencies
- Added `Pillow==11.0.0` to requirements.txt for image processing capabilities

### 4. Improved Logging
- Added detailed logging for debugging extraction process
- Logs vision API usage and estimated costs
- Better error messages for troubleshooting

## How It Works

1. **Text-based PDFs** (normal PDFs with selectable text):
   - Uses PyMuPDF for direct text extraction (fast, free)
   - No API calls, no additional costs

2. **Image-based PDFs** (scanned documents, PDFs with text as images):
   - Detects when direct extraction yields minimal text
   - Converts PDF pages to PNG images
   - Sends images to OpenAI Vision API for text extraction
   - Same approach as resume-parser for consistency

## Cost Implications

- **No additional costs** for regular text-based PDFs
- **Vision API costs** only for image-based PDFs (approximately $0.01 per page)
- Efficient: only uses vision API when necessary

## Testing

To test the implementation:

1. **Text-based PDF**: Upload any regular PDF job posting - should extract instantly without API calls
2. **Image-based PDF**: Upload a scanned job posting - will use vision API and log the usage
3. **Monitor logs**: Look for "Vision API usage" messages to confirm when it's being used

## Environment Variables

The implementation respects existing environment variables:
- `OPENAI_API_KEY`: Required for vision API
- `OPENAI_PARSER_MODEL`: Defaults to `gpt-4o-mini`
- `JOB_PAGES_LIMIT`: Maximum pages to process (default: 10)
- `JOB_DPI`: Image quality for vision processing (default: 150)