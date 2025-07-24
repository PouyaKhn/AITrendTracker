"""
Configuration settings for the news scraping service.
"""

import os
from pathlib import Path
from typing import List, Dict, Any


class Config:
    """Configuration class for news scraping service."""
    
    def __init__(self):
        """Initialize configuration with default values."""
        # Base directories
        self.project_root = Path(__file__).parent
        self.data_dir = self.project_root / "data"
        self.logs_dir = self.project_root / "logs"
        
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # News sources configuration
        self.news_sources = [
            "https://www.bbc.com/news",
            "https://www.reuters.com",
            "https://www.cnn.com",
            "https://www.theguardian.com/international",
        ]
        
        # Scraping configuration
        self.scrape_interval_minutes = int(os.getenv("SCRAPE_INTERVAL", "60"))
        self.max_articles_per_source = int(os.getenv("MAX_ARTICLES", "50"))
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        
        # Data storage configuration
        self.output_format = os.getenv("OUTPUT_FORMAT", "json")  # json, csv, parquet
        self.data_retention_days = int(os.getenv("DATA_RETENTION_DAYS", "30"))
        
        # AWS configuration (if using S3)
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.s3_bucket = os.getenv("S3_BUCKET")
        self.s3_prefix = os.getenv("S3_PREFIX", "news-data/")
        
        # Logging configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = self.logs_dir / "news_scraper.log"
        
        # Rate limiting
        self.requests_per_minute = int(os.getenv("REQUESTS_PER_MINUTE", "30"))
        self.delay_between_requests = int(os.getenv("DELAY_BETWEEN_REQUESTS", "2"))
    
    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests."""
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        if not self.news_sources:
            raise ValueError("No news sources configured")
        
        if self.scrape_interval_minutes < 1:
            raise ValueError("Scrape interval must be at least 1 minute")
        
        if self.max_articles_per_source < 1:
            raise ValueError("Max articles per source must be at least 1")
        
        return True
