"""
Database module for tracking processed articles and pipeline state.

Provides SQLite-based storage for:
- Processed article URLs and metadata
- Pipeline execution history
- Statistics and metrics for future dashboard
"""

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict

from logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessedArticle:
    """Data class for processed article records."""
    url: str
    title: str
    domain: str
    domain_category: str
    language: str
    source_country: str
    processed_at: str
    gdelt_id: str
    extraction_method: str
    ai_topic_detected: bool
    file_stored_in: str


class ArticleDatabase:
    """SQLite database manager for tracking processed articles."""
    
    def __init__(self, db_path: str = "data/processed_articles.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                                                   
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS processed_articles (
                        url TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        domain TEXT,
                        domain_category TEXT,
                        language TEXT,
                        source_country TEXT,
                        processed_at TIMESTAMP NOT NULL,
                        gdelt_id TEXT,
                        extraction_method TEXT,
                        ai_topic_detected BOOLEAN,
                        file_stored_in TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                                                                 
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rejected_articles (
                        url TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        domain TEXT,
                        domain_category TEXT,
                        language TEXT,
                        source_country TEXT,
                        rejected_at TIMESTAMP NOT NULL,
                        gdelt_id TEXT,
                        extraction_method TEXT,
                        rejection_reason TEXT,
                        file_stored_in TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                                            
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS pipeline_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_started_at TIMESTAMP NOT NULL,
                        run_completed_at TIMESTAMP,
                        articles_fetched INTEGER DEFAULT 0,
                        articles_processed INTEGER DEFAULT 0,
                        articles_stored INTEGER DEFAULT 0,
                        ai_topic_count INTEGER DEFAULT 0,
                        processing_time_seconds REAL,
                        status TEXT DEFAULT 'running',
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                                                        
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS daily_statistics (
                        date TEXT PRIMARY KEY,
                        total_articles INTEGER DEFAULT 0,
                        unique_domains INTEGER DEFAULT 0,
                        languages_count INTEGER DEFAULT 0,
                        countries_count INTEGER DEFAULT 0,
                        ai_topic_percentage REAL DEFAULT 0.0,
                        processing_time_avg REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                                                       
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_processed_at ON processed_articles(processed_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_domain ON processed_articles(domain)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_language ON processed_articles(language)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rejected_at ON rejected_articles(rejected_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rejected_domain ON rejected_articles(domain)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rejected_language ON rejected_articles(language)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_run_started ON pipeline_runs(run_started_at)')
                
                                                                                   
                try:
                    cursor.execute("ALTER TABLE processed_articles ADD COLUMN domain_category TEXT DEFAULT 'unknown'")
                    logger.info("Added domain_category column to processed_articles table")
                except sqlite3.OperationalError:
                                                   
                    pass
                
                try:
                    cursor.execute("ALTER TABLE rejected_articles ADD COLUMN domain_category TEXT DEFAULT 'unknown'")
                    logger.info("Added domain_category column to rejected_articles table")
                except sqlite3.OperationalError:
                                                   
                    pass
                
                conn.commit()
                logger.info(f"Database initialized: {self.db_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def get_processed_urls(self) -> Set[str]:
        """Get set of all processed and rejected URLs for deduplication."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                                    
                cursor.execute('SELECT url FROM processed_articles')
                processed_urls = {row[0] for row in cursor.fetchall()}
                
                                   
                cursor.execute('SELECT url FROM rejected_articles')
                rejected_urls = {row[0] for row in cursor.fetchall()}
                
                                   
                all_urls = processed_urls | rejected_urls
                logger.debug(f"Loaded {len(processed_urls)} processed URLs and {len(rejected_urls)} rejected URLs from database")
                return all_urls
        except Exception as e:
            logger.error(f"Failed to get processed URLs: {e}")
            return set()
    
    def get_last_processed_time(self) -> Optional[str]:
        """Get timestamp of the most recently processed article."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT MAX(processed_at) FROM processed_articles 
                    WHERE processed_at IS NOT NULL
                ''')
                result = cursor.fetchone()
                if result and result[0]:
                    logger.debug(f"Last processed time: {result[0]}")
                    return result[0]
                return None
        except Exception as e:
            logger.error(f"Failed to get last processed time: {e}")
            return None
    
    def add_processed_articles(self, articles: List[Dict[str, Any]], file_stored_in: str):
        """Add processed articles to database."""
        if not articles:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for article in articles:
                                                    
                    ai_topic_detected = False
                    
                    if 'ai_topic_analysis' in article:
                        ai_topic_detected = article['ai_topic_analysis'].get('is_ai_topic', False)
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO processed_articles 
                        (url, title, domain, domain_category, language, source_country, processed_at, 
                         gdelt_id, extraction_method, ai_topic_detected, file_stored_in)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        article.get('url', ''),
                        article.get('title', ''),
                        article.get('domain', ''),
                        article.get('domain_category', 'unknown'),
                        article.get('language', ''),
                        article.get('sourcecountry', ''),
                        article.get('date_download', ''),
                        article.get('gdelt_id', ''),
                        article.get('extraction_method', ''),
                        ai_topic_detected,
                        file_stored_in
                    ))
                
                conn.commit()
                logger.info(f"Added {len(articles)} articles to database")
                
        except Exception as e:
            logger.error(f"Failed to add processed articles: {e}")
    
    def add_rejected_articles(self, articles: List[Dict[str, Any]], file_stored_in: str):
        """Add rejected articles to database for deduplication."""
        if not articles:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for article in articles:
                    cursor.execute('''
                        INSERT OR REPLACE INTO rejected_articles 
                        (url, title, domain, domain_category, language, source_country, rejected_at, 
                         gdelt_id, extraction_method, rejection_reason, file_stored_in)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        article.get('url', ''),
                        article.get('title', ''),
                        article.get('domain', ''),
                        article.get('domain_category', 'unknown'),
                        article.get('language', ''),
                        article.get('sourcecountry', ''),
                        article.get('date_download', ''),
                        article.get('gdelt_id', ''),
                        article.get('extraction_method', ''),
                        article.get('rejection_reason', 'unknown'),
                        file_stored_in
                    ))
                
                conn.commit()
                logger.info(f"Added {len(articles)} rejected articles to database")
                
        except Exception as e:
            logger.error(f"Failed to add rejected articles: {e}")
    
    def start_pipeline_run(self) -> int:
        """Start a new pipeline run and return run ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO pipeline_runs (run_started_at, status)
                    VALUES (?, ?)
                ''', (datetime.now(timezone.utc).isoformat(), 'running'))
                conn.commit()
                run_id = cursor.lastrowid
                logger.info(f"Started pipeline run ID: {run_id}")
                return run_id
        except Exception as e:
            logger.error(f"Failed to start pipeline run: {e}")
            return -1
    
    def complete_pipeline_run(self, run_id: int, stats: Dict[str, Any]):
        """Complete a pipeline run with statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE pipeline_runs 
                    SET run_completed_at = ?, articles_fetched = ?, articles_processed = ?, 
                        articles_stored = ?, ai_topic_count = ?, processing_time_seconds = ?, status = ?
                    WHERE id = ?
                ''', (
                    datetime.now(timezone.utc).isoformat(),
                    stats.get('fetched_articles', 0),
                    stats.get('processed_articles', 0),
                    stats.get('stored_articles', 0),
                    stats.get('ai_topic_count', 0),
                    stats.get('processing_time', 0),
                    'completed',
                    run_id
                ))
                conn.commit()
                logger.info(f"Completed pipeline run ID: {run_id}")
        except Exception as e:
            logger.error(f"Failed to complete pipeline run: {e}")
    
    def get_dashboard_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get statistics for dashboard visualization."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                                           
                cursor.execute('''
                    SELECT COUNT(*) FROM processed_articles 
                    WHERE processed_at >= datetime('now', '-{} days')
                '''.format(days))
                recent_articles = cursor.fetchone()[0]
                
                                    
                cursor.execute('''
                    SELECT COUNT(DISTINCT domain) FROM processed_articles 
                    WHERE processed_at >= datetime('now', '-{} days')
                '''.format(days))
                unique_domains = cursor.fetchone()[0]
                
                                         
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN ai_topic_detected THEN 1 ELSE 0 END) as ai_topics
                    FROM processed_articles 
                    WHERE processed_at >= datetime('now', '-{} days')
                '''.format(days))
                ai_stats = cursor.fetchone()
                ai_topic_percentage = (ai_stats[1] / ai_stats[0] * 100) if ai_stats[0] > 0 else 0
                
                
                return {
                    'recent_articles': recent_articles,
                    'unique_domains': unique_domains,
                    'ai_topic_percentage': round(ai_topic_percentage, 2),
                    'days_analyzed': days
                }
                
        except Exception as e:
            logger.error(f"Failed to get dashboard stats: {e}")
            return {}
    
    def cleanup_old_records(self, days_to_keep: int = 30):
        """Clean up old records to prevent database bloat."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                                               
                cursor.execute('''
                    DELETE FROM processed_articles 
                    WHERE processed_at < datetime('now', '-{} days')
                '''.format(days_to_keep))
                articles_deleted = cursor.rowcount
                
                                          
                cursor.execute('''
                    DELETE FROM pipeline_runs 
                    WHERE run_started_at < datetime('now', '-{} days')
                '''.format(days_to_keep))
                runs_deleted = cursor.rowcount
                
                conn.commit()
                logger.info(f"Cleaned up {articles_deleted} old articles and {runs_deleted} old runs")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")
    
    def get_total_article_count(self) -> int:
        """Get total number of processed articles."""
        try:
            db_path_str = str(self.db_path.resolve())
            with sqlite3.connect(db_path_str) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM processed_articles")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get total article count: {e}")
            return 0
    
    def get_articles_by_domain_category(self) -> Dict[str, int]:
        """Get count of articles by domain category."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT domain_category, COUNT(*) 
                    FROM processed_articles 
                    GROUP BY domain_category 
                    ORDER BY COUNT(*) DESC
                """)
                return dict(cursor.fetchall())
        except Exception as e:
            logger.error(f"Failed to get articles by domain category: {e}")
            return {}
    
    def get_recent_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent articles."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT url, title, domain, domain_category, language, processed_at
                    FROM processed_articles 
                    ORDER BY processed_at DESC 
                    LIMIT ?
                """, (limit,))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get recent articles: {e}")
            return []
    
    def get_recent_pipeline_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent pipeline runs."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, run_started_at, run_completed_at, articles_stored, 
                           processing_time_seconds, status
                    FROM pipeline_runs 
                    ORDER BY run_started_at DESC 
                    LIMIT ?
                """, (limit,))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get recent pipeline runs: {e}")
            return []


    def get_ai_article_count(self) -> int:
        """Get total number of AI-related articles."""
        try:
            db_path_str = str(self.db_path.resolve())
            with sqlite3.connect(db_path_str) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM processed_articles WHERE ai_topic_detected = 1")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get AI article count: {e}")
            return 0
    
    def get_ai_articles_by_domain_category(self) -> Dict[str, int]:
        """Get count of AI-related articles by domain category."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT domain_category, COUNT(*) 
                    FROM processed_articles 
                    WHERE ai_topic_detected = 1
                    GROUP BY domain_category
                """)
                return dict(cursor.fetchall())
        except Exception as e:
            logger.error(f"Failed to get AI articles by domain category: {e}")
            return {}
    
    def get_recent_ai_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent AI-related articles."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT url, title, domain, domain_category, language, 
                           source_country, processed_at, ai_topic_detected
                    FROM processed_articles 
                    WHERE ai_topic_detected = 1
                    ORDER BY processed_at DESC 
                    LIMIT ?
                """, (limit,))
                
                columns = ['url', 'title', 'domain', 'domain_category', 'language', 
                          'source_country', 'processed_at', 'ai_topic_detected']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get recent AI articles: {e}")
            return []
    
    def get_ai_articles_by_language(self) -> Dict[str, int]:
        """Get count of AI-related articles by language."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT language, COUNT(*) 
                    FROM processed_articles 
                    WHERE ai_topic_detected = 1
                    GROUP BY language
                """)
                return dict(cursor.fetchall())
        except Exception as e:
            logger.error(f"Failed to get AI articles by language: {e}")
            return {}
    
    def get_ai_articles_by_domain(self) -> Dict[str, int]:
        """Get count of AI-related articles by domain."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT domain, COUNT(*) 
                    FROM processed_articles 
                    WHERE ai_topic_detected = 1
                    GROUP BY domain
                    ORDER BY COUNT(*) DESC
                """)
                return dict(cursor.fetchall())
        except Exception as e:
            logger.error(f"Failed to get AI articles by domain: {e}")
            return {}
    
    def clear_all_data(self):
        """Clear all data from the database - DANGEROUS OPERATION."""
        try:
            # Use absolute path to ensure we're working with the correct database
            db_path_str = str(self.db_path.resolve())
            
            with sqlite3.connect(db_path_str) as conn:
                cursor = conn.cursor()
                
                # Get counts before deletion for verification
                cursor.execute("SELECT COUNT(*) FROM processed_articles")
                processed_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM rejected_articles")
                rejected_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM pipeline_runs")
                runs_count = cursor.fetchone()[0]
                
                # Delete all data
                cursor.execute("DELETE FROM processed_articles")
                cursor.execute("DELETE FROM rejected_articles")
                cursor.execute("DELETE FROM pipeline_runs")
                cursor.execute("DELETE FROM daily_statistics")
                
                # Reset auto-increment sequences
                cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('pipeline_runs', 'processed_articles', 'rejected_articles', 'daily_statistics')")
                
                # Verify deletion
                cursor.execute("SELECT COUNT(*) FROM processed_articles")
                remaining_processed = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM rejected_articles")
                remaining_rejected = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM pipeline_runs")
                remaining_runs = cursor.fetchone()[0]
                
                conn.commit()
                
                # VACUUM to reclaim space and optimize database
                conn.execute("VACUUM")
                
                logger.warning(f"All database data has been cleared. Deleted: {processed_count} processed, {rejected_count} rejected, {runs_count} runs")
                
                # Verify all data was deleted
                if remaining_processed > 0 or remaining_rejected > 0 or remaining_runs > 0:
                    raise Exception(f"Failed to clear all data. Remaining: {remaining_processed} processed, {remaining_rejected} rejected, {remaining_runs} runs")
                
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            raise


                          
_db_instance: Optional[ArticleDatabase] = None


def get_database() -> ArticleDatabase:
    """Get or create database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = ArticleDatabase()
    return _db_instance


def reset_database_instance():
    """Reset the database singleton instance (useful after clearing data)."""
    global _db_instance
    _db_instance = None


def init_database():
    """Initialize database (called at startup)."""
    db = get_database()
    db.cleanup_old_records()                                   
    return db 