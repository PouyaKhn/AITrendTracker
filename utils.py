"""
Utility functions for the news scraping service.
"""

import re
import time
import hashlib
from typing import Optional
from urllib.parse import urlparse

from logger import get_logger


def rate_limit(delay_seconds: float, last_request_time: float) -> None:
    """
    Apply rate limiting by waiting if necessary.
    
    Args:
        delay_seconds: Minimum delay between requests
        last_request_time: Timestamp of last request
    """
    elapsed = time.time() - last_request_time
    if elapsed < delay_seconds:
        sleep_time = delay_seconds - elapsed
        time.sleep(sleep_time)


def sanitize_filename(url: str) -> str:
    """
    Convert a URL to a safe filename.
    
    Args:
        url: URL to convert
        
    Returns:
        Safe filename string
    """
                              
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
                            
    domain = re.sub(r'^www\.', '', domain)
    
                                                 
    safe_name = re.sub(r'[^\w\-_\.]', '_', domain)
    
    return safe_name


def generate_content_hash(content: str) -> str:
    """
    Generate a hash for content deduplication.
    
    Args:
        content: Text content to hash
        
    Returns:
        MD5 hash string
    """
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def normalize_text(text: Optional[str]) -> Optional[str]:
    """
    Normalize text content by removing extra whitespace.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text or None
    """
    if not text:
        return None
    
                                                       
    normalized = re.sub(r'\s+', ' ', text.strip())
    return normalized



