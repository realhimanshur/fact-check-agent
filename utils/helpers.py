"""
Helper Functions Module
Utility functions for the Fact-Check Agent
"""

import os
import re
from typing import Tuple
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_pdf_file(uploaded_file) -> Tuple[bool, str]:
    """
    Validate uploaded PDF file
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Tuple of (is_valid, message)
    """
    # Check file type
    if not uploaded_file.name.endswith('.pdf'):
        return False, "File must be a PDF"
    
    # Check file size (max 50MB)
    max_size = 50 * 1024 * 1024  # 50MB in bytes
    if uploaded_file.size > max_size:
        return False, f"File size exceeds 50MB limit (size: {uploaded_file.size / 1024 / 1024:.2f}MB)"
    
    # Check if file is empty
    if uploaded_file.size == 0:
        return False, "File is empty"
    
    return True, "File is valid"


def create_directories():
    """Create necessary directories for the application"""
    directories = ['uploads', 'reports', 'assets']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Directory created/verified: {directory}")


def save_uploaded_file(uploaded_file) -> str:
    """
    Save uploaded file to uploads directory
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Path to saved file
    """
    # Sanitize filename
    filename = sanitize_filename(uploaded_file.name)
    
    # Create unique filename
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{timestamp}_{filename}"
    
    # Save file
    filepath = os.path.join('uploads', unique_filename)
    
    with open(filepath, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
    logger.info(f"File saved: {filepath}")
    
    return filepath


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove dangerous characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path separators
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return name + ext


def format_confidence_score(confidence: float) -> str:
    """
    Format confidence score for display
    
    Args:
        confidence: Confidence score (0-100)
        
    Returns:
        Formatted string
    """
    return f"{confidence:.0f}%"


def get_verdict_emoji(verdict: str) -> str:
    """
    Get emoji for verdict
    
    Args:
        verdict: Verification verdict
        
    Returns:
        Emoji string
    """
    emoji_map = {
        'VERIFIED': '✅',
        'INACCURATE': '⚠️',
        'FALSE': '❌',
        'ERROR': '⚫'
    }
    return emoji_map.get(verdict, '❓')


def get_verdict_color(verdict: str) -> str:
    """
    Get CSS class for verdict color
    
    Args:
        verdict: Verification verdict
        
    Returns:
        CSS class name
    """
    color_map = {
        'VERIFIED': 'verified',
        'INACCURATE': 'inaccurate',
        'FALSE': 'false',
        'ERROR': ''
    }
    return color_map.get(verdict, '')


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def clean_url(url: str) -> str:
    """
    Clean and validate URL
    
    Args:
        url: URL string
        
    Returns:
        Cleaned URL
    """
    # Remove whitespace
    url = url.strip()
    
    # Ensure https
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url


def format_date(date_str: str) -> str:
    """
    Format date string for display
    
    Args:
        date_str: Date string
        
    Returns:
        Formatted date string
    """
    from datetime import datetime
    
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return date_str