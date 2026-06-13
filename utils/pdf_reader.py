"""
PDF Reader Module
Handles PDF text extraction using PyMuPDF
"""

import fitz  # PyMuPDF
import re
from typing import Tuple, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFReader:
    """
    PDF text extraction handler
    Supports multi-page PDFs and preserves paragraph structure
    """
    
    def __init__(self):
        """Initialize PDF reader"""
        self.supported_formats = ['.pdf']
    
    def extract_text(self, pdf_path: str) -> Tuple[str, int]:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, page_count)
            
        Raises:
            Exception: If PDF cannot be read
        """
        try:
            logger.info(f"Starting text extraction from: {pdf_path}")
            
            # Open PDF
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            
            if page_count == 0:
                raise ValueError("PDF has no pages")
            
            logger.info(f"PDF has {page_count} page(s)")
            
            # Extract text from all pages
            all_text = []
            
            for page_num in range(page_count):
                page = doc[page_num]
                text = page.get_text("text")
                
                if text.strip():
                    # Add page marker
                    all_text.append(f"\n--- Page {page_num + 1} ---\n")
                    all_text.append(text)
            
            doc.close()
            
            # Combine all text
            combined_text = "".join(all_text)
            
            # Clean text
            cleaned_text = self._clean_text(combined_text)
            
            logger.info(f"Extracted {len(cleaned_text)} characters from {page_count} pages")
            
            return cleaned_text, page_count
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep necessary punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\'\"\$\%\@\#\/\\&\*\+\=\_\n]', '', text)
        
        # Normalize newlines
        text = re.sub(r'\n+', '\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def extract_text_by_page(self, pdf_path: str) -> List[str]:
        """
        Extract text from PDF, returning list of page texts
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of text strings, one per page
        """
        try:
            doc = fitz.open(pdf_path)
            page_texts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                cleaned_text = self._clean_text(text)
                page_texts.append(cleaned_text)
            
            doc.close()
            
            return page_texts
            
        except Exception as e:
            logger.error(f"Error extracting text by page: {str(e)}")
            raise Exception(f"Failed to extract text by page: {str(e)}")