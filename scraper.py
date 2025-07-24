"""
News scraping functionality using news-please library.
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

import requests
from newsplease import NewsPlease
from tqdm import tqdm

from config import Config
from data_handler import DataHandler
from logger import get_logger
from utils import rate_limit, sanitize_filename


class NewsScraper:
    """News scraper class using news-please library."""
    
    def __init__(self, config: Config):
        """Initialize the news scraper."""
        self.config = config
        self.logger = get_logger(__name__)
        self.data_handler = DataHandler(config)
        self.session = requests.Session()
        self.session.headers.update(config.get_headers())
        
        # Rate limiting
        self.last_request_time = 0
        
    def scrape_article(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a single article from URL.
        
        Args:
            url: Article URL to scrape
            
        Returns:
            Dictionary containing article data or None if failed
        """
        try:
            # Apply rate limiting
            rate_limit(self.config.delay_between_requests, self.last_request_time)
            self.last_request_time = time.time()
            
            # Scrape article using news-please
            article = NewsPlease.from_url(url)
            
            if article and article.title:
                article_data = {
                    'url': url,
                    'title': article.title,
                    'text': article.maintext,
                    'date_publish': article.date_publish.isoformat() if article.date_publish else None,
                    'date_download': article.date_download.isoformat() if article.date_download else None,
                    'authors': article.authors,
                    'language': article.language,
                    'source_domain': article.source_domain,
                    'filename': article.filename,
                    'description': article.description,
                    'image_url': article.image_url,
                    'scraped_at': datetime.now().isoformat()
                }
                
                self.logger.debug(f"Successfully scraped article: {article.title}")
                return article_data
            else:
                self.logger.warning(f"Failed to extract article content from {url}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error scraping article from {url}: {e}")
            return None
    
    def discover_article_urls(self, source_url: str, max_articles: int = None) -> List[str]:
        """
        Discover article URLs from a news source.
        
        Args:
            source_url: Base URL of news source
            max_articles: Maximum number of articles to discover
            
        Returns:
            List of article URLs
        """
        try:
            max_articles = max_articles or self.config.max_articles_per_source
            
            # Apply rate limiting
            rate_limit(self.config.delay_between_requests, self.last_request_time)
            self.last_request_time = time.time()
            
            response = self.session.get(
                source_url,
                timeout=self.config.request_timeout
            )
            response.raise_for_status()
            
            # Use news-please to discover articles (this is a simplified approach)
            # In a real implementation, you might want to use more sophisticated
            # URL discovery methods or RSS feeds
            
            # For now, return a placeholder - in real implementation,
            # you would parse the HTML to find article links
            urls = []
            
            self.logger.info(f"Discovered {len(urls)} articles from {source_url}")
            return urls[:max_articles]
            
        except Exception as e:
            self.logger.error(f"Error discovering articles from {source_url}: {e}")
            return []
    
    def scrape_source(self, source_url: str) -> List[Dict[str, Any]]:
        """
        Scrape all articles from a news source.
        
        Args:
            source_url: URL of the news source
            
        Returns:
            List of scraped article data
        """
        self.logger.info(f"Starting to scrape source: {source_url}")
        
        # Discover article URLs
        article_urls = self.discover_article_urls(source_url)
        
        if not article_urls:
            self.logger.warning(f"No articles found for source: {source_url}")
            return []
        
        articles = []
        failed_count = 0
        
        # Scrape each article with progress bar
        with tqdm(article_urls, desc=f"Scraping {source_url}") as pbar:
            for url in pbar:
                article_data = self.scrape_article(url)
                if article_data:
                    articles.append(article_data)
                    pbar.set_postfix({"success": len(articles), "failed": failed_count})
                else:
                    failed_count += 1
                    pbar.set_postfix({"success": len(articles), "failed": failed_count})
        
        self.logger.info(f"Scraped {len(articles)} articles from {source_url} "
                        f"({failed_count} failed)")
        
        return articles
    
    def scrape_all_sources(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape articles from all configured news sources.
        
        Returns:
            Dictionary mapping source URLs to lists of article data
        """
        self.logger.info("Starting to scrape all news sources")
        start_time = datetime.now()
        
        all_articles = {}
        total_articles = 0
        
        for source_url in self.config.news_sources:
            try:
                articles = self.scrape_source(source_url)
                all_articles[source_url] = articles
                total_articles += len(articles)
                
                # Save articles for this source
                if articles:
                    source_name = sanitize_filename(source_url)
                    self.data_handler.save_articles(articles, f"{source_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                
            except Exception as e:
                self.logger.error(f"Error scraping source {source_url}: {e}")
                all_articles[source_url] = []
        
        duration = datetime.now() - start_time
        self.logger.info(f"Completed scraping all sources. "
                        f"Total articles: {total_articles}, Duration: {duration}")
        
        return all_articles
    
    def cleanup_old_data(self):
        """Clean up old data files based on retention policy."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.data_retention_days)
            self.data_handler.cleanup_old_files(cutoff_date)
            self.logger.info(f"Cleaned up data files older than {self.config.data_retention_days} days")
        except Exception as e:
            self.logger.error(f"Error during data cleanup: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        return {
            'total_sources': len(self.config.news_sources),
            'last_scrape_time': getattr(self, 'last_scrape_time', None),
            'data_directory': str(self.config.data_dir),
            'retention_days': self.config.data_retention_days
        }
