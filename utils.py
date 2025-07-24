"""
Utility functions for the news scraping service.
"""

import re
import time
import hashlib
from typing import Any, Optional
from datetime import datetime
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
    # Parse URL and get domain
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # Remove common prefixes
    domain = re.sub(r'^www\.', '', domain)
    
    # Replace special characters with underscores
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
    
    # Remove extra whitespace and normalize line breaks
    normalized = re.sub(r'\s+', ' ', text.strip())
    return normalized


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain string or None if invalid URL
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return None


def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


def timestamp_to_datetime(timestamp: Any) -> Optional[datetime]:
    """
    Convert various timestamp formats to datetime.
    
    Args:
        timestamp: Timestamp in various formats
        
    Returns:
        Datetime object or None if conversion fails
    """
    if timestamp is None:
        return None
    
    try:
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, str):
            # Try ISO format first
            try:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                # Try parsing common formats
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d',
                    '%d/%m/%Y %H:%M:%S',
                    '%d/%m/%Y',
                ]
                for fmt in formats:
                    try:
                        return datetime.strptime(timestamp, fmt)
                    except ValueError:
                        continue
        return None
    except Exception:
        return None


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to specified length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in MB
    """
    try:
        import os
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0
