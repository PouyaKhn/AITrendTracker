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

2. **Virtual Environment Setup** (Recommended):
   
   Create a fresh virtual environment:
   ```bash
   python3 -m venv venv
   ```
   
   **Activate the virtual environment:**
   
   **Linux/macOS (bash/zsh):**
   ```bash
   source venv/bin/activate
   ```
   
   **Windows (Command Prompt):**
   ```cmd
   venv\Scripts\activate.bat
   ```
   
   **Windows (PowerShell):**
   ```powershell
   venv\Scripts\Activate.ps1
   ```
   
   **Fish Shell:**
   ```fish
   source venv/bin/activate.fish
   ```
   
   **C Shell (csh/tcsh):**
   ```csh
   source venv/bin/activate.csh
   ```
   
   **Note:** You can verify the virtual environment is active by checking that `(venv)` appears at the beginning of your command prompt, or by running:
   ```bash
   echo $VIRTUAL_ENV  # Linux/macOS
   echo %VIRTUAL_ENV%  # Windows Command Prompt
   echo $env:VIRTUAL_ENV  # Windows PowerShell
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
   **Verified Dependencies:** All packages install successfully without import errors on Python 3.13+

4. **Quick Setup Script**: For automated setup, you can use the provided script:
   ```bash
   ./dev_setup.sh
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

The news scraping pipeline supports two modes of operation:

### Continuous Mode (Default)

Run the continuous pipeline with 30-minute intervals:

```bash
python main.py
```

This mode will:
1. Start the scheduler with automatic 30-minute intervals
2. Run an initial pipeline batch immediately
3. Continue running batches every 30 minutes
4. Log all activities to both console and rotating log files
5. Handle graceful shutdown on SIGINT/SIGTERM

### Single Batch Verification Mode

Run a single batch for testing and verification:

```bash
python main.py --once
```

This mode will:
1. Execute `verification.test_single_batch()` once
2. Verify that articles are properly fetched, processed, and stored
3. Display comprehensive verification results
4. Exit after completion

### CLI Options

```bash
python main.py [options]

Options:
  --once        Run single batch verification test instead of continuous mode
  --version     Show version information
  --help        Show help message and usage examples
```

### Environment Variables

Customize the pipeline behavior using environment variables:

```bash
# Set fetch interval (default: 30 minutes)
export FETCH_INTERVAL=30

# Set storage directory (default: ./data)
export STORAGE_DIR=/path/to/storage

# Set log file path (default: ./logs/news_scraper.log)
export LOG_PATH=/path/to/logfile.log

# Set logging level (default: INFO)
export LOG_LEVEL=DEBUG

# Set maximum articles to process (default: 100)
export MAX_ARTICLES=50

# Run the pipeline
python main.py
```

### Examples

```bash
# Run continuous pipeline with default settings
python main.py

# Run single verification test
python main.py --once

# Run with custom fetch interval (60 minutes)
FETCH_INTERVAL=60 python main.py

# Run with debug logging
LOG_LEVEL=DEBUG python main.py --once
```

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
