"""
Article processing module for news scraping service.

This module provides functions to:
- Process article data (deduplication, HTML stripping, encoding enforcement)
- Validate article data (required fields, content length, format)
- Store articles as JSON files with metadata
- Handle IO errors gracefully
"""

import json
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
from html import unescape
import unicodedata

from logger import get_logger
from config import load_config
from utils import generate_content_hash, normalize_text

                   
logger = get_logger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects."""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'isoformat'):                                      
            return obj.isoformat()
        elif hasattr(obj, 'strftime'):                       
            return obj.strftime('%Y-%m-%d')
        elif hasattr(obj, 'total_seconds'):                            
            return str(obj)
        return super().default(obj)


class ProcessorError(Exception):
    """Base exception for processor operations."""
    pass


class ValidationError(ProcessorError):
    """Exception raised when article validation fails."""
    pass


class StorageError(ProcessorError):
    """Exception raised when article storage fails."""
    pass


def process_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process article data by normalizing fields and enforcing encoding.
    
    Args:
        article: Raw article data dictionary
        
    Returns:
        Dict: Processed article data
        
    Raises:
        ProcessorError: If processing fails
    """
    try:
        logger.debug(f"Processing article: {article.get('title', 'Unknown')}")
        
                                                   
        processed = {}
        
                                                                        
        for key, value in article.items():
            if value is not None:                    
                processed[key] = value
        
                                                      
        for key, value in processed.items():
            if isinstance(value, str):
                try:
                                                  
                    processed[key] = unicodedata.normalize('NFKC', value)
                                                  
                    processed[key] = value.encode('utf-8', errors='ignore').decode('utf-8')
                except (UnicodeError, AttributeError) as e:
                    logger.warning(f"Encoding issue with field '{key}': {e}")
                    processed[key] = str(value)                                 
        
                                            
        if 'text' in processed and processed['text']:
            processed['content_hash'] = generate_content_hash(processed['text'])
        
                                  
        processed['processed_at'] = datetime.now().isoformat()
        
        logger.debug(f"Successfully processed article: {processed.get('title', 'Unknown')}")
        return processed
        
    except Exception as e:
        logger.error(f"Error processing article: {e}")
        raise ProcessorError(f"Failed to process article: {e}")


def validate_article(article: Dict[str, Any]) -> bool:
    """
    Validate article data for required fields, content length, and format.
    
    Args:
        article: Article data dictionary
        
    Returns:
        bool: True if valid, False otherwise
        
    Raises:
        ValidationError: If validation encounters an error
    """
    try:
        config = load_config()
        
                               
        required_keys = {'url', 'title', 'text', 'date_publish'}
        missing_keys = required_keys - set(article.keys())
        
        if missing_keys:
            logger.warning(f"Article missing required fields: {missing_keys}")
            return False
        
                                                          
        for key in required_keys:
            if key == 'text' and not article[key]:
                                                          
                article['text'] = f"Article from {article.get('domain', 'unknown domain')}. Full text extraction failed. This is a metadata-only article with title: {article.get('title', 'No title')}. The complete article content can be accessed at the provided URL."
                logger.debug(f"Added placeholder text for article with failed extraction: {article.get('url', 'unknown')}")
            elif not article[key] or (isinstance(article[key], str) and not article[key].strip()):
                logger.warning(f"Article has empty required field: {key}")
                return False
        
                                               
        if article['text'].startswith("Article from") and len(article['text']) < config.min_article_length:
            logger.warning(f"Metadata-only article too short even with placeholder: {len(article['text'])} chars")
            return False
        text_length = len(article['text']) if article['text'] else 0
        if text_length < config.min_article_length:
            logger.warning(f"Article too short: {text_length} chars (min: {config.min_article_length})")
            return False
        
                                                                                  
        
        
        
                                                                    
        language = article.get('language')
        if language:
            logger.debug(f"Article language: {language}")
                                                       
        
                             
        url = article.get('url', '')
        if not url.startswith(('http://', 'https://')):
            logger.warning(f"Invalid URL format: {url}")
            return False
        
        logger.debug(f"Article validation successful: {article.get('title', 'Unknown')}")
        return True
        
    except Exception as e:
        logger.error(f"Error validating article: {e}")
        raise ValidationError(f"Failed to validate article: {e}")


