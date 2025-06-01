import io
import pytest
from pathlib import Path

from utils.files.doc_converters import (
    extract_text_from_document,
    extract_text_from_docx,
    extract_text_from_odt,
    extract_text_from_pdf,
    get_file_extension,
)

text_to_find = "Dr. Benjamin Tan Wei Sheng"


def sample_resume(file_extension: str):
    """Load a real resume"""
    pdf_path = (
        Path(__file__).parent
        / f"../assets/resume/cv_primary_care_doctor.{file_extension}"
    )
    with open(pdf_path.resolve(), "rb") as f:
        return io.BytesIO(f.read())


def test_get_file_extension():
    assert get_file_extension("document.pdf") == "pdf"
    assert get_file_extension("report.DOCX") == "docx"
    assert get_file_extension("notes.txt") == "txt"
    assert get_file_extension("/some_path/notes.doc") == "doc"
    assert get_file_extension("archive.tar.gz") == "gz"


def test_extract_text_from_pdf():
    file = sample_resume("pdf")
    text = extract_text_from_pdf(file)
    assert text_to_find in text


def test_extract_text_from_docx():
    file = sample_resume("docx")
    text = extract_text_from_docx(file)
    assert text_to_find in text


def test_extract_text_from_odt():
    file = sample_resume("odt")
    text = extract_text_from_odt(file)
    assert text_to_find in text


def test_extract_text_from_document():
    assert (
        text_to_find in extract_text_from_document(sample_resume("pdf"), "file.pdf")[0]
    )
    assert (
        text_to_find
        in extract_text_from_document(sample_resume("docx"), "file.docx")[0]
    )
    assert (
        text_to_find in extract_text_from_document(sample_resume("odt"), "file.odt")[0]
    )
    assert (
        text_to_find in extract_text_from_document(sample_resume("txt"), "file.txt")[0]
    )


def test_extract_text_from_document_invalid():
    """Test unsupported file formats."""
    invalid_file = io.BytesIO(b"Fake binary data")
    with pytest.raises(ValueError, match="Unsupported file type: unknown"):
        extract_text_from_document(invalid_file, "file.unknown")


def test_extract_text_from_document_old_doc():
    """Test error on old .doc format."""
    file = sample_resume("doc")
    with pytest.raises(ValueError, match="Old .doc format is not supported"):
        extract_text_from_document(file, "file.doc")
