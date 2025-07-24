"""
Task scheduling functionality for automated news scraping.
"""

import schedule
import time
import threading
from datetime import datetime
from typing import Optional

from config import Config
from logger import get_logger


class NewsScheduler:
    """Scheduler for automated news scraping tasks."""
    
    def __init__(self, scraper, config: Config):
        """
        Initialize the scheduler.
        
        Args:
            scraper: NewsScraper instance
            config: Configuration object
        """
        self.scraper = scraper
        self.config = config
        self.logger = get_logger(__name__)
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        
    def scheduled_scrape_job(self):
        """Job function that runs the scraping process."""
        try:
            self.logger.info("Starting scheduled scraping job")
            start_time = datetime.now()
            
            # Run the scraping
            results = self.scraper.scrape_all_sources()
            
            # Count total articles
            total_articles = sum(len(articles) for articles in results.values())
            
            # Clean up old data
            self.scraper.cleanup_old_data()
            
            duration = datetime.now() - start_time
            self.logger.info(f"Scheduled scraping job completed. "
                           f"Articles scraped: {total_articles}, Duration: {duration}")
            
        except Exception as e:
            self.logger.error(f"Error in scheduled scraping job: {e}")
    
    def setup_schedule(self):
        """Set up the scraping schedule."""
        # Schedule scraping job
        schedule.every(self.config.scrape_interval_minutes).minutes.do(self.scheduled_scrape_job)
        
        # Schedule daily cleanup job at 2 AM
        schedule.every().day.at("02:00").do(self.scraper.cleanup_old_data)
        
        self.logger.info(f"Scheduled scraping every {self.config.scrape_interval_minutes} minutes")
        self.logger.info("Scheduled daily cleanup at 02:00")
    
    def run_scheduler(self):
        """Run the scheduler in a loop."""
        self.logger.info("Starting scheduler thread")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def start(self):
        """Start the scheduler."""
        if self.running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.logger.info("Starting news scraping scheduler")
        
        # Set up the schedule
        self.setup_schedule()
        
        # Run initial scraping job
        self.logger.info("Running initial scraping job")
        self.scheduled_scrape_job()
        
        # Start the scheduler thread
        self.running = True
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("News scraping scheduler started successfully")
    
    def stop(self):
        """Stop the scheduler."""
        if not self.running:
            self.logger.warning("Scheduler is not running")
            return
        
        self.logger.info("Stopping news scraping scheduler")
        self.running = False
        
        # Clear all scheduled jobs
        schedule.clear()
        
        # Wait for scheduler thread to finish
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("News scraping scheduler stopped")
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time."""
        try:
            next_run = schedule.next_run()
            return next_run
        except Exception:
            return None
    
    def get_status(self) -> dict:
        """Get scheduler status information."""
        return {
            'running': self.running,
            'next_run': self.get_next_run_time(),
            'jobs_count': len(schedule.jobs),
            'scrape_interval_minutes': self.config.scrape_interval_minutes,
        }
    
    def run_job_now(self):
        """Manually trigger a scraping job."""
        self.logger.info("Manually triggering scraping job")
        
        # Run in a separate thread to avoid blocking
        job_thread = threading.Thread(target=self.scheduled_scrape_job, daemon=True)
        job_thread.start()
        
        return "Scraping job started manually"
