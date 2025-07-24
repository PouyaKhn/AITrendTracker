"""
Logging configuration for the news scraping service.
"""

import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional

try:
    from loguru import logger as loguru_logger
    LOGURU_AVAILABLE = True
except ImportError:
    LOGURU_AVAILABLE = False


def setup_logger(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    if LOGURU_AVAILABLE:
        return setup_loguru_logger(log_level, log_file)
    else:
        return setup_standard_logger(log_level, log_file)


def setup_loguru_logger(log_level: str = "INFO", log_file: Optional[str] = None):
    """Set up loguru logger."""
    # Remove default handler
    loguru_logger.remove()
    
    # Console handler
    loguru_logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        colorize=True
    )
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(exist_ok=True)
        
        loguru_logger.add(
            log_file,
            level=log_level,
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
        )
    
    return loguru_logger


def setup_standard_logger(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Set up standard Python logger."""
    # Create logger
    logger = logging.getLogger("news_scraper")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = None):
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    if LOGURU_AVAILABLE:
        if name:
            return loguru_logger.bind(name=name)
        return loguru_logger
    else:
        return logging.getLogger(name or "news_scraper")


# Configure root logger
root_logger = setup_logger()
