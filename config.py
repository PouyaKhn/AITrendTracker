"""
Configuration settings for the news scraping service.

Centralizes all tunable parameters with environment variable overrides
and automatic path creation.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging


                               
_config_instance: Optional['Config'] = None


class Config:
    """Configuration class for news scraping service."""
    
    def __init__(self):
        """Initialize configuration with default values and env overrides."""
                                                 
        self.project_root = Path(__file__).parent
        
                                         
        storage_dir_env = os.getenv("STORAGE_DIR")
        if storage_dir_env:
            self.storage_dir = Path(storage_dir_env)
        else:
            self.storage_dir = self.project_root / "data"
        
                             
        log_path_env = os.getenv("LOG_PATH")
        if log_path_env:
            self.log_path = Path(log_path_env)
        else:
            self.log_path = self.project_root / "logs" / "news_scraper.log"
        
                                     
        self.logs_dir = self.log_path.parent
        
                                                                        
        self.fetch_interval_minutes = int(os.getenv("FETCH_INTERVAL", "1"))
        
                                          
        self.cc_bucket = os.getenv("CC_BUCKET")
        
                                                                       
        self.max_articles = int(os.getenv("MAX_ARTICLES", "0"))
        
                                            
        self.newsapi_key = os.getenv("NEWSAPI_KEY")
        
                                                                            
                                                                  
        
                                                
        self._ensure_paths_exist()
        
                                    
        self.news_sources = self._get_news_sources()
        
                                                   
        self.max_articles_per_source = int(os.getenv("MAX_ARTICLES_PER_SOURCE", "50"))
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.user_agent = os.getenv("USER_AGENT", 
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
                                    
        self.output_format = os.getenv("OUTPUT_FORMAT", "json")                      
        self.data_retention_days = int(os.getenv("DATA_RETENTION_DAYS", "30"))
        
                                     
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.s3_bucket = os.getenv("S3_BUCKET", self.cc_bucket)                         
        self.s3_prefix = os.getenv("S3_PREFIX", "news-data/")
        
                               
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", 
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.log_max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))        
        self.log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
        
                       
        self.requests_per_minute = int(os.getenv("REQUESTS_PER_MINUTE", "30"))
        self.delay_between_requests = float(os.getenv("DELAY_BETWEEN_REQUESTS", "2.0"))
        
                                                            
        self.db_url = os.getenv("DATABASE_URL")
        self.db_pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        
                           
        self.min_article_length = int(os.getenv("MIN_ARTICLE_LENGTH", "700"))
        self.max_article_length = int(os.getenv("MAX_ARTICLE_LENGTH", "1000000"))                                           
        
                                                                                         
        self.content_scope = os.getenv("CONTENT_SCOPE", "all")
        
                             
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.retry_delay = float(os.getenv("RETRY_DELAY", "1.0"))
        
                              
        self.concurrent_requests = int(os.getenv("CONCURRENT_REQUESTS", "5"))
        self.batch_size = int(os.getenv("BATCH_SIZE", "10"))
    
    def _get_news_sources(self) -> List[str]:
        """Get news sources from environment or use defaults."""
        sources_env = os.getenv("NEWS_SOURCES")
        if sources_env:
            return [url.strip() for url in sources_env.split(",") if url.strip()]
        
        return [
            "https://www.bbc.com/news",
            "https://www.reuters.com",
            "https://www.cnn.com",
            "https://www.theguardian.com/international",
        ]
    
    def _ensure_paths_exist(self) -> None:
        """Ensure all required paths exist, creating them if necessary."""
        paths_to_create = [
            self.storage_dir,
            self.logs_dir,
        ]
        
        for path in paths_to_create:
            try:
                path.mkdir(parents=True, exist_ok=True)
                logging.info(f"Ensured path exists: {path}")
            except Exception as e:
                logging.error(f"Failed to create path {path}: {e}")
                raise
    
    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests."""
        return {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        if not self.news_sources:
            raise ValueError("No news sources configured")
        
        if self.fetch_interval_minutes < 1:
            raise ValueError("Fetch interval must be at least 1 minute")
        
        if self.max_articles < 0:
            raise ValueError("Max articles must be at least 0 (0 = unlimited)")
        
        if self.max_articles_per_source < 1:
            raise ValueError("Max articles per source must be at least 1")
        
        if self.request_timeout < 1:
            raise ValueError("Request timeout must be at least 1 second")
        
                                                                                  
        
        if self.concurrent_requests < 1:
            raise ValueError("Concurrent requests must be at least 1")
        
        return True
    
    def get_storage_path(self, filename: str) -> Path:
        """Get full path for a file in the storage directory."""
        return self.storage_dir / filename
    
    def get_log_path(self) -> Path:
        """Get the configured log file path."""
        return self.log_path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            'storage_dir': str(self.storage_dir),
            'log_path': str(self.log_path),
            'fetch_interval_minutes': self.fetch_interval_minutes,
            'cc_bucket': self.cc_bucket,
            'max_articles': self.max_articles,
            'max_articles_per_source': self.max_articles_per_source,
            'news_sources': self.news_sources,
            'output_format': self.output_format,
            'log_level': self.log_level,
            'requests_per_minute': self.requests_per_minute,
            'delay_between_requests': self.delay_between_requests,
        }


def load_config() -> Config:
    """Load configuration with environment variable overrides.
    
    This function implements a singleton pattern to ensure only one
    configuration instance exists throughout the application lifecycle.
    
    Returns:
        Config: Configured instance with all parameters loaded
        
    Example:
        >>> config = load_config()
        >>> print(f"Storage directory: {config.storage_dir}")
        >>> print(f"Fetch interval: {config.fetch_interval_minutes} minutes")
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config()
        _config_instance.validate()
        
                                   
        try:
            logging.info("Configuration loaded successfully")
            logging.info(f"Storage directory: {_config_instance.storage_dir}")
            logging.info(f"Log path: {_config_instance.log_path}")
            logging.info(f"Fetch interval: {_config_instance.fetch_interval_minutes} minutes")
            logging.info(f"Max articles: {_config_instance.max_articles}")
            if _config_instance.cc_bucket:
                logging.info(f"Cloud bucket: {_config_instance.cc_bucket}")
        except Exception:
                                                    
            pass
    
    return _config_instance


def reload_config() -> Config:
    """Force reload of configuration, useful for testing or config changes.
    
    Returns:
        Config: Newly loaded configuration instance
    """
    global _config_instance
    _config_instance = None
    return load_config()



