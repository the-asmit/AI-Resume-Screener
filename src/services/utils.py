"""Utility functions for file processing."""

import io
from PyPDF2 import PdfReader
from src.core.logging import get_logger


logger = get_logger(__name__)


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_content: The raw bytes of the PDF file
        
    Returns:
        Extracted text content from all pages
        
    Raises:
        Exception: If PDF extraction fails
    """
    try:
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        text_content = ""
        
        for page_num, page in enumerate(pdf_reader.pages, 1):
            text = page.extract_text()
            if text:
                text_content += text + "\n"
        
        if not text_content.strip():
            raise ValueError("No text could be extracted from PDF")
        
        logger.info(f"Extracted {len(text_content)} characters from PDF with {len(pdf_reader.pages)} pages")
        return text_content.strip()
        
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        raise Exception(f"Failed to extract text from PDF: {str(e)}")
