# News Scraping Service

An automated news scraping service that uses the `news-please` library to collect articles from various news sources on a scheduled basis.

## Project Structure

- `main.py` - Main application entry point
- `config.py` - Configuration settings and environment variables
- `scraper.py` - News scraping functionality using news-please
- `scheduler.py` - Task scheduling for automated scraping
- `data_handler.py` - Data storage and management
- `utils.py` - Utility functions for the application
- `logger.py` - Logging configuration (supports both loguru and standard logging)
- `requirements.txt` - Project dependencies

## Dependencies

### Core Dependencies
- `news-please` - News article extraction library
- `schedule` - Task scheduling library
- `tqdm` - Progress bars for scraping operations
- `requests` - HTTP library (news-please dependency)
- `boto3` - AWS SDK for cloud storage
- `python-dateutil` - Date/time utilities

### Optional Dependencies
- `loguru` - Enhanced logging (falls back to standard logging if not available)
- `pytest` - Testing framework
- `python-dotenv` - Environment variable management

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Secondment
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The application can be configured through environment variables:

- `SCRAPE_INTERVAL` - Scraping interval in minutes (default: 60)
- `MAX_ARTICLES` - Maximum articles per source (default: 50)
- `REQUEST_TIMEOUT` - HTTP request timeout in seconds (default: 30)
- `OUTPUT_FORMAT` - Data output format: json, csv, parquet (default: json)
- `DATA_RETENTION_DAYS` - Data retention period in days (default: 30)
- `LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `AWS_REGION` - AWS region for S3 storage (default: us-east-1)
- `S3_BUCKET` - S3 bucket name for data storage
- `S3_PREFIX` - S3 key prefix (default: news-data/)

## Usage

Run the news scraping service:

```bash
python main.py
```

The service will:
1. Start the scheduler
2. Run an initial scraping job
3. Continue scraping at the configured interval
4. Clean up old data files based on retention policy
5. Log all activities to console and optionally to file

## Data Storage

Scraped articles are stored in the `data/` directory in the configured format (JSON by default). Each article includes:

- URL and title
- Full text content
- Publication and download dates
- Authors and language
- Source domain
- Description and image URL
- Metadata timestamps

## Logging

The application supports both enhanced logging with `loguru` and standard Python logging. Logs include:

- Scraping progress and statistics
- Error handling and debugging information
- File rotation and compression (with loguru)
- Console and file output

## Git Repository

The project is initialized as a Git repository with:
- Proper `.gitignore` for Python projects
- Initial commit with all core files
- Exclusion of data/, logs/, and temporary files

## Development

To contribute to this project:

1. Create a feature branch
2. Make your changes
3. Add tests for new functionality
4. Run the test suite: `pytest`
5. Submit a pull request

## License

[Add license information here]
