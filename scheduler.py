"""
Task scheduling functionality for automated news scraping.
"""

import schedule
import time
import threading
import signal
from datetime import datetime
from typing import Optional, Callable

from config import load_config
from logger import get_logger

                   
logger = get_logger(__name__)

                                                  
FETCH_INTERVAL = load_config().fetch_interval_minutes

                                   
_shutdown_requested = False


def run_batch():
    """Default batch job function that can be overridden."""
    logger.info("Running default batch job")
                                                                                       


def _signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown")
    _shutdown_requested = True


def start_scheduler(job_fn: Callable = None):
    """
    Start the scheduler that blocks and repeatedly calls job_fn.
    
    Args:
        job_fn: Function to be called on each scheduled interval.
                If None, uses the default run_batch function.
    
    Features:
    - Uses schedule.every(FETCH_INTERVAL).minutes.do(job_fn)
    - Blocks and repeatedly calls job_fn
    - Provides graceful shutdown on KeyboardInterrupt
    - Re-registers jobs on failure
    """
    global _shutdown_requested
    
                                           
    config = load_config()
    fetch_interval = config.fetch_interval_minutes
    
                                          
    if job_fn is None:
        job_fn = run_batch
    
                                                                              
    def unlimited_job_wrapper():
        """Wrapper that ensures MAX_ARTICLES=0 for each job execution."""
        import os
        os.environ['MAX_ARTICLES'] = '0'                         
        logger.info("🔄 Ensuring unlimited mode for scheduled job execution")
        return job_fn()
    
                                                  
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    
                                                      
    logger.info(f"FETCH_INTERVAL environment variable: {fetch_interval} minutes")
    if fetch_interval >= 60:
        hours = fetch_interval / 60
        logger.info(f"Starting scheduler with {hours:.1f} hour intervals")
    else:
        logger.info(f"Starting scheduler with {fetch_interval} minute intervals")
    
    def register_job():
        """Register the job with the scheduler."""
        schedule.clear()                           
        schedule.every(fetch_interval).minutes.do(unlimited_job_wrapper)
        logger.info(f"Job registered to run every {fetch_interval} minutes")
    
                              
    register_job()
    
                                  
    try:
        logger.info("Running initial job execution")
        unlimited_job_wrapper()
    except Exception as e:
        logger.error(f"Error in initial job execution: {e}")
    
                         
    while not _shutdown_requested:
        try:
                                        
            schedule.run_pending()
            time.sleep(1)                      
            
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received, initiating graceful shutdown")
            _shutdown_requested = True
            break
            
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
            logger.info("Re-registering job after failure")
            
            try:
                                                
                register_job()
                logger.info("Job re-registered successfully")
            except Exception as reg_error:
                logger.error(f"Failed to re-register job: {reg_error}")
            
                                  
            time.sleep(60)
    
             
    logger.info("Scheduler shutting down gracefully")
    schedule.clear()
    logger.info("All scheduled jobs cleared")

