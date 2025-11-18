# AI Trend Tracker - Technical Documentation

## System Overview

The AI Trend Tracker is a comprehensive news scraping and analysis system designed to monitor AI-related content from global news sources. The system fetches articles from GDELT (Global Database of Events, Language, and Tone), processes them through advanced text extraction, classifies AI-related content using Large Language Models (LLMs), and provides real-time analytics through a multilingual Streamlit web dashboard.

## Architecture

### Core Components

1. **News Fetcher** (`fetcher.py`) - GDELT integration and content extraction
2. **Article Processor** (`processor.py`) - Validation and data normalization
3. **AI Classifier** (`ai_classifier.py`) - LLM-based topic classification
4. **Pipeline Orchestrator** (`pipeline.py`) - End-to-end workflow management
5. **Database Manager** (`database.py`) - SQLite storage and analytics
6. **Scheduler** (`scheduler.py`) - Automated execution management
7. **Web Dashboard** (`streamlit_app.py`) - User interface and monitoring
8. **Configuration** (`config.py`) - System settings and environment management
9. **Logging** (`logger.py`) - Comprehensive logging system
10. **Utilities** (`utils.py`) - Helper functions and data processing
11. **Language Support** (`config/languages.py`) - Multilingual translations (English/Danish)

### Data Flow

```
GDELT API → Fetcher → Processor → AI Classifier → Database → Dashboard
    ↓           ↓         ↓           ↓            ↓         ↓
  Articles → Validation → LLM API → SQLite → Streamlit UI
```

## Detailed Component Analysis

### 1. News Fetcher (`fetcher.py`)

**Purpose**: Fetches news articles from GDELT and extracts full text content.

**Key Features**:
- GDELT DOC 2.0 API integration for worldwide news access
- Multi-library text extraction (Trafilatura, Goose3, Newspaper3k, Readability-lxml, BeautifulSoup)
- Domain failure tracking and persistent blacklisting
- Language detection (English/Danish focus)
- Duplicate removal and URL deduplication
- Rate limiting and error handling
- Unlimited mode support (fetches all available articles from past 2 hours)

**Core Functions**:
- `fetch_gdelt_news_articles()`: Main entry point for unlimited article fetching
- `fetch_danish_news()`: Danish-specific news fetching (unlimited mode)
- `fetch_by_domains()`: Domain-based article collection (unlimited mode)
- `fetch_gdelt_news_articles_unlimited()`: Combined Danish and English article fetching
- `_extract_text_advanced()`: Multi-method text extraction with fallback chain
- `_parse_gdeltdoc_dataframe_row()`: GDELT DataFrame row parsing
- `_extract_journalisten_specific_article()`: Special handling for Journalisten.dk overview pages

**Text Extraction Strategy**:
1. **Trafilatura** (Primary) - Fast general extraction with encoding fixes
2. **Goose3** (Fallback) - News-specific extraction
3. **Newspaper3k** (Fallback) - Reliable news parsing
4. **Readability-lxml** (Fallback) - Content-focused extraction
5. **BeautifulSoup** (Last resort) - Basic HTML parsing with content area detection

**Domain Management**:
- `RELIABLE_NEWS_DOMAINS`: Curated list of domains with good GDELT coverage
- `PROBLEMATIC_DOMAINS`: Blacklisted domains (YouTube, social media, etc.)
- `DomainFailureTracker`: Tracks and blacklists domains after repeated failures
- Special handling for Danish news sites (Journalisten.dk overview pages)
- Domain category mapping for analytics

**Domain Failure Tracking**:
- Tracks failures per domain across batches
- Configurable failure threshold (default: 5 failures)
- Persistent blacklisting of problematic domains
- Failure reporting and statistics

### 2. Article Processor (`processor.py`)

**Purpose**: Validates, normalizes, and stores article data.

**Key Features**:
- Article validation (required fields, content length, format)
- UTF-8 encoding enforcement and Unicode normalization (NFKC)
- Content hash generation for deduplication
- JSON storage with metadata tracking
- Error handling and graceful degradation
- Custom JSON encoder for datetime objects

**Core Functions**:
- `process_article()`: Article data normalization and encoding
- `validate_article()`: Content validation and filtering
- `store_articles()`: JSON file storage with metadata files

