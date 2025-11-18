# AI Trend Tracker – News Pipeline and Dashboard

A practical system that fetches recent news articles from GDELT, classifies AI-related content using LLM APIs (OpenAI/Anthropic), stores them in SQLite, and visualizes results in a multilingual Streamlit dashboard.

## Features

- **GDELT Integration**: Fetches worldwide news articles from the past 2 hours (unlimited mode)
- **Robust Text Extraction**: Multi-library approach (Trafilatura, Goose3, Newspaper3k, Readability-lxml, BeautifulSoup)
- **AI Classification**: API-based LLM classification using OpenAI GPT-4o-mini or Anthropic Claude 3.5 Haiku
- **SQLite Storage**: Efficient local database with deduplication and analytics
- **Streamlit Dashboard**: Interactive web interface with:
  - Pipeline start/stop controls
  - Live statistics and metrics with automatic refresh (every 30 seconds when pipeline is running, and when pipeline completes each batch run)
  - Manual refresh button to refresh all data (stats, charts, articles)
  - Paginated AI article browser
  - Interactive trend charts (hourly, daily, weekly, monthly, yearly)
  - Multilingual support (English/Danish)
  - Admin login for pipeline management and database operations
  - Database clearing functionality
- **Article Summaries**: Pre-computed Danish summaries for articles using OpenAI
- **Domain Failure Tracking**: Persistent blacklisting of problematic domains
- **Comprehensive Logging**: Rotating log files with detailed execution tracking
- **Production Ready**: Systemd service configuration and Nginx reverse proxy support

## Quick Start

### 1. Setup Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file or set environment variables:

```bash
export OPENAI_API_KEY=your_openai_key
export ANTHROPIC_API_KEY=your_anthropic_key
export FETCH_INTERVAL=120          # minutes between runs (default: 120)
export MAX_ARTICLES=0              # 0 = unlimited mode (default)
export LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
export STORAGE_DIR=./data          # data storage directory
export ADMIN_USERNAME=your_admin_username  # Admin login username (required)
export ADMIN_PASSWORD=your_admin_password  # Admin login password (required)
```

### 3. Run the Dashboard

```bash
source venv/bin/activate
streamlit run streamlit_app.py --server.port 8501
```

Open `http://localhost:8501` in your browser.

### 4. Use the Dashboard

- **START**: Runs the pipeline in the background as a separate process
- **STOP**: Terminates the running pipeline
- **Auto-Refresh**: Automatically refreshes every 30 seconds when pipeline is running, and when pipeline completes each batch run (every 2 hours in continuous mode)
- **Manual Refresh**: Click the "🔄 Refresh Stats" button to refresh all data (stats, charts, and articles)
- **Language Selection**: Switch between English and Danish interface using flag icons
- **Admin Login**: Access admin controls by clicking the login button (requires ADMIN_USERNAME and ADMIN_PASSWORD)
- **Database Management**: Clear database functionality available in admin panel

### Dashboard Features

- **Live Statistics**: Total articles, AI articles, processing rates, success rates
- **AI Article Browser**: Paginated list (10 per page) with expandable details
- **Article Summaries**: Pre-computed Danish summaries for articles
- **Interactive Charts**:
  - AI Topics Distribution (bar chart)
  - Articles by Domain Category (bar chart)
  - Trend Analysis (line charts):
    - Hourly: Today (00-23)
    - Daily: Current week (Mon-Sun)
    - Weekly: Weeks 1-4 of current month
    - Monthly: January-December of current year
    - Yearly: From 2025 onward
- **Admin Panel**: Pipeline controls, database management, and system monitoring

## Command Line Interface

### Single Batch Mode

Run a single pipeline batch without the dashboard:

```bash
python main.py --once
```

This fetches, processes, classifies, and stores one batch, then exits.

### Continuous Mode

Run the pipeline continuously with scheduled intervals:

```bash
python main.py
```

The pipeline runs every 2 hours (configurable via `FETCH_INTERVAL`).

## Architecture

### Core Modules

- **`fetcher.py`**: GDELT API integration, text extraction, domain filtering, duplicate removal
- **`processor.py`**: Article validation, encoding normalization, JSON storage
- **`ai_classifier.py`**: LLM API integration (OpenAI/Anthropic) for AI topic classification
- **`pipeline.py`**: Main orchestration (fetch → process → classify → store → database)
- **`database.py`**: SQLite schema, queries, and analytics
- **`scheduler.py`**: Background scheduling for continuous operation
- **`streamlit_app.py`**: Web dashboard and pipeline process management
- **`summaries.py`**: Article summary generation and caching
- **`config.py`**: Centralized configuration with environment variable support
- **`logger.py`**: Logging setup (Loguru or standard logging)
- **`utils.py`**: Helper functions (rate limiting, hashing, text normalization)
- **`config/languages.py`**: Multilingual support (English/Danish translations)

