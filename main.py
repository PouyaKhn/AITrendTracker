#!/usr/bin/env python3
"""
Main application entry point for the news scraping service.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config
from logger import setup_logger
from scheduler import NewsScheduler
from scraper import NewsScraper


def main():
    """Main application function."""
    # Setup logging
    logger = setup_logger()
    logger.info("Starting news scraping service")
    
    try:
        # Initialize configuration
        config = Config()
        
        # Initialize scraper
        scraper = NewsScraper(config)
        
        # Initialize and start scheduler
        scheduler = NewsScheduler(scraper, config)
        scheduler.start()
        
        logger.info("News scraping service started successfully")
        
        # Keep the main thread alive
        try:
            while True:
                pass
        except KeyboardInterrupt:
            logger.info("Shutting down news scraping service")
            scheduler.stop()
            
    except Exception as e:
        logger.error(f"Failed to start news scraping service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
