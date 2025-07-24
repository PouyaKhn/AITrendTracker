"""
Data handling functionality for storing, retrieving, and cleaning up scraped data.
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from config import Config
from logger import get_logger


class DataHandler:
    """Data handler for storing and managing scraped data."""
    
    def __init__(self, config: Config):
        """Initialize data handler with configuration."""
        self.config = config
        self.logger = get_logger(__name__)
        
    def save_articles(self, articles: List[Dict[str, Any]], filename: str) -> None:
        """
        Save articles to a file in the configured data directory.
        
        Args:
            articles: List of article data
            filename: Filename to save data
        """
        try:
            file_path = self.config.data_dir / f"{filename}.{self.config.output_format}"
            
            if self.config.output_format == "json":
                with open(file_path, "w") as f:
                    json.dump(articles, f, indent=4)
            
            # Add other formats if needed, e.g., CSV, Parquet
            
            self.logger.info(f"Saved {len(articles)} articles to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving articles to {file_path}: {e}")
    
    def cleanup_old_files(self, cutoff_date: datetime) -> None:
        """
        Delete data files older than the specified cutoff date.
        
        Args:
            cutoff_date: Datetime to determine what files to delete
        """
        try:
            for file_path in self.config.data_dir.iterdir():
                file_mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mod_time <= cutoff_date and file_path.is_file():
                    file_path.unlink()
                    self.logger.info(f"Deleted old data file {file_path} (modified: {file_mod_time})")
        except Exception as e:
            self.logger.error(f"Error cleaning up old files: {e}")
    
    def list_article_files(self) -> List[str]:
        """List all article files in the data directory."""
        try:
            files = [str(file) for file in self.config.data_dir.iterdir() if file.is_file()]
            return files
        except Exception as e:
            self.logger.error(f"Error listing article files: {e}")
            return []
    
    def move_data(self, dest_dir: Path) -> None:
        """Move all data files to an archive directory."""
        try:
            dest_dir.mkdir(exist_ok=True)
            
            for file_path in self.config.data_dir.iterdir():
                if file_path.is_file():
                    shutil.move(str(file_path), dest_dir)
                    self.logger.info(f"Moved {file_path} to {dest_dir}")
                    
        except Exception as e:
            self.logger.error(f"Error moving data files to {dest_dir}: {e}")
