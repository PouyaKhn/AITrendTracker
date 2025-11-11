"""News fetcher module for processing GDELT news data.

This module provides functions to:
- Fetch fresh worldwide news articles from GDELT DOC 2.0 API
- Extract recent articles from GDELT events data
- Process multiple languages and regions
- Extract full text content using multi-library approach
- Support unlimited mode fetching
- Track domain failures persistently
- Log key events and propagate exceptions
"""

import time
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any, Set
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

                                 
project_root = Path(__file__).parent
import sys
sys.path.insert(0, str(project_root))

from config import load_config
from logger import get_logger
from utils import format_duration, rate_limit
from database import get_database

                                                       
try:
    import gdeltdoc
    import pandas as pd
except ImportError:
    gdeltdoc = None
    pd = None

                          


                   
logger = get_logger(__name__)

                                
class DomainFailureTracker:
    """Tracks domains that fail text extraction persistently across batches."""
    
    def __init__(self, max_failures_per_domain: int = 5):
        self.failed_domains: Set[str] = set()
        self.domain_failure_counts: Dict[str, int] = {}
        self.batch_start_time = datetime.now()
        self.max_failures_per_domain = max_failures_per_domain
        
    def mark_domain_failed(self, domain: str, failure_reason: str = "text_extraction_failed"):
        """Mark a domain as failed for the current batch."""
        if domain not in self.failed_domains:
            self.domain_failure_counts[domain] = 1
            logger.warning(f"Domain {domain} failure 1/{self.max_failures_per_domain}: {failure_reason}")
        else:
            self.domain_failure_counts[domain] += 1
            logger.warning(f"Domain {domain} failure {self.domain_failure_counts[domain]}/{self.max_failures_per_domain}: {failure_reason}")
        
                                                           
        if self.domain_failure_counts[domain] >= self.max_failures_per_domain:
            self.failed_domains.add(domain)
            logger.error(f"Domain {domain} marked as BAD DOMAIN after {self.domain_failure_counts[domain]} failures - will skip all future articles from this domain")
    
    def is_domain_failed(self, domain: str) -> bool:
        """Check if a domain is marked as failed in current batch."""
        return domain in self.failed_domains
    
    def get_domain_failure_count(self, domain: str) -> int:
        """Get the current failure count for a domain."""
        return self.domain_failure_counts.get(domain, 0)
    
    def should_skip_domain(self, domain: str) -> bool:
        """Check if we should skip processing this domain based on failure count."""
        return self.is_domain_failed(domain) or self.get_domain_failure_count(domain) >= self.max_failures_per_domain
    
    def get_failed_domains_report(self) -> Dict[str, Any]:
        """Get a report of failed domains for the current batch."""
        return {
            'failed_domains': list(self.failed_domains),
            'failure_counts': self.domain_failure_counts.copy(),
            'batch_duration': (datetime.now() - self.batch_start_time).total_seconds(),
            'total_failures': len(self.failed_domains)
        }
    
                                                                    
_domain_failure_tracker = DomainFailureTracker()

def get_domain_failure_tracker() -> DomainFailureTracker:
    """Get the global domain failure tracker instance."""
    return _domain_failure_tracker

def reset_domain_failure_tracker():
    """Reset the domain failure tracker for a new batch."""
    global _domain_failure_tracker
                                                                            
    _domain_failure_tracker = DomainFailureTracker()
    logger.info("Domain failure tracker reset for new batch")

def get_domain_failure_report() -> Dict[str, Any]:
    """
    Get a comprehensive report of domain failures for the current batch.
    
    Returns:
        Dict containing failure statistics and details
    """
    tracker = get_domain_failure_tracker()
    return tracker.get_failed_domains_report()

def normalize_domain_for_dedup(domain: str) -> str:
    """
    Normalize domain for duplicate detection by removing subdomains.
    
    Examples:
        edition.cnn.com -> cnn.com
        www.cnn.com -> cnn.com
        cnn.com -> cnn.com
        deadline.com -> deadline.com
    
    Args:
        domain: Domain string (may include subdomain)
        
    Returns:
        Normalized domain (base domain only)
    """
    if not domain:
        return domain
    
    domain = domain.lower().strip()
    if domain.startswith('www.'):
        domain = domain[4:]
    
    parts = domain.split('.')
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    return domain


def _domain_suffix_matches(candidate_domain: str, target_domain: str) -> bool:
    """Return True if candidate_domain is exactly target_domain (no subdomains)."""
    candidate = candidate_domain.lower()
    target = target_domain.lower()
    if candidate.startswith('www.'):
        candidate = candidate[4:]
    if target.startswith('www.'):
        target = target[4:]
    return candidate == target