### Data Flow

```
GDELT API → Fetcher → Processor → AI Classifier → Database → Dashboard
    ↓           ↓         ↓           ↓            ↓         ↓
  Articles → Validation → LLM API → SQLite → Streamlit UI
```

## Production Deployment

### Systemd Service

The application can be run as a systemd service. A sample service file (`streamlit.service`) is provided for deployment on Linux servers.

**Service Configuration**:
- Runs as a background service
- Automatic restart on failure
- Supports base path configuration for subdirectory deployment
- Logs to systemd journal

### Nginx Reverse Proxy

For production deployment with a custom domain, use Nginx as a reverse proxy. A sample configuration (`nginx-ai-center.conf`) is provided.

**Features**:
- WebSocket support for real-time updates
- HTTPS support with Let's Encrypt (via Certbot)
- Subdirectory deployment support (e.g., `/aitrendtracker`)
- Static file serving

### HTTPS Setup

To enable HTTPS for your domain:

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
- Update your Nginx configuration
- Set up automatic renewal
- Redirect HTTP to HTTPS

For detailed HTTPS setup instructions, see `Documentation.md`.

### Deployment Steps

1. **Clone repository** on your server
2. **Set up environment variables** in `.env` file
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Configure systemd service** (see `streamlit.service`)
5. **Configure Nginx** (see `nginx-ai-center.conf`)
6. **Set up HTTPS** (optional, see HTTPS Setup above)
7. **Start service**: `sudo systemctl start streamlit`

For detailed deployment instructions, see `Documentation.md`.

## Data Storage

### File Structure

```
data/
├── processed_articles.db          # SQLite database
├── articles_YYYYMMDD_HHMMSS.json  # Processed articles (JSON)
├── metadata_YYYYMMDD_HHMMSS.json  # Article metadata
└── rejected_articles_*.json       # Failed articles

logs/
└── news_scraper.log              # Main log file (rotating)
```

## AI Topic Categories

The system classifies articles into 14 AI topic categories:

- AI Research and Development
- AI Ethics and Regulations
- AI Safety and Governance
- AI Business and Industry
- AI Language Models and NLP
- AI Robotics and Automation
- AI Healthcare and Medical
- AI Education and Training
- AI Cybersecurity and Privacy
- AI Computer Vision
- AI Data Science and Analytics
- AI Neural Networks and Deep Learning
- AI Applications and Deployment
- AI Technology and Infrastructure

## Troubleshooting

### Port Already in Use

```bash
streamlit run streamlit_app.py --server.port 8502
```

### Missing Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Missing API Keys

Set `OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY` environment variables. The system will use keyword-based fallback if APIs are unavailable.

### No New Articles

GDELT may have limited articles in the current 2-hour window. The system fetches from the past 2 hours only (minimum GDELT timespan). Try again later or check logs for domain failures.

### Database Issues

```bash
# Check database
sqlite3 data/processed_articles.db "SELECT COUNT(*) FROM processed_articles;"

# View recent articles
sqlite3 data/processed_articles.db "SELECT title, domain, processed_at FROM processed_articles ORDER BY processed_at DESC LIMIT 10;"
```

### Admin Login Not Working

Ensure `ADMIN_USERNAME` and `ADMIN_PASSWORD` are set in your `.env` file or as environment variables. The admin login button will not appear if credentials are not configured.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for classification and summaries | None |
| `ANTHROPIC_API_KEY` | Anthropic API key for classification | None |
| `FETCH_INTERVAL` | Minutes between pipeline runs | 120 |
| `MAX_ARTICLES` | Maximum articles per batch (0 = unlimited) | 0 |
| `LOG_LEVEL` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) | INFO |
| `STORAGE_DIR` | Data storage directory | ./data |
| `LOG_PATH` | Log file path | ./logs/news_scraper.log |
| `ADMIN_USERNAME` | Admin login username (required for admin access) | None |
| `ADMIN_PASSWORD` | Admin login password (required for admin access) | None |

## Requirements

- Python 3.8+
- 2GB+ RAM recommended
- Internet connection for GDELT and LLM APIs
- 10GB+ disk space for data and logs

## License

MIT