**Validation Criteria**:
- Required fields: URL, title, text, date_publish
- Minimum text length: 700 characters (configurable via `MIN_ARTICLE_LENGTH`)
- URL format validation (must start with http:// or https://)
- Language acceptance (all languages accepted, English/Danish focus)
- Content quality checks

**Storage Format**:
- Articles stored as formatted JSON arrays
- Separate metadata files for tracking
- Timestamped filenames for batch identification
- Rejected articles stored separately with rejection reasons

### 3. AI Classifier (`ai_classifier.py`)

**Purpose**: Classifies articles for AI-related content using LLM APIs.

**Key Features**:
- OpenAI GPT-4o-mini integration (primary)
- Anthropic Claude 3.5 Haiku support (fallback)
- Fallback keyword-based classification
- Comprehensive AI topic categorization (14 categories)
- Confidence scoring and explanation generation
- Keyword extraction from articles

**AI Topic Categories**:
1. AI Research and Development
2. AI Ethics and Regulations
3. AI Safety and Governance
4. AI Business and Industry
5. AI Language Models and NLP
6. AI Robotics and Automation
7. AI Healthcare and Medical
8. AI Education and Training
9. AI Cybersecurity and Privacy
10. AI Computer Vision
11. AI Data Science and Analytics
12. AI Neural Networks and Deep Learning
13. AI Applications and Deployment
14. AI Technology and Infrastructure

**Classification Process**:
1. API-based LLM analysis (OpenAI/Anthropic)
2. JSON response parsing with regex fallback
3. Manual response parsing if JSON extraction fails
4. Fallback keyword matching if APIs unavailable
5. Confidence scoring (0.0-1.0)
6. Topic assignment and explanation generation
7. Keyword extraction from article text

**API Configuration**:
- OpenAI model: `gpt-4o-mini-2024-07-18`
- Anthropic model: `claude-3-5-haiku-20241022`
- Temperature: 0.1 (low for consistency)
- Max tokens: 300
- Rate limiting: 100ms delay between API calls

**Core Functions**:
- `classify_articles_ai_topics()`: Batch classification of articles
- `get_ai_topic_summary()`: Summary statistics for classified articles
- `APIBasedAITopicClassifier`: Main classifier class

### 4. Pipeline Orchestrator (`pipeline.py`)

**Purpose**: Coordinates the entire news processing workflow.

**Key Features**:
- End-to-end batch processing
- Database integration and tracking
- Statistics collection and reporting
- Error handling and recovery
- Unlimited mode support (MAX_ARTICLES=0)
- Language-aware duplicate removal

**Workflow Steps**:
1. Database initialization and run tracking
2. Article fetching from GDELT (unlimited mode)
3. Content processing and validation
4. Database duplicate removal
5. AI topic classification
6. Article storage (JSON files)
7. Database storage and tracking
8. Statistics compilation and reporting

**Statistics Tracked**:
- Articles fetched, validated, stored
- Processing failures and errors
- AI topic detection counts
- Domain failure tracking
- Processing time metrics
- Language distribution

**Core Functions**:
- `run_batch()`: Main batch processing function
- `_is_danish_article()`: Language detection helper

### 5. Database Manager (`database.py`)

**Purpose**: SQLite-based storage and analytics system.

**Database Schema**:

**processed_articles**:
- `url` (TEXT PRIMARY KEY)
- `title` (TEXT NOT NULL)
- `domain` (TEXT)
- `domain_category` (TEXT)
- `language` (TEXT)
- `source_country` (TEXT)
- `processed_at` (TIMESTAMP)
- `gdelt_id` (TEXT)
- `extraction_method` (TEXT)
- `ai_topic_detected` (BOOLEAN)
- `file_stored_in` (TEXT)
- `created_at` (TIMESTAMP)

**rejected_articles**:
- `url` (TEXT PRIMARY KEY)
- `title` (TEXT NOT NULL)
- `domain` (TEXT)
- `domain_category` (TEXT)
- `language` (TEXT)
- `source_country` (TEXT)
- `rejected_at` (TIMESTAMP)
- `gdelt_id` (TEXT)
- `extraction_method` (TEXT)
- `rejection_reason` (TEXT)
- `file_stored_in` (TEXT)
- `created_at` (TIMESTAMP)

**pipeline_runs**:
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `run_started_at` (TIMESTAMP)
- `run_completed_at` (TIMESTAMP)
- `articles_fetched` (INTEGER)
- `articles_processed` (INTEGER)
- `articles_stored` (INTEGER)
- `ai_topic_count` (INTEGER)
- `processing_time_seconds` (REAL)
- `status` (TEXT)
- `error_message` (TEXT)
- `created_at` (TIMESTAMP)

**daily_statistics**:
- `date` (TEXT PRIMARY KEY)
- `total_articles` (INTEGER)
- `unique_domains` (INTEGER)
- `languages_count` (INTEGER)
- `countries_count` (INTEGER)
- `ai_topic_percentage` (REAL)
- `processing_time_avg` (REAL)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Key Features**:
- URL deduplication across runs
- Pipeline execution tracking
- Statistics aggregation
- Data cleanup and maintenance (30-day retention)
- Dashboard data provision
- Indexed queries for performance

**Core Functions**:
- `get_processed_urls()`: Deduplication support
- `add_processed_articles()`: Article storage
- `add_rejected_articles()`: Rejected article tracking
- `start_pipeline_run()`: Execution tracking
- `complete_pipeline_run()`: Run completion with statistics
- `get_dashboard_stats()`: Analytics data
- `get_recent_ai_articles()`: Dashboard article retrieval
- `cleanup_old_records()`: Maintenance (30-day retention)

### 6. Scheduler (`scheduler.py`)

**Purpose**: Automated execution management for continuous operation.

**Key Features**:
- Configurable interval scheduling (default: 2 hours)
- Graceful shutdown handling (SIGINT, SIGTERM)
- Signal processing and cleanup
- Job re-registration on failure
- Unlimited mode enforcement (MAX_ARTICLES=0)
- Initial job execution on startup

**Scheduling Options**:
- Continuous mode: Automated recurring execution (`python main.py`)
- Single batch: One-time execution (`python main.py --once`)
- Manual execution: Dashboard-triggered runs

**Core Functions**:
- `start_scheduler()`: Main scheduler function
- `run_batch()`: Default batch job (placeholder)
- `_signal_handler()`: Graceful shutdown handler

### 7. Web Dashboard (`streamlit_app.py`)

**Purpose**: User interface for system monitoring and control.

**Key Features**:
- Pipeline start/stop control (subprocess management)
- Real-time statistics display with automatic refresh (every 30 seconds when pipeline is running, and when pipeline completes each batch run)
- Manual refresh button to refresh all data (stats, charts, articles)
- AI article browsing with pagination (10 per page)
- Interactive charts and analytics
- Process management (PID tracking)
- Multilingual support (English/Danish)
- Language selection in UI via flag icons
- Admin login system for protected operations
- Database clearing functionality
- Article summaries display

**Dashboard Components**:
- **Control Panel**: Start/stop pipeline, status indicators, language selection
- **Live Statistics**: Real-time metrics and counters with automatic refresh (every 30 seconds when running, and on batch completion) and manual refresh button
- **Article Browser**: Paginated AI article list with expandable details and summaries
- **Analytics Charts**: Topic distribution, category analysis, trend analysis
- **Status Monitoring**: Process health and error reporting
- **Admin Panel**: Pipeline controls, database management, system monitoring

**Refresh Mechanisms**:
- **Automatic Refresh**: Dashboard automatically refreshes every 30 seconds when pipeline is running, and immediately when pipeline completes each batch run (detected via database changes)
- **Manual Refresh**: "🔄 Refresh Stats" button clears all caches (`st.cache_data` and `st.cache_resource`) and refreshes all data (stats, charts, and articles)

**Chart Types**:
- AI Topics Distribution (Bar chart)
- Articles by Domain Category (Bar chart)
- Trend Analysis (Line chart):
  - Hourly: Today (00-23)
  - Daily: Current week (Mon-Sun)
  - Weekly: Weeks 1-4 of current month
  - Monthly: January-December of current year
  - Yearly: From 2025 onward

**Language Support**:
- English (en) - default
- Danish (da)
- All UI elements translated
- AI topics and domain categories translated
- Time labels (days, months, weeks) translated

### 8. Configuration System (`config.py`)

**Purpose**: Centralized configuration management with environment variable support.

**Key Configuration Areas**:
- **Storage**: Data directory, log paths, file retention
- **Fetching**: Intervals, timeouts, rate limiting
- **Processing**: Article limits, validation criteria
- **API Keys**: OpenAI, Anthropic
- **Database**: Connection settings, cleanup policies
- **Logging**: Levels, formats, rotation

**Environment Variables**:
- `FETCH_INTERVAL`: Minutes between runs (default: 120)
- `MAX_ARTICLES`: Article limit (0 = unlimited, default)
- `OPENAI_API_KEY`: OpenAI API access (required for classification and summaries)
- `ANTHROPIC_API_KEY`: Anthropic API access (optional, fallback)
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `STORAGE_DIR`: Data storage location (default: ./data)
- `LOG_PATH`: Log file path (default: ./logs/news_scraper.log)
- `MIN_ARTICLE_LENGTH`: Minimum article text length (default: 700)
- `ADMIN_USERNAME`: Admin login username (required for admin access)
- `ADMIN_PASSWORD`: Admin login password (required for admin access)

**Core Functions**:
- `load_config()`: Singleton configuration loader
- `reload_config()`: Force configuration reload
- `Config.validate()`: Configuration validation

### 9. Logging System (`logger.py`)

**Purpose**: Comprehensive logging with multiple backends.

**Features**:
- Loguru integration (preferred, if available)
- Standard Python logging fallback
- Console and file output
- Log rotation and compression (10MB, 5 backups)
- Colorized console output (Loguru)
- Structured logging format

**Log Levels**:
- DEBUG: Detailed execution information
- INFO: General operational messages
- WARNING: Non-critical issues
- ERROR: Processing failures
- CRITICAL: System-level errors

**Core Functions**:
- `setup_logger()`: Logger initialization
- `get_logger()`: Logger instance retrieval

### 10. Utilities (`utils.py`)

**Purpose**: Helper functions for data processing and system operations.

**Key Functions**:
- `rate_limit()`: Request throttling
- `sanitize_filename()`: Safe filename generation
- `generate_content_hash()`: MD5 hash for deduplication
- `format_duration()`: Human-readable time formatting
- `normalize_text()`: Text cleaning and whitespace normalization

### 11. Summaries (`summaries.py`)

**Purpose**: Article summary generation and caching for improved dashboard performance.

**Key Features**:
- Pre-computed Danish summaries using OpenAI API
- Caching mechanism to avoid redundant API calls
- Fallback to English text if API unavailable
- Thread-safe client initialization
- Lazy loading of OpenAI client

**Core Functions**:
- `get_or_generate_danish_summary()`: Get cached summary or generate new one
- `_get_openai_client()`: Lazy initialization of OpenAI client
- `_generate_summary_with_openai()`: Generate summary using OpenAI API

### 12. Language Support (`config/languages.py`)

**Purpose**: Multilingual interface translations.

**Supported Languages**:
- English (en) - default
- Danish (da)

**Translation Coverage**:
- All UI elements (buttons, labels, messages)
- AI topic names
- Domain category names
- Time labels (days, months, weeks)
- Error messages
- Status messages

**Core Functions**:
- `get_language()`: Get current language from session
- `set_language()`: Set language in session
- `t()`: Translation function
- `translate_ai_topic()`: AI topic translation
- `translate_domain_category()`: Domain category translation
- `translate_day_name()`: Day name translation
- `translate_month_name()`: Month name translation
- `translate_week_label()`: Week label translation

## Data Storage

### File Structure

```
data/
├── processed_articles.db          # SQLite database
├── articles_YYYYMMDD_HHMMSS.json  # Processed articles (formatted JSON)
├── metadata_YYYYMMDD_HHMMSS.json  # Article metadata
├── rejected_articles_*.json       # Failed articles
└── rejected_metadata_*.json       # Rejected article metadata

logs/
└── news_scraper.log              # Main log file (rotating, 10MB, 5 backups)
```

## API Integration

### GDELT Integration

- **API**: GDELT DOC 2.0
- **Coverage**: Worldwide news sources
- **Time Window**: Past 2 hours (minimum GDELT timespan)
- **Languages**: English and Danish focus (all languages accepted)
- **Rate Limiting**: 1-second delays between domain requests
- **Mode**: Unlimited (fetches all available articles)

### LLM API Integration

- **OpenAI**: GPT-4o-mini for classification (primary)
- **Anthropic**: Claude 3.5 Haiku as fallback
- **Rate Limiting**: 100ms delays between API calls
- **Error Handling**: Graceful fallback to keyword matching
- **Response Format**: JSON with structured classification results

## Performance Characteristics

### Scalability

- **Unlimited Mode**: No article limits (MAX_ARTICLES=0)
- **Batch Processing**: Efficient article processing
- **Database Optimization**: Indexed queries and cleanup
- **Memory Efficiency**: Streaming processing where possible

### Resource Usage

- **Memory**: Efficient processing with minimal overhead
- **Storage**: Compressed logs, JSON file rotation
- **Network**: Rate-limited API calls
- **CPU**: Single-threaded processing (can be parallelized)

### Error Handling

- **Domain Failures**: Persistent blacklisting after threshold
- **API Failures**: Graceful degradation to keyword matching
- **Processing Errors**: Comprehensive logging and recovery
- **Recovery**: Automatic retry mechanisms where appropriate

## Security Considerations

### Data Protection

- **API Keys**: Environment variable storage (never in code)
- **Logging**: No sensitive data in logs
- **Storage**: Local file system only
- **Network**: HTTPS-only API calls

### Access Control

- **Admin Authentication**: Username/password-based admin login
- **Environment Variables**: Admin credentials stored in environment variables (never in code)
- **Local Access**: Streamlit dashboard (localhost by default in production)
- **Process Isolation**: Separate subprocess execution
- **File Permissions**: Standard Unix permissions
- **HTTPS Support**: Recommended for production deployments

## Deployment

### System Requirements

- **Python**: 3.8+
- **Memory**: 2GB+ recommended
- **Storage**: 10GB+ for data and logs
- **Network**: Internet access for APIs
- **Server**: Ubuntu/Debian Linux for production deployment (optional)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_key
export ANTHROPIC_API_KEY=your_key
export FETCH_INTERVAL=120
export MAX_ARTICLES=0
export ADMIN_USERNAME=your_admin_username
export ADMIN_PASSWORD=your_admin_password
```

### Running the System

```bash
# Dashboard mode (local development)
streamlit run streamlit_app.py --server.port 8501

# Dashboard mode (production with base path)
streamlit run streamlit_app.py --server.port 8501 --server.address 127.0.0.1 --server.baseUrlPath=/aitrendtracker

# CLI single batch
python main.py --once

# CLI continuous mode
python main.py
```

### Production Deployment

#### Systemd Service

The application can be deployed as a systemd service for automatic startup and management:

1. **Create service file**: Copy `streamlit.service` to `/etc/systemd/system/`
2. **Update paths**: Modify `WorkingDirectory` and `ExecStart` paths
3. **Enable service**: `sudo systemctl enable streamlit`
4. **Start service**: `sudo systemctl start streamlit`
5. **Check status**: `sudo systemctl status streamlit`

**Service Features**:
- Automatic restart on failure
- Runs as background service
- Logs to systemd journal
- Supports base path configuration for subdirectory deployment

#### Nginx Reverse Proxy

For production deployment with custom domain and HTTPS:

1. **Install Nginx**: `sudo apt install nginx`
2. **Configure site**: Use `nginx-ai-center.conf` as template
3. **Enable site**: `sudo ln -s /etc/nginx/sites-available/your-site /etc/nginx/sites-enabled/`
4. **Test configuration**: `sudo nginx -t`
5. **Reload Nginx**: `sudo systemctl reload nginx`

**Nginx Features**:
- WebSocket support for real-time dashboard updates
- HTTPS support with Let's Encrypt (via Certbot)
- Subdirectory deployment (e.g., `/aitrendtracker`)
- Static file serving
- Reverse proxy to Streamlit on localhost

#### HTTPS Setup with Let's Encrypt

To enable HTTPS for your domain using Let's Encrypt:

1. **Install Certbot**:
   ```bash
   sudo apt update
   sudo apt install certbot python3-certbot-nginx -y
   ```

2. **Obtain SSL Certificate**:
   ```bash
   sudo certbot --nginx -d your-domain.com -d www.your-domain.com
   ```

Certbot will automatically:
- Obtain free SSL certificates from Let's Encrypt
- Update your existing `nginx-ai-center.conf` configuration
- Set up automatic renewal (certificates renew every 90 days)
- Configure HTTP to HTTPS redirect
- Configure modern TLS protocols and ciphers

**Certificate Renewal**:
- Certificates automatically renew via systemd timer
- Test renewal: `sudo certbot renew --dry-run`
- Check renewal status: `sudo systemctl status certbot.timer`

**Firewall Configuration**:
Ensure ports 80 and 443 are open:
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```

#### Environment Variables for Production

Ensure all required environment variables are set in your `.env` file:
- `OPENAI_API_KEY`: Required for AI classification and summaries
- `ANTHROPIC_API_KEY`: Optional, used as fallback
- `ADMIN_USERNAME`: Required for admin access
- `ADMIN_PASSWORD`: Required for admin access
- `FETCH_INTERVAL`: Pipeline execution interval (default: 120 minutes)
- `MAX_ARTICLES`: Article limit (0 = unlimited)
- `STORAGE_DIR`: Data storage directory
- `LOG_LEVEL`: Logging verbosity

## Monitoring and Maintenance

### Health Monitoring

- **Process Status**: PID tracking and health checks
- **Database Health**: Connection monitoring
- **API Status**: Rate limit and error tracking
- **Storage Usage**: Disk space monitoring

### Maintenance Tasks

- **Log Rotation**: Automatic cleanup (30 days retention)
- **Database Cleanup**: Old record removal (30 days retention)
- **File Cleanup**: JSON file rotation (manual or automated)
- **Error Recovery**: Automatic restart capabilities

### Troubleshooting

- **Common Issues**: Port conflicts, API limits, storage full
- **Debug Mode**: Enhanced logging (LOG_LEVEL=DEBUG)
- **Status Files**: Process tracking and error reporting
- **Log Analysis**: Comprehensive error tracking

## Codebase Structure

### File-by-File Overview

This section describes the purpose and functionality of each file in the codebase:

#### Core Application Files

- **`main.py`**: Main application entry point. Provides CLI interface with two modes: single batch (`--once`) and continuous scheduling (default, runs every 2 hours). Handles argument parsing, logging setup, and mode selection.

- **`pipeline.py`**: Main orchestration module. Coordinates the end-to-end workflow: fetching articles from GDELT, processing and validating content, AI topic classification, database storage, and statistics collection. Implements unlimited mode support and language-aware duplicate removal.

- **`fetcher.py`**: News article fetching module. Integrates with GDELT DOC 2.0 API to fetch worldwide news articles. Implements multi-library text extraction (Trafilatura, Goose3, Newspaper3k, Readability-lxml, BeautifulSoup) with fallback chain. Handles domain failure tracking, duplicate removal, and language detection.

- **`processor.py`**: Article processing and validation module. Validates article data (required fields, content length, format), normalizes encoding (UTF-8, Unicode NFKC), generates content hashes for deduplication, and stores articles as JSON files with metadata.

- **`ai_classifier.py`**: AI topic classification module. Uses LLM APIs (OpenAI GPT-4o-mini, Anthropic Claude 3.5 Haiku) to classify articles for AI-related content. Provides fallback keyword-based classification when APIs are unavailable. Categorizes articles into 14 AI topic categories with confidence scoring.

- **`database.py`**: SQLite database management module. Handles article storage, deduplication, pipeline run tracking, statistics aggregation, and data cleanup. Provides queries for dashboard analytics and article retrieval. Manages database schema and indexes.

- **`scheduler.py`**: Task scheduling module. Implements automated execution management for continuous pipeline operation. Handles configurable interval scheduling (default: 2 hours), graceful shutdown (SIGINT, SIGTERM), job re-registration on failure, and unlimited mode enforcement.

- **`streamlit_app.py`**: Streamlit web dashboard application. Provides user interface for pipeline monitoring and control. Features include: pipeline start/stop controls, real-time statistics display, AI article browsing with pagination, interactive charts (topics, categories, trends), multilingual support (English/Danish), admin login system, and database management.

- **`summaries.py`**: Article summary generation module. Generates and caches Danish summaries for articles using OpenAI API. Implements thread-safe client initialization, lazy loading, and fallback to English text when API is unavailable.

#### Configuration and Support Files

- **`config.py`**: Centralized configuration management. Loads settings from environment variables with sensible defaults. Manages storage directories, log paths, API keys, fetch intervals, article limits, and validation criteria. Provides singleton pattern for configuration access.

- **`config/__init__.py`**: Module initialization file. Re-exports `load_config` from parent `config.py` to resolve import conflicts when both `config.py` file and `config/` directory exist.

- **`config/languages.py`**: Multilingual translation support. Provides translation functions for UI elements, AI topics, domain categories, and time labels. Supports English (en) and Danish (da) languages. Implements language detection and session state management.

- **`logger.py`**: Logging configuration module. Sets up comprehensive logging with Loguru (preferred) or standard Python logging fallback. Provides console and file output, log rotation (10MB, 5 backups), colorized console output, and structured logging format.

- **`utils.py`**: Utility functions module. Provides helper functions for rate limiting, filename sanitization, content hashing (MD5), duration formatting, and text normalization.

#### Deployment and Configuration Files

- **`streamlit.service`**: Systemd service configuration file. Defines service settings for running Streamlit app as a background service on Linux. Includes working directory, environment variables, restart policy, and base path configuration.

- **`nginx-ai-center.conf`**: Nginx reverse proxy configuration template. Configures Nginx to proxy requests to Streamlit app with WebSocket support, subdirectory deployment (`/aitrendtracker`), and proper headers for real-time updates. When using Certbot for HTTPS, this file will be automatically modified to include SSL configuration.

- **`requirements.txt`**: Python package dependencies. Lists all required packages with version constraints for the project.

- **`.gitignore`**: Git ignore rules. Specifies files and directories to exclude from version control (e.g., `.env`, `__pycache__/`, `venv/`, `*.log`, `data/`, `*.db`).

#### Documentation Files

- **`README.md`**: Project overview and quick start guide. Provides feature list, installation instructions, usage examples, environment variables, and troubleshooting tips.

- **`Documentation.md`**: Comprehensive technical documentation. Detailed component analysis, architecture overview, API integration details, deployment instructions, and system requirements.

### Removed/Deprecated Components

The following components have been removed as part of codebase cleanup:

- `update_llm_prompt.py`: Obsolete migration script
- `update_pipeline_for_improved_classifier.py`: Obsolete migration script
- `NewsScheduler` class: Replaced by simpler `start_scheduler()` function
- NewsAPI integration: Removed in favor of GDELT-only approach
- Replacement article functions: Removed legacy replacement logic
- Duplicate unlimited fetch functions: Consolidated into single implementations

### Current Architecture

The system follows a clean, modular architecture with:

- **Separation of Concerns**: Each module has a single, well-defined purpose
- **Error Handling**: Comprehensive error handling at each layer
- **Logging**: Detailed logging throughout the system
- **Configuration**: Centralized configuration management
- **Testing**: CLI test modes available (stub implementations)

## Future Enhancements

### Potential Improvements

- **Additional Data Sources**: RSS feeds, other news APIs
- **Advanced Analytics**: Sentiment analysis, topic modeling
- **Real-time Processing**: WebSocket updates for dashboard
- **Cloud Deployment**: Docker, Kubernetes support
- **Machine Learning**: Custom classification models
- **API Endpoints**: REST API for external access
- **Additional Languages**: More language support in dashboard

### Scalability Options

- **Distributed Processing**: Multi-node deployment
- **Database Scaling**: PostgreSQL, MongoDB support
- **Caching**: Redis for performance
- **Load Balancing**: Multiple pipeline instances

## Conclusion

The AI Trend Tracker represents a comprehensive solution for automated news monitoring and AI content analysis. The system's modular architecture, robust error handling, and real-time analytics capabilities make it suitable for both research and production environments. The combination of GDELT data access, advanced text extraction, LLM-based classification, and interactive visualization provides a complete pipeline for AI trend monitoring and analysis.