def _extract_text_advanced(url: str, domain: str) -> Optional[str]:
    """
    Advanced text extraction using multiple specialized libraries with proper encoding handling.
    
    Tries multiple extraction methods in order of sophistication:
    1. Trafilatura (fast general extraction - PRIORITY)
    2. Goose3 (news-specific extraction fallback) 
    3. Newspaper3k (reliable, news-specific fallback)
    4. Readability-lxml (content-focused)
    5. BeautifulSoup (last resort)
    
    Special handling for Journalisten.dk overview pages to extract specific articles by news_band_id.
    
    Args:
        url: Article URL
        domain: Domain name for logging
        
    Returns:
        Extracted text or None if failed
    """
                            
    if not url or not isinstance(url, str):
        logger.debug(f"Invalid URL provided: {url}")
        return None
        
    if not url.startswith(('http://', 'https://')):
        logger.debug(f"URL missing protocol: {url}")
        return None
    
                                                         
    if domain == 'journalisten.dk' and '/nyhedsoverblik' in url and 'news_band_id=' in url:
        logger.info(f"🔍 Detected Journalisten.dk overview page, extracting specific article by news_band_id")
        return _extract_journalisten_specific_article(url, domain)
    
    def _fix_encoding(text: str) -> str:
        """Fix common encoding issues with Danish characters."""
        if not text:
            return text
        
                                                     
        encoding_fixes = {
            'æ': 'æ', 'ø': 'ø', 'å': 'å',
            'Æ': 'Æ', 'Ø': 'Ø', 'Å': 'Å',
                                        
            'Ã¦': 'æ', 'Ã¸': 'ø', 'Ã¥': 'å',
            'Ã†': 'Æ', 'Ã˜': 'Ø', 'Ã…': 'Å',
                                     
            'Ã©': 'é', 'Ã¨': 'è', 'Ã ': 'à',
            'Ã¼': 'ü', 'Ã¶': 'ö', 'Ã¤': 'ä'
        }
        
        for wrong, correct in encoding_fixes.items():
            text = text.replace(wrong, correct)
        
        return text
    
                                                                
    try:
        import trafilatura
        import logging
        
                                                                                   
        trafilatura_logger = logging.getLogger('trafilatura.downloads')
        original_level = trafilatura_logger.level
        trafilatura_logger.setLevel(logging.CRITICAL)                                                     
        
        try:
                                                             
            if not url or not url.startswith(('http://', 'https://')):
                logger.debug(f"Invalid URL format: {url}")
                return None
                
                                                       
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                                            
                text = trafilatura.extract(downloaded, 
                                        include_comments=False, 
                                        include_tables=False,
                                        include_formatting=False)
                if text and len(text.strip()) > 200:
                    text = _fix_encoding(text.strip())
                    logger.info(f"✓ TRAFILATURA extracted {len(text)} chars from {domain}")
                    return text
                else:
                    logger.debug(f"Trafilatura extracted insufficient text from {domain} ({len(text) if text else 0} chars)")
            else:
                logger.debug(f"Trafilatura could not download content from {domain} (404 or network error)")
        finally:
                                            
            trafilatura_logger.setLevel(original_level)
            
    except Exception as e:
        logger.debug(f"Trafilatura extraction failed for {domain}: {e}")
    
                                                          
    try:
        from goose3 import Goose
        
        g = Goose()
        article = g.extract(url=url)
        
        if article.cleaned_text and len(article.cleaned_text.strip()) > 200:
            text = _fix_encoding(article.cleaned_text.strip())
            logger.info(f"✓ GOOSE3 extracted {len(text)} chars from {domain}")
            return text
    except Exception as e:
        logger.debug(f"Goose3 extraction failed for {domain}: {e}")
    
                                                    
    try:
        from newspaper import Article
        
        article = Article(url)
        article.download()
        article.parse()
        
        if article.text and len(article.text.strip()) > 200:
            text = _fix_encoding(article.text.strip())
            logger.info(f"✓ NEWSPAPER3K extracted {len(text)} chars from {domain}")
            return text
    except Exception as e:
        logger.debug(f"Newspaper3k extraction failed for {domain}: {e}")
    
                                                  
    try:
        from readability import Document
        import requests
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
                                                               
        try:
                                                   
            if hasattr(response, 'text') and response.text:
                content = response.text
            else:
                                            
                content = response.content.decode('utf-8', errors='ignore')
            
            doc = Document(content)
            
                                                
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(doc.summary(), 'html.parser')
            text = soup.get_text(strip=True)
            
            if text and len(text.strip()) > 200:
                text = _fix_encoding(text.strip())
                logger.info(f"✓ READABILITY extracted {len(text)} chars from {domain}")
                return text
        except (TypeError, UnicodeDecodeError) as encoding_error:
            logger.debug(f"Readability encoding error for {domain}: {encoding_error}")
                                                 
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text(strip=True)
            
            if text and len(text.strip()) > 200:
                text = _fix_encoding(text.strip())
                logger.info(f"✓ READABILITY fallback extracted {len(text)} chars from {domain}")
                return text
    except Exception as e:
        logger.debug(f"Readability extraction failed for {domain}: {e}")
    
                                                        
    return _extract_text_fallback(url, domain)