def store_articles(articles: List[Dict[str, Any]], rejected_articles: List[Dict[str, Any]] = None) -> tuple[Optional[Path], Optional[Path], Optional[Path], Optional[Path]]:
    """
    Store articles as newline-delimited JSON in timestamped files.
    
    Creates 4 files:
    1. articles_{timestamp}.json - Valid articles that passed all validation (formatted JSON)
    2. metadata_{timestamp}.json - Metadata for valid articles
    3. rejected_articles_{timestamp}.json - Articles that failed validation/processing (formatted JSON)
    4. rejected_metadata_{timestamp}.json - Metadata for rejected articles
    
    Args:
        articles: List of article dictionaries to store (valid articles)
        rejected_articles: List of rejected article dictionaries (optional)
        
    Returns:
        tuple: (articles_file, articles_metadata_file, rejected_file, rejected_metadata_file)
        
    Raises:
        StorageError: If storage fails critically
    """
    if not articles:
        logger.warning("No articles to store")
        return None
    
    config = load_config()
    storage_dir = config.storage_dir
    
                                     
    try:
        storage_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create storage directory {storage_dir}: {e}")
        raise StorageError(f"Cannot create storage directory: {e}")
    
                                    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]                        
    articles_filename = storage_dir / f"articles_{timestamp}.json"
    articles_metadata_filename = storage_dir / f"metadata_{timestamp}.json"
    
                                                  
    if rejected_articles is None:
        rejected_articles = []
    
    rejected_filename = None
    rejected_metadata_filename = None
    
    if rejected_articles:
        rejected_filename = storage_dir / f"rejected_articles_{timestamp}.json"
        rejected_metadata_filename = storage_dir / f"rejected_metadata_{timestamp}.json"
    
                      
    stored_count = 0
    failed_count = 0
    failed_articles = []
    
    logger.info(f"Storing {len(articles)} valid articles to {articles_filename}")
    if rejected_articles:
        logger.info(f"Storing {len(rejected_articles)} rejected articles to {rejected_filename}")
    
                          
    try:
        with open(articles_filename, 'w', encoding='utf-8') as f:
                                                          
            json.dump(articles, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
            stored_count = len(articles)
        
                                        
        logger.info(f"Successfully stored {stored_count} valid articles to {articles_filename}")
        
        if failed_count > 0:
            logger.warning(f"Failed to store {failed_count} valid articles")
                                            
            for failure in failed_articles:
                logger.warning(f"Failed valid article {failure['index']}: "
                             f"{failure['title']} - {failure['error']}")
        
                                                    
        valid_metadata = {
            'timestamp': datetime.now().isoformat(),
            'file_type': 'valid_articles',
            'total_articles': len(articles),
            'stored_count': stored_count,
            'failed_count': failed_count,
            'filename': str(articles_filename),
            'failed_articles': failed_articles
        }
        
                                            
        try:
            with open(articles_metadata_filename, 'w', encoding='utf-8') as f:
                json.dump(valid_metadata, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
            logger.debug(f"Stored valid articles metadata to {articles_metadata_filename}")
        except Exception as e:
            logger.warning(f"Failed to store valid articles metadata: {e}")
        
                                        
        rejected_stored_count = 0
        rejected_failed_count = 0
        rejected_failed_articles = []
        
        if rejected_articles and rejected_filename:
            try:
                with open(rejected_filename, 'w', encoding='utf-8') as f:
                                                                           
                    json.dump(rejected_articles, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
                    rejected_stored_count = len(rejected_articles)
                
                logger.info(f"Successfully stored {rejected_stored_count} rejected articles to {rejected_filename}")
                
                if rejected_failed_count > 0:
                    logger.warning(f"Failed to store {rejected_failed_count} rejected articles")
                    for failure in rejected_failed_articles:
                        logger.warning(f"Failed rejected article {failure['index']}: "
                                     f"{failure['title']} - {failure['error']}")
                
                                                               
                rejected_metadata = {
                    'timestamp': datetime.now().isoformat(),
                    'file_type': 'rejected_articles',
                    'total_articles': len(rejected_articles),
                    'stored_count': rejected_stored_count,
                    'failed_count': rejected_failed_count,
                    'filename': str(rejected_filename),
                    'failed_articles': rejected_failed_articles
                }
                
                                                       
                try:
                    with open(rejected_metadata_filename, 'w', encoding='utf-8') as f:
                        json.dump(rejected_metadata, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
                    logger.debug(f"Stored rejected articles metadata to {rejected_metadata_filename}")
                except Exception as e:
                    logger.warning(f"Failed to store rejected articles metadata: {e}")
                    
            except IOError as e:
                logger.error(f"IO error storing rejected articles to {rejected_filename}: {e}")
                rejected_filename = None
                rejected_metadata_filename = None
        
        return articles_filename, articles_metadata_filename, rejected_filename, rejected_metadata_filename
        
    except IOError as e:
        logger.error(f"IO error storing valid articles to {articles_filename}: {e}")
                                      
        try:
            if articles_filename.exists():
                articles_filename.unlink()
                logger.info(f"Cleaned up partial file {articles_filename}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to cleanup partial file: {cleanup_error}")
        
        raise StorageError(f"Failed to store valid articles: {e}")
    
    except Exception as e:
        logger.error(f"Unexpected error storing valid articles: {e}")
        raise StorageError(f"Unexpected storage error: {e}")

