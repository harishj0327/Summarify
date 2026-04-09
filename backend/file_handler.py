"""
file_handler.py - Handles file upload and text extraction
Supports: PDF, DOCX, and TXT file formats
"""

import os
from PyPDF2 import PdfReader
from docx import Document


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text content from uploaded files.
    
    Args:
        file_path: Path to the uploaded file
        
    Returns:
        Extracted text as a string
        
    Raises:
        ValueError: If the file format is not supported
        FileNotFoundError: If the file does not exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get file extension (lowercase)
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    if extension == ".pdf":
        return _extract_from_pdf(file_path)
    elif extension == ".docx":
        return _extract_from_docx(file_path)
    elif extension == ".txt":
        return _extract_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {extension}. Supported: PDF, DOCX, TXT")


def _extract_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file using PyPDF2."""
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        raise ValueError(f"Error reading PDF file: {str(e)}")

    if not text.strip():
        raise ValueError("Could not extract text from PDF. The file may be scanned or image-based.")

    return text.strip()


def _extract_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file using python-docx."""
    text = ""
    try:
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text += paragraph.text + "\n"
    except Exception as e:
        raise ValueError(f"Error reading DOCX file: {str(e)}")

    if not text.strip():
        raise ValueError("The DOCX file appears to be empty.")

    return text.strip()


def _extract_from_txt(file_path: str) -> str:
    """Extract text from a plain TXT file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        # Fallback to latin-1 encoding
        with open(file_path, "r", encoding="latin-1") as f:
            text = f.read()
    except Exception as e:
        raise ValueError(f"Error reading TXT file: {str(e)}")

    if not text.strip():
        raise ValueError("The TXT file appears to be empty.")

    return text.strip()


def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