def _extract_deadline_title(url: str) -> Optional[str]:
    """
    Extract actual article title from deadline.com when GDELT provides 'Deadline' as title.
    
    Args:
        url: Article URL from deadline.com
        
    Returns:
        Extracted title or None if extraction fails
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title_selectors = [
            'h1.article-title',
            'h1.a-headline',
            'h1[class*="title"]',
            'h1[class*="headline"]',
            'article h1',
            'h1',
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                if title_text and title_text.lower() != 'deadline' and len(title_text) > 5:
                    return title_text
        
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            meta_title_text = meta_title.get('content').strip()
            if meta_title_text and meta_title_text.lower() != 'deadline' and len(meta_title_text) > 5:
                return meta_title_text
        
        return None
        
    except Exception as e:
        logger.debug(f"Failed to extract deadline.com title from {url}: {e}")
        return None


def _extract_text_fallback(url: str, domain: str) -> Optional[str]:
    """
    Text extraction using requests and BeautifulSoup (fallback method).
    
    Args:
        url: Article URL
        domain: Domain name for logging
        
    Returns:
        Extracted text or None if failed
    """
                                                      
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning(f"BeautifulSoup not available for fallback extraction from {domain}")
        return None
        
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
                                          
        for script in soup(["script", "style"]):
            script.decompose()
        
                                        
        content_selectors = [
            'article', 'main', '.content', '.article-content', '.post-content',
            '.entry-content', '.story-content', '.news-content', '.text-content',
            '[role="main"]', '.main-content', '.article-body', '.story-body'
        ]
        
        text_content = ""
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                text_content = ' '.join([elem.get_text(strip=True) for elem in elements])
                if len(text_content) > 100:
                    break
        
                                                     
        if len(text_content) < 100:
            body = soup.find('body')
            if body:
                text_content = body.get_text(strip=True)
        
                           
        if text_content:
                                     
            text_content = ' '.join(text_content.split())
            
                                                       
            def _fix_encoding(text: str) -> str:
                """Fix common encoding issues with Danish characters."""
                if not text:
                    return text
                
                                                             
                encoding_fixes = {
                    'æ': 'æ', 'ø': 'ø', 'å': 'å',
                    'Æ': 'Æ', 'Ø': 'Ø', 'Å': 'Å',
                                                
                    'Ã¦': 'æ', 'Ã¸': 'ø', 'Ã¥': 'å',
                    'Ã†': 'Æ', 'Ã˜': 'Ø', 'Ã…': 'Å',
                                             
                    'Ã©': 'é', 'Ã¨': 'è', 'Ã ': 'à',
                    'Ã¼': 'ü', 'Ã¶': 'ö', 'Ã¤': 'ä'
                }
                
                for wrong, correct in encoding_fixes.items():
                    text = text.replace(wrong, correct)
                
                return text
            
            text_content = _fix_encoding(text_content)
            
            if len(text_content) > 100:
                logger.info(f"✓ BEAUTIFULSOUP fallback: {len(text_content)} chars from {domain}")
                return text_content
        
        return None
        
    except Exception as e:
        logger.debug(f"BeautifulSoup fallback extraction failed for {domain}: {e}")
        return None

def _extract_journalisten_specific_article(url: str, domain: str) -> Optional[str]:
    """
    Extracts specific article content from Journalisten.dk overview pages.
    Uses the correct HTML structure: div id="news-feed-[id]" and div class="news-band__content".
    
    Args:
        url: The URL of the overview page containing news_band_id
        domain: The domain name (e.g., 'journalisten.dk')
        
    Returns:
        Extracted text of the specific article, or None if extraction fails.
    """
    logger.info(f"🔍 Extracting specific article from Journalisten.dk overview page: {url}")
    
    try:
                                           
        parsed_url = urlparse(url)
        query_params = parsed_url.query
        news_band_id = None
        if 'news_band_id=' in query_params:
            news_band_id = query_params.split('news_band_id=')[1].split('&')[0]
            logger.info(f"📋 Found news_band_id: {news_band_id}")
        else:
            logger.warning(f"❌ Could not find news_band_id in URL: {url}")
            return None

                                 
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
                        
        soup = BeautifulSoup(response.content, 'html.parser')
        
                                                                            
                                                     
        target_article_id = f"news-feed-{news_band_id}"
        target_article = soup.find('div', id=target_article_id)
        
        if target_article:
            logger.info(f"✅ Found target article container with id: {target_article_id}")
            
                                                                        
                                                      
            article_content = target_article.find('div', class_='news-band__content')
            
            if article_content:
                logger.info(f"✅ Found article content with class 'news-band__content'")
                
                                                            
                article_text = article_content.get_text(strip=True)
                
                if article_text and len(article_text) > 100:
                                       
                    lines = article_text.split('\n')
                    cleaned_lines = []
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 10:                               
                            cleaned_lines.append(line)
                    
                    final_text = '\n'.join(cleaned_lines)
                    logger.info(f"✅ Successfully extracted {len(final_text)} chars from specific article using correct selectors")
                    return final_text
                else:
                    logger.warning(f"❌ Article content too short: {len(article_text) if article_text else 0} chars")
            else:
                logger.warning(f"❌ Could not find article content with class 'news-band__content' in article {target_article_id}")
        else:
            logger.warning(f"❌ Could not find target article container with id: {target_article_id}")
        
        return None

    except Exception as e:
        logger.warning(f"❌ Failed to extract specific article from Journalisten.dk overview page {url}: {e}")
        return None

                                                            
                                                            
RELIABLE_NEWS_DOMAINS = [
                                                         
    'reuters.com',
    'bbc.com',
    'theguardian.com',
    'cnn.com',
    'npr.org',
    'nbcnews.com',
    'abcnews.go.com',
    'cbsnews.com',
    'msnbc.com',
    'foxnews.com',
    'latimes.com',
    'theglobeandmail.com',
    'washingtonpost.com',
    'usatoday.com',
    'nationalpost.com',
    'adweek.com',
    'adage.com',
    'thedrum.com',
    'campaignlive.com',
    'cjr.org',
    'niemanlab.org',
    'poynter.org',
    'pressgazette.co.uk',
    'creativereview.co.uk',
    'commarts.com',
    'itsnicethat.com',
    'eyeondesign.aiga.org',
    'prweek.com',
    'provokemedia.com',
    'prdaily.com',
    'variety.com',
    'hollywoodreporter.com',
    'indiewire.com',
    'deadline.com',
    'nationalgeographic.com',
    'bjp-online.com',
    'petapixel.com',
    'lensculture.com',
    'smashingmagazine.com',
    'alistapart.com',
    'uxmag.com',
    'nngroup.com',
    'theverge.com',
    'wired.com',
    'mashable.com',
    'digiday.com',
    'contentmarketinginstitute.com',
    
                                                  
    'journalisten.dk',
    'dr.dk',
    'tv2.dk',
    'berlingske.dk',
    'jyllands-posten.dk',
    'ekstrabladet.dk',
    'bt.dk',
    'information.dk',
    'weekendavisen.dk',
    'kristeligt-dagblad.dk',
    'kforum.dk',
    'medietrends.dk',
    'mediawatch.dk',
    'markedsforing.dk',
    'bureaubiz.dk',
    'ekkofilm.dk',
    'digitalfoto.dk',
    'soundvenue.dk',
    'ddc.dk',
    'computerworld.dk',
    'version2.dk',
    'elektronista.dk',
                               
    'politiken.dk',
    'arbejderen.dk',
    'avisen.dk',
    'nordjyske.dk',
    'sn.dk',
    'fyens.dk'
]

                                      

PROBLEMATIC_DOMAINS = [
    'youtube.com', 'vimeo.com', 'dailymotion.com', 'twitch.tv', 'tiktok.com', 
    'facebook.com', 'twitter.com', 'instagram.com', 'deperu.com'
]

                              
                          
def detect_language_from_domain_and_text(domain: str, text: str = "") -> str:
    """Detect language based on domain and text patterns."""
                    
    if domain.endswith('.dk'):
        return 'da'
    
                                    
    if text:
        danish_words = ['danmark', 'dansk', 'københavn', 'aarhus', 'odense', 'og', 'er', 'det', 'den', 'der']
        if any(word in text.lower() for word in danish_words):
            return 'da'
    
                        
    return 'en'

def infer_country_from_domain(domain: str) -> str:
    """Infer country from domain extension."""
    if domain.endswith('.dk'):
        return 'DK'
    elif domain.endswith('.com'):
        return 'US'                      
    elif domain.endswith('.co.uk'):
        return 'GB'
    elif domain.endswith('.org'):
        return 'US'                      
    else:
        return 'unknown'

                                          

                               
DOMAIN_CATEGORIES = {
                                
    'adweek.com': 'advertising and commercial',
    'adage.com': 'advertising and commercial',
    'thedrum.com': 'advertising and commercial',
    'campaignlive.com': 'advertising and commercial',
    'markedsforing.dk': 'advertising and commercial',
    'bureaubiz.dk': 'advertising and commercial',
    
                                
    'reuters.com': 'journalism, news and media',
    'bbc.com': 'journalism, news and media',
    'theguardian.com': 'journalism, news and media',
    'cnn.com': 'journalism, news and media',
    'washingtonpost.com': 'journalism, news and media',
    'npr.org': 'journalism, news and media',
    'nbcnews.com': 'journalism, news and media',
    'abcnews.go.com': 'journalism, news and media',
    'cbsnews.com': 'journalism, news and media',
    'msnbc.com': 'journalism, news and media',
    'foxnews.com': 'journalism, news and media',
    'usatoday.com': 'journalism, news and media',
    'latimes.com': 'journalism, news and media',
    'theglobeandmail.com': 'journalism, news and media',
    'nationalpost.com': 'journalism, news and media',
    'cjr.org': 'journalism, news and media',
    'niemanlab.org': 'journalism, news and media',
    'poynter.org': 'journalism, news and media',
    'pressgazette.co.uk': 'journalism, news and media',
    'journalisten.dk': 'journalism, news and media',
    'dr.dk': 'journalism, news and media',
    'tv2.dk': 'journalism, news and media',
    'berlingske.dk': 'journalism, news and media',
    'jyllands-posten.dk': 'journalism, news and media',
    'ekstrabladet.dk': 'journalism, news and media',
    'bt.dk': 'journalism, news and media',
    'information.dk': 'journalism, news and media',
    'weekendavisen.dk': 'journalism, news and media',
    'kristeligt-dagblad.dk': 'journalism, news and media',
    'kforum.dk': 'journalism, news and media',
    'medietrends.dk': 'journalism, news and media',
    'mediawatch.dk': 'journalism, news and media',
                               
    'politiken.dk': 'journalism, news and media',
    'arbejderen.dk': 'journalism, news and media',
    'avisen.dk': 'journalism, news and media',
    'nordjyske.dk': 'journalism, news and media',
    'sn.dk': 'journalism, news and media',
    'fyens.dk': 'journalism, news and media',
    
                                             
    'creativereview.co.uk': 'graphic design and visual communication',
    'commarts.com': 'graphic design and visual communication',
    'itsnicethat.com': 'graphic design and visual communication',
    'eyeondesign.aiga.org': 'graphic design and visual communication',
    
                                    
    'prweek.com': 'strategic communication and PR',
    'provokemedia.com': 'strategic communication and PR',
    'prdaily.com': 'strategic communication and PR',
    
                            
    'variety.com': 'film and TV production',
    'hollywoodreporter.com': 'film and TV production',
    'indiewire.com': 'film and TV production',
    'deadline.com': 'film and TV production',
    'ekkofilm.dk': 'film and TV production',
    
                 
    'nationalgeographic.com': 'photography',
    'bjp-online.com': 'photography',
    'petapixel.com': 'photography',
    'lensculture.com': 'photography',
    'digitalfoto.dk': 'photography',
    
                       
    'smashingmagazine.com': 'web and UX design',
    'alistapart.com': 'web and UX design',
    'uxmag.com': 'web and UX design',
    'nngroup.com': 'web and UX design',
    
                                        
    'soundvenue.dk': 'digital media and content creation',
    'ddc.dk': 'digital media and content creation',
    'theverge.com': 'digital media and content creation',
    'wired.com': 'digital media and content creation',
    'mashable.com': 'digital media and content creation',
    'digiday.com': 'digital media and content creation',
    'contentmarketinginstitute.com': 'digital media and content creation',
    'computerworld.dk': 'digital media and content creation',
    'version2.dk': 'digital media and content creation',
    'elektronista.dk': 'digital media and content creation',
}

def get_domain_category(domain: str) -> str:
    """
    Get the category for a given domain.
    
    Args:
        domain: Domain name (e.g., 'bbc.com', 'dr.dk')
        
    Returns:
        str: Category name or 'Other' if not found
    """
                                                                    
    normalized_domain = domain.lower()
    if normalized_domain.startswith('www.'):
        normalized_domain = normalized_domain[4:]
    
                             
    if normalized_domain in DOMAIN_CATEGORIES:
        return DOMAIN_CATEGORIES[normalized_domain]
    
                                                                                  
    for category_domain, category in DOMAIN_CATEGORIES.items():
        if normalized_domain.endswith('.' + category_domain) or normalized_domain == category_domain:
            return category
    
                                          
    return 'Other'

class FetcherError(Exception):
    """Base exception for fetcher operations."""
    pass


class DownloadError(FetcherError):
    """Exception raised when GDELT API request fails."""
    pass


class ExtractionError(FetcherError):
    """Exception raised when article extraction fails."""
    pass


def get_last_processed_timestamp() -> Optional[str]:
    """Get the timestamp of the last processed article from database."""
    try:
        from database import get_database
        db = get_database()
        return db.get_last_processed_time()
    except Exception as e:
        logger.warning(f"Failed to get last processed timestamp: {e}")
        return None

def fetch_by_domains(processed_urls: Set[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch all available news from major domains using GDELT only.
    Always operates in unlimited mode for the past 2 hours.
    
    Args:
        processed_urls: Set of already processed URLs to skip duplicates
        
    Returns:
        List[Dict]: List of extracted article dictionaries from major domains
    """
    logger.info("🚀 Fetching all available articles from major domains (past 2 hours)")
    
    all_articles = []
    tracker = get_domain_failure_tracker()
    
    try:
                                                                              
        gdelt_domains = [domain for domain in RELIABLE_NEWS_DOMAINS if '.dk' not in domain]
        
        logger.info(f"🔄 Using {len(gdelt_domains)} English domains with GDELT coverage")
        
                                        
        if gdeltdoc and gdelt_domains:
            gd = gdeltdoc.GdeltDoc()
            
            for domain in gdelt_domains:
                try:
                    
                                                        
                    if tracker.should_skip_domain(domain):
                        logger.info(f"⏭️  Skipping failed GDELT domain '{domain}' (failure count: {tracker.get_domain_failure_count(domain)})")
                        continue
                    
                    logger.info(f"🔍 Searching GDELT domain '{domain}' for articles (last 2 hours)")
                    
                                                                                           
                    now = datetime.utcnow()
                    two_hours_ago = now - timedelta(hours=2)
                    
                    filters = gdeltdoc.Filters(
                        domain=domain,
                        start_date=two_hours_ago,
                        end_date=now
                    )
                    
                    df = gd.article_search(filters)
                    
                    if df is not None and not df.empty:
                        logger.info(f"✅ Found {len(df)} articles from GDELT domain {domain}")
                        
                        domain_counter = 0
                        articles_from_domain = 0
                        
                        for _, row in df.iterrows():
                            try:
                                domain_counter += 1
                                logger.info(f"   📄 [{domain_counter}/{len(df)}] Extracting GDELT article {domain_counter} from {domain}...")
                                article = _parse_gdeltdoc_dataframe_row(row, processed_urls)
                                if article:
                                                               
                                    article['fetch_source'] = 'gdelt'
                                    article['gdelt_metadata'] = True
                                    all_articles.append(article)
                                    articles_from_domain += 1
                                    logger.info(f"   ✅ GDELT article {domain_counter} extracted successfully")
                                else:
                                    logger.info(f"   ❌ GDELT article {domain_counter} failed extraction (filtered out)")
                            except Exception as e:
                                logger.debug(f"   ❌ Failed to parse GDELT article {domain_counter} from {domain}: {e}")
                                continue
                        
                                                                                
                        if articles_from_domain > 0:
                            logger.info(f"✅ GDELT domain {domain} working well: {articles_from_domain} articles extracted")
                        else:
                                                                    
                            tracker.mark_domain_failed(domain, "no_valid_articles")
                            logger.warning(f"⚠️  GDELT domain {domain} marked as failed: no valid articles extracted")
                            
                    else:
                        logger.info(f"❌ No articles found from GDELT domain {domain}")
                                                              
                        tracker.mark_domain_failed(domain, "no_articles_found")
                    
                                                             
                        
                                                    
                    time.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"❌ Error fetching from GDELT domain {domain}: {e}")
                                           
                    tracker.mark_domain_failed(domain, f"fetch_error: {str(e)}")
                    continue
        
        
                            
        logger.info(f"🔄 Removing duplicates from {len(all_articles)} articles...")
        unique_articles = _remove_duplicate_articles(all_articles)
        
        logger.info(f"✅ GDELT fetch completed: {len(unique_articles)} articles")
        logger.info(f"📊 GDELT articles: {len([a for a in unique_articles if a.get('fetch_source') == 'gdelt'])}")
        
        return unique_articles
        
    except Exception as e:
        logger.error(f"Error in GDELT fetch: {e}")
        return []


