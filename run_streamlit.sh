#!/bin/bash
# Startup script for the News Scraping Pipeline Streamlit Dashboard

echo "🚀 Starting News Scraping Pipeline Dashboard..."
echo "=============================================="

# Activate virtual environment
source venv/bin/activate

# Set environment variables for unlimited mode
export MAX_ARTICLES=0

# Start Streamlit app
echo "📱 Starting Streamlit web application..."
echo "🌐 Access the dashboard at: http://localhost:8501"
echo "⏹️  Press Ctrl+C to stop the application"
echo ""

streamlit run streamlit_app.py --server.port 8501
