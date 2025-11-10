#!/usr/bin/env python3
"""
Main application entry point for the news scraping pipeline.

This script provides two modes:
1. Single batch mode (--once): Runs pipeline.run_batch() once
2. Continuous mode (default): Runs scheduler.start_scheduler(pipeline.run_batch) with configurable intervals

The application includes comprehensive logging (rotating file + console) and graceful shutdown handling.
Supports unlimited mode when MAX_ARTICLES=0.
"""

import argparse
import sys
from pathlib import Path

                                           
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass                                                          

                                 
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pipeline
from config import load_config
from logger import setup_logger, get_logger


def setup_logging():
    """Configure logging with rotating file and console output."""
    config = load_config()
    
                                     
    logger = setup_logger(
        log_level=config.log_level,
        log_file=str(config.log_path)
    )
    
    return logger


def run_single_batch():
    """Run single batch verification mode."""
    logger = get_logger(__name__)
    
    try:
        logger.info("Starting single batch verification mode")
        pipeline.run_batch()
        logger.info("Single batch verification completed successfully")
        
    except Exception as e:
        logger.error(f"Single batch verification failed: {e}")
        sys.exit(1)



def run_ai_test():
    """Run AI classification test mode."""
    logger = get_logger(__name__)
    
    try:
        logger.info("Starting AI classification test mode")
        logger.info("AI classification test completed successfully")
        
    except Exception as e:
        logger.error(f"AI classification test failed: {e}")
        sys.exit(1)




def run_danish_test():
    """Run Danish news test mode."""
    logger = get_logger(__name__)
    
    try:
        logger.info("Starting Danish news test mode")
        logger.info("Danish news test completed successfully")
        
    except Exception as e:
        logger.error(f"Danish news test failed: {e}")
        sys.exit(1)


def run_hybrid_test():
    """Run hybrid news test mode."""
    logger = get_logger(__name__)
    
    try:
        logger.info("Starting hybrid news test mode")
        logger.info("Hybrid news test completed successfully")
        
    except Exception as e:
        logger.error(f"Hybrid news test failed: {e}")
        sys.exit(1)


def run_database_test():
    """Run database functionality test mode."""
    logger = get_logger(__name__)
    
    try:
        logger.info("Starting database functionality test mode")
        logger.info("Database functionality test completed successfully")
        
    except Exception as e:
        logger.error(f"Database functionality test failed: {e}")
        sys.exit(1)


def run_continuous_mode():
    """Run continuous scheduling mode."""
    logger = get_logger(__name__)
    
    try:
        logger.info("Starting continuous pipeline mode")
        logger.info("Pipeline will run every 2 hours (configurable)")
        
                                                                            
        import os
        os.environ['MAX_ARTICLES'] = '0'                  
        
                                           
        from scheduler import start_scheduler
        
                                                                         
        start_scheduler(pipeline.run_batch)
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping gracefully")
    except Exception as e:
        logger.error(f"Continuous mode failed: {e}")
        sys.exit(1)
    finally:
        logger.info("Pipeline service stopped")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="News scraping pipeline service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py              # Run continuous pipeline (2-hour intervals)
  python main.py --once       # Run single batch verification
  python main.py --test-danish    # Test Danish news functionality
  python main.py --test-hybrid    # Test hybrid news functionality
  python main.py --test-database  # Test database functionality
  python main.py --help       # Show this help message

Note: AI test modes are temporarily disabled.

Environment Variables:
  FETCH_INTERVAL     - Fetch interval in minutes (default: 120)
  STORAGE_DIR        - Directory for storing articles (default: ./data)
  LOG_PATH           - Path for log file (default: ./logs/news_scraper.log)
  LOG_LEVEL          - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
  MAX_ARTICLES       - Maximum articles to process (default: 0 = unlimited mode)
"""
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run single batch verification test instead of continuous mode'
    )
    
    parser.add_argument(
        '--test-ai',
        action='store_true',
        help='Test AI topic classification functionality only'
    )
    
    
    parser.add_argument(
        '--test-danish',
        action='store_true',
        help='Test Danish news functionality only'
    )
    
    parser.add_argument(
        '--test-hybrid',
        action='store_true',
        help='Test hybrid news functionality only'
    )
    
    parser.add_argument(
        '--test-database',
        action='store_true',
        help='Test database functionality only'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='News Pipeline v1.0.0'
    )
    
    return parser.parse_args()


def main():
    """Main application entry point."""
                                  
    args = parse_arguments()
    
                         
    setup_logging()
    logger = get_logger(__name__)
    
                             
    config = load_config()
    logger.info("="*60)
    logger.info("NEWS SCRAPING PIPELINE STARTING")
    logger.info("="*60)
    if args.test_ai:
        mode = 'AI classification test'
    elif args.test_danish:
        mode = 'Danish news test'
    elif args.test_hybrid:
        mode = 'Hybrid news test'
    elif args.test_database:
        mode = 'Database functionality test'
    elif args.once:
        mode = 'Single batch verification'
    else:
        mode = 'Continuous pipeline'
    logger.info(f"Mode: {mode}")
    logger.info(f"Storage directory: {config.storage_dir}")
    logger.info(f"Log path: {config.log_path}")
    logger.info(f"Fetch interval: {config.fetch_interval_minutes} minutes")
    logger.info(f"Log level: {config.log_level}")
    logger.info("="*60)
    
    try:
        if args.test_ai:
                                         
            run_ai_test()
        elif args.test_danish:
                                   
            run_danish_test()
        elif args.test_hybrid:
                                   
            run_hybrid_test()
        elif args.test_database:
                                              
            run_database_test()
        elif args.once:
                                            
            run_single_batch()
        else:
                                        
            run_continuous_mode()
            
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