def fetch_danish_news(processed_urls: Set[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch all available Danish news using GDELT only.
    Always operates in unlimited mode for the past 2 hours.
    
    Args:
        processed_urls: Set of already processed URLs to skip duplicates
        
    Returns:
        List[Dict]: List of extracted article dictionaries from Danish domains
    """
    start_time = datetime.now()
    logger.info("🚀 Starting unlimited Danish news fetch (past 2 hours)")
    
    all_articles = []
    tracker = get_domain_failure_tracker()
    
    try:
                                                                             
        gdelt_danish_domains = [domain for domain in RELIABLE_NEWS_DOMAINS if '.dk' in domain]
        
        logger.info(f"🎯 Found {len(gdelt_danish_domains)} Danish domains with GDELT coverage")
        
                                               
        if gdeltdoc and gdelt_danish_domains:
            logger.info("📡 Initializing GDELT DOC client...")
            gd = gdeltdoc.GdeltDoc()
            
            domain_count = 0
            for domain in gdelt_danish_domains:
                domain_count += 1
                domain_start_time = datetime.now()
                
                                                             
                if tracker.should_skip_domain(domain):
                    logger.info(f"⏭️  [{domain_count}/{len(gdelt_danish_domains)}] Skipping GDELT Danish domain '{domain}' - already marked as failed ({tracker.get_domain_failure_count(domain)} failures)")
                    continue
                    
                try:
                    logger.info(f"🔍 [{domain_count}/{len(gdelt_danish_domains)}] Processing GDELT Danish domain '{domain}'...")
                    logger.info(f"📡 Making GDELT API request for {domain}...")
                    
                                                                                           
                    now = datetime.utcnow()
                    two_hours_ago = now - timedelta(hours=2)
                    
                    filters = gdeltdoc.Filters(
                        domain=domain,
                        start_date=two_hours_ago,
                        end_date=now
                    )
                    
                    api_start_time = datetime.now()
                    df = gd.article_search(filters)
                    api_duration = (datetime.now() - api_start_time).total_seconds()
                    
                    logger.info(f"⏱️  API request completed in {api_duration:.2f}s")
                    
                    if df is not None and not df.empty:
                        logger.info(f"✅ Found {len(df)} articles from GDELT Danish domain {domain}")
                        
                        domain_articles = []
                        article_count = 0
                                                                                  
                            
                        logger.info(f"   📊 GDELT Danish domain {domain}: can fetch articles (no per-domain limit)")
                        extraction_start_time = datetime.now()
                        
                        for _, row in df.iterrows():
                                
                            article_count += 1
                            try:
                                logger.info(f"   📄 [{article_count}/{len(df)}] Extracting GDELT Danish article {article_count}...")
                                article = _parse_gdeltdoc_dataframe_row(row, processed_urls)
                                if article:                                                           
                                                               
                                    article['fetch_source'] = 'gdelt'
                                    article['gdelt_metadata'] = True
                                    domain_articles.append(article)
                                    logger.info(f"   ✅ GDELT Danish article {article_count} extracted successfully")
                                    
                                else:
                                    logger.info(f"   ❌ GDELT Danish article {article_count} failed extraction (filtered out)")
                            except Exception as e:
                                logger.debug(f"   ❌ Failed to parse GDELT Danish article {article_count} from {domain}: {e}")
                                continue
                        
                        extraction_duration = (datetime.now() - extraction_start_time).total_seconds()
                        logger.info(f"   ⏱️  GDELT Danish article extraction completed in {extraction_duration:.2f}s")
                        
                                                                  
                        if tracker.should_skip_domain(domain):
                            logger.warning(f"   ⚠️  GDELT Danish domain {domain} failed during processing - discarding {len(domain_articles)} articles")
                                                                   
                        else:
                            all_articles.extend(domain_articles)
                            logger.info(f"   ✅ Added {len(domain_articles)} GDELT Danish articles from {domain}")
                            
                                                                                    
                            if len(domain_articles) > 0:
                                logger.info(f"✅ GDELT Danish domain {domain} working well: {len(domain_articles)} articles extracted")
                            else:
                                                                        
                                tracker.mark_domain_failed(domain, "no_valid_articles")
                                logger.warning(f"⚠️  GDELT Danish domain {domain} marked as failed: no valid articles extracted")
                    else:
                        logger.info(f"   ❌ No articles found from GDELT Danish domain {domain}")
                                                              
                        tracker.mark_domain_failed(domain, "no_articles_found")
                    
                    domain_duration = (datetime.now() - domain_start_time).total_seconds()
                    logger.info(f"   ⏱️  GDELT Danish domain {domain} completed in {domain_duration:.2f}s")
                    logger.info(f"   📊 Total Danish articles so far: {len(all_articles)}")
                        
                                                    
                    logger.info(f"   ⏳ Rate limiting: waiting 1 second...")
                    time.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"❌ Error fetching from GDELT Danish domain {domain}: {e}")
                                           
                    tracker.mark_domain_failed(domain, f"fetch_error: {str(e)}")
                    continue
        
        
                                                        
        logger.info(f"🔄 Removing duplicates from {len(all_articles)} Danish articles...")
        unique_articles = _remove_duplicate_articles(all_articles)
        final_articles = unique_articles
        
        total_duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Danish news fetch COMPLETED in {total_duration:.2f}s")
        logger.info(f"📊 Final results: {len(final_articles)} Danish articles (after deduplication and failure handling)")
        logger.info(f"📊 GDELT Danish articles: {len([a for a in final_articles if a.get('fetch_source') == 'gdelt'])}")
        logger.info(f"📈 Success rate: {len(final_articles)} Danish articles (unlimited mode)")
        logger.info(f"🔄 Final Danish fetch completed")
        
        return final_articles
        
    except Exception as e:
        logger.error(f"Error fetching Danish news: {e}")
        return []

def _parse_gdeltdoc_dataframe_row(row, processed_urls: Set[str] = None) -> Optional[Dict[str, Any]]:
    """
    Parse gdeltdoc DataFrame row into pipeline-compatible format.
    
    Args:
        row: Pandas DataFrame row from gdeltdoc library
        processed_urls: Set of already processed URLs to skip duplicates
        
    Returns:
        Dict: Article in pipeline format, or None if invalid
    """
    parse_start_time = datetime.now()
    try:
                                                
        url = row.get('url', '')
        title = row.get('title', '')
        seendate = row.get('seendate', '')
        
                                                
        if not all([url, title, seendate]):
            return None
        
                                                                                               
        if processed_urls and url in processed_urls:
            logger.debug(f"⏭️  Skipping duplicate URL (already processed): {url}")
            return None
        
                                                                      
        logger.debug(f"Processing article with seendate: {seendate}")
        
                                                      
        domain = row.get('domain', '')
        language = row.get('language', 'en')
        sourcecountry = row.get('sourcecountry', '')
        
                                                                     
        logger.debug(f"Article language: '{language}' from domain '{domain}'")
        
                                                                                                     
        if '.dk' in domain.lower():
            logger.debug(f"Accepting article from Danish domain '{domain}' regardless of language '{language}'")
        elif language not in ['en', 'da', 'danish', 'eng', 'dan', 'English', 'Danish']:
            logger.info(f"❌ Language filter: Skipping article with language '{language}' - only English and Danish supported")
            return None
        
                                      
        parsed_url = urlparse(url)
        url_domain = parsed_url.netloc.lower()
        
                            
        if url_domain.startswith("www."):
            url_domain = url_domain[4:]
        
                                                                                      
        text = ''
        try:
            
            
                                                  
            reliable_domains = RELIABLE_NEWS_DOMAINS
            skip_domains = PROBLEMATIC_DOMAINS
            
                                                                                                           
            is_reliable = any(url_domain.endswith(reliable_domain) for reliable_domain in reliable_domains)
            is_problematic = any(skip_domain in url_domain for skip_domain in skip_domains)
            
            logger.debug(f"Domain check: {url_domain} - reliable: {is_reliable}, problematic: {is_problematic}")
            
                                                                                 
            japanese_domains = ['jp.reuters.com', 'jp.bloomberg.com', 'asahi.com', 'mainichi.jp', 'yomiuri.co.jp']
            is_japanese = any(jp_domain in url_domain for jp_domain in japanese_domains)
            
                                                                        
            tracker = get_domain_failure_tracker()
            if tracker.should_skip_domain(url_domain):
                logger.debug(f"Skipping domain {url_domain} due to previous failures ({tracker.get_domain_failure_count(url_domain)} failures)")
                                                                        
                return None
            elif is_problematic:
                logger.debug(f"Skipping problematic domain: {url_domain}")
                return None
            elif is_japanese:
                logger.debug(f"Skipping Japanese domain: {url_domain}")
                return None
            elif is_reliable:
                logger.info(f"Extracting full text from reliable domain {url_domain}: {url}")
                
                                                                 
                extraction_start_time = datetime.now()
                text = _extract_text_advanced(url, url_domain)
                extraction_duration = (datetime.now() - extraction_start_time).total_seconds()
                
                if text:
                                                                                                           
                    if len(text) < 700:
                        logger.warning(f"Text too short before processing for {url_domain}: {len(text)} chars (minimum 700 required)")
                        tracker.mark_domain_failed(url_domain, "text_too_short_before_processing")
                        return None
                    
                    logger.info(f"✓ Successfully extracted {len(text)} characters from {url_domain} in {extraction_duration:.2f}s")
                else:
                    logger.warning(f"Failed to extract text from {url_domain} after {extraction_duration:.2f}s")
                                                          
                    tracker.mark_domain_failed(url_domain, "text_extraction_failed")
                                                                            
                    return None
            else:
                logger.info(f"❌ Domain filter: Skipping non-reliable domain: {url_domain}")
                return None
                    
        except Exception as e:
            logger.debug(f"✗ Failed to extract text from {url}: {e}")
                                                  
            tracker = get_domain_failure_tracker()
            tracker.mark_domain_failed(url_domain, f"extraction_exception: {str(e)}")
                                                                    
            return None
        
                                             
        if text:
            import re
            
                                    
            text = re.sub(r'<[^>]+>', ' ', text)
            
                                      
            text = re.sub(r"\s+", " ", text)                        
            text = text.strip()
            
            logger.info(f"Basic text processing: {len(text)} chars for {url_domain}")
        
                                                    
        extraction_method = "basic_text_extraction"        
                                         
        total_parse_duration = (datetime.now() - parse_start_time).total_seconds()
        logger.info(f"✅ Article parsing completed in {total_parse_duration:.2f}s")
        
                             
        article_domain = domain or urlparse(url).netloc
        domain_category = get_domain_category(article_domain)
        logger.debug(f"Domain category for {article_domain}: {domain_category}")
        
        if article_domain == 'deadline.com' and (not title or title.strip().lower() == 'deadline'):
            extracted_title = _extract_deadline_title(url)
            if extracted_title:
                title = extracted_title
                logger.info(f"✓ Extracted actual title from deadline.com: {title[:80]}...")
        
        return {
            'url': url,
            'title': title,
            'text': text,
            'domain': article_domain,
            'domain_category': domain_category,
            'language': language,
            'date_publish': seendate,
            'date_download': datetime.now(timezone.utc).isoformat(),
            'authors': [],                                         
            'description': '',                                            
            'image': '',                                                      
            'source': domain,
            'sourcecountry': sourcecountry,
            'gdelt_id': url,
            'extraction_method': extraction_method
        }
        
    except Exception as e:
        logger.debug(f"Error parsing gdeltdoc DataFrame row: {e}")
        return None


                                                                                            


def fetch_gdelt_news_articles() -> List[Dict[str, Any]]:
    """
    Fetch all available news articles from GDELT within the past 2 hours.
    
    This function always operates in unlimited mode:
    - Fetches all available articles within 2-hour time windows
    - No language balancing or quotas applied
    - Uses GDELT only for maximum coverage
    
    Failed domains are tracked persistently across batches.
        
    Returns:
        List[Dict]: List of extracted articles
        
    Raises:
        FetcherError: If any step in the process fails
    """
    logger.info("🚀 Starting unlimited news fetch (past 2 hours only)")
    
                                                
    reset_domain_failure_tracker()
    tracker = get_domain_failure_tracker()
    
    config = load_config()
    
                                                         
    try:
        db = get_database()
        processed_urls = db.get_processed_urls()
        logger.info(f"Loaded {len(processed_urls)} processed URLs for duplicate checking")
    except Exception as e:
        logger.warning(f"Failed to load processed URLs, continuing without duplicate checking: {e}")
        processed_urls = set()
    
    try:
                                                                                    
        logger.info("🔄 Using unlimited fetch mode - fetching ALL available articles from past 2 hours")
        return fetch_gdelt_news_articles_unlimited()
    
    except Exception as e:
        logger.error(f"Error in unlimited fetch: {e}")
        return []


def fetch_by_domains_unlimited(processed_urls: Set[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch all available articles from major domains using GDELT only.
    Always operates in unlimited mode for the past 2 hours.
    """
    logger.info("🚀 Starting unlimited fetch from major domains (past 2 hours)")
    return fetch_by_domains(processed_urls=processed_urls)


def fetch_danish_news_unlimited(processed_urls: Set[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch all available Danish articles using GDELT only.
    Always operates in unlimited mode for the past 2 hours.
    """
    logger.info("🚀 Starting unlimited Danish news fetch (past 2 hours)")
    return fetch_danish_news(processed_urls=processed_urls)


def fetch_gdelt_news_articles_unlimited(processed_urls: Set[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch all available news articles from both Danish and English domains.
    Always operates in unlimited mode for the past 2 hours.
    """
    logger.info("🚀 Starting unlimited fetch from all domains (past 2 hours)")
    
    all_articles = []
    
                           
    danish_articles = fetch_danish_news_unlimited(processed_urls=processed_urls)
    all_articles.extend(danish_articles)
    logger.info(f"📊 Danish articles fetched: {len(danish_articles)}")
    
                              
    english_articles = fetch_by_domains_unlimited(processed_urls=processed_urls)
    all_articles.extend(english_articles)
    logger.info(f"📊 English articles fetched: {len(english_articles)}")
    
                       
    logger.info(f"🔄 Removing duplicates from {len(all_articles)} total articles...")
    unique_articles = _remove_duplicate_articles(all_articles)
    
    logger.info(f"✅ Unlimited fetch completed: {len(unique_articles)} unique articles")
    logger.info(f"📊 GDELT articles: {len([a for a in unique_articles if a.get('fetch_source') == 'gdelt'])}")
                                      
    
    return unique_articles






def _filter_failed_domains(articles: List[Dict[str, Any]], tracker: DomainFailureTracker) -> List[Dict[str, Any]]:
    """
    Filter out articles from domains that have failed text extraction.
    
    Args:
        articles: List of article dictionaries
        tracker: Domain failure tracker instance
        
    Returns:
        List[Dict]: List of articles with failed domains filtered out
    """
    filtered_articles = []
    
    for article in articles:
        url = article.get('url', '')
        if not url:
            continue
            
                                 
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
        except Exception:
                                                       
            filtered_articles.append(article)
            continue
        
                                             
        if tracker.is_domain_failed(domain):
            logger.debug(f"Filtering out article from failed domain: {domain}")
            continue
        
        filtered_articles.append(article)
    
    return filtered_articles


def _remove_duplicate_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate articles based on URL and normalized domain+title.
    
    Handles subdomain variations (e.g., cnn.com vs edition.cnn.com) by normalizing
    domains and checking for same title from same base domain.
    
    NOTE: Database deduplication is now handled AFTER processing in pipeline.py
    to ensure we don't lose articles before they're fully processed.
    
    Args:
        articles: List of article dictionaries
        
    Returns:
        List[Dict]: Deduplicated list of articles (in-memory only)
    """
    seen_urls: Set[str] = set()
    seen_domain_title: Set[tuple] = set()
    unique_articles = []
    
    for article in articles:
        url = article.get('url', '')
        title = article.get('title', '').strip().lower()
        domain = article.get('domain', '')
        
        is_duplicate = False
        
        if url and url in seen_urls:
            is_duplicate = True
        elif domain and title:
            normalized_domain = normalize_domain_for_dedup(domain)
            domain_title_key = (normalized_domain, title)
            if domain_title_key in seen_domain_title:
                is_duplicate = True
                logger.debug(f"Duplicate detected: {normalized_domain} - '{title[:50]}...'")
            else:
                seen_domain_title.add(domain_title_key)
        
        if not is_duplicate:
            if url:
                seen_urls.add(url)
            unique_articles.append(article)
            
    logger.info(f"Removed {len(articles) - len(unique_articles)} in-memory duplicate articles")
    return unique_articles





                       
__all__ = [
    'fetch_gdelt_news_articles',
    'get_domain_failure_tracker',
    'get_domain_failure_report',
    'DomainFailureTracker'
]


