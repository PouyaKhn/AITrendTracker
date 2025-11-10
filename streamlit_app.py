"""
Streamlit Web Application for News Scraping Pipeline

This application provides a web interface to:
- Run the pipeline in unlimited mode
- View pipeline output and logs
- Monitor database statistics
- Track pipeline performance
"""

import streamlit as st
from datetime import datetime, timedelta
import time
import json
from pathlib import Path
import sqlite3
import re
from typing import List, Dict, Any
import os
import sys
import base64
import subprocess
import signal
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from collections import Counter, defaultdict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

                                                                 

                                   
from database import get_database, reset_database_instance

                               
from config.languages import LANGUAGES, get_language, set_language, t, translate_ai_topic, translate_domain_category, translate_day_name, translate_month_name, translate_week_label
from config import load_config

@st.cache_data(ttl=30)                             
def get_ai_articles_by_topic(language: str = None) -> Dict[str, int]:
    """Get count of AI articles by AI topic."""
    try:
        ai_articles = get_ai_articles_with_content()
        
        if not ai_articles:
            return {}
        
                                    
        topics = Counter()
        for article in ai_articles:
            topic = article.get('ai_topic', 'Unknown Topic')
            if topic and topic != 'Unknown Topic':
                                                 
                translated_topic = translate_ai_topic(topic)
                topics[translated_topic] += 1
        
        return dict(topics)
        
    except Exception as e:
                                                        
        return {}

@st.cache_data(ttl=30)                             
def get_ai_articles_by_category(language: str = None) -> Dict[str, int]:
    """Get count of AI articles by category."""
    try:
        db = get_database()
        ai_articles = db.get_recent_ai_articles(limit=10000)                    
        
        if not ai_articles:
            return {}
        
                                    
        categories = Counter()
        for article in ai_articles:
            category = article.get('domain_category', 'Unknown')
                                                
            translated_category = translate_domain_category(category)
            categories[translated_category] += 1
        
        return dict(categories)
        
    except Exception as e:
                                                        
        return {}

@st.cache_data(ttl=30)
def get_ai_articles_trend_data(time_period: str, language: str = None) -> Dict[str, int]:
    """Fixed-range trend bins for hourly/daily/weekly/monthly/yearly as requested."""
    try:
        import calendar
        db = get_database()
        ai_articles = db.get_recent_ai_articles(limit=100000)
        parsed = []
        for a in ai_articles or []:
            ts = a.get('processed_at')
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00')) if 'T' in ts else datetime.fromisoformat(ts)
                parsed.append(dt.replace(tzinfo=None))
            except Exception:
                continue
        now = datetime.now().replace(tzinfo=None)

        if time_period == 'hourly':
            labels = [f"{h:02d}:00" for h in range(24)]
            bins = {l: 0 for l in labels}
            today = now.date()
            for dt in parsed:
                if dt.date() == today:
                    bins[f"{dt.hour:02d}:00"] += 1
            return bins

        if time_period == 'daily':
            monday = now - timedelta(days=now.weekday())
            days = [monday + timedelta(days=i) for i in range(7)]
            labels = [d.strftime('%A') for d in days]
            bins = {l: 0 for l in labels}
            map_day = {d.date(): d.strftime('%A') for d in days}
            for dt in parsed:
                if dt.date() in map_day:
                    bins[map_day[dt.date()]] += 1
            
                                              
            translated_bins = {}
            for label, count in bins.items():
                translated_label = translate_day_name(label)
                translated_bins[translated_label] = count
            return translated_bins

        if time_period == 'weekly':
            labels = [f"Week {i}" for i in range(1, 5)]
            bins = {l: 0 for l in labels}
            y, m = now.year, now.month
            for dt in parsed:
                if dt.year == y and dt.month == m:
                    d = dt.day
                    if 1 <= d <= 7:
                        bins['Week 1'] += 1
                    elif 8 <= d <= 14:
                        bins['Week 2'] += 1
                    elif 15 <= d <= 21:
                        bins['Week 3'] += 1
                    else:
                        bins['Week 4'] += 1
            
                                              
            translated_bins = {}
            for label, count in bins.items():
                translated_label = translate_week_label(label)
                translated_bins[translated_label] = count
            return translated_bins

        if time_period == 'monthly':
            y = now.year
            labels = [calendar.month_name[i] for i in range(1, 13)]
            bins = {l: 0 for l in labels}
            for dt in parsed:
                if dt.year == y:
                    bins[calendar.month_name[dt.month]] += 1
            
                                              
            translated_bins = {}
            for label, count in bins.items():
                translated_label = translate_month_name(label)
                translated_bins[translated_label] = count
            return translated_bins

                
        start_year = 2025
        labels = [str(y) for y in range(start_year, max(start_year, now.year) + 1)]
        bins = {l: 0 for l in labels}
        for dt in parsed:
            y = str(dt.year)
            if int(y) >= start_year:
                if y not in bins:
                    bins[y] = 0
                bins[y] += 1
        return bins
    except Exception:
        return {}

                                                                                    

def generate_danish_summary(english_summary: str, url: str) -> str:
    """Generate Danish summary from English summary using OpenAI."""
    try:
        import openai
        import os
        from dotenv import load_dotenv
        
                                                                   
        load_dotenv()
        
                                         
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            print(f"Warning: No OpenAI API key found for translating: {url[:50]}...")
            return english_summary                                
        
                                  
        client = openai.OpenAI(api_key=openai_api_key)
        
                                       
        prompt = f"""Translate the following English article summary to Danish. Maintain the same meaning and tone.

English summary:
{english_summary}

Danish translation:"""

                         
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": "You are a professional English-to-Danish translator. Translate the given text to Danish."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=500
        )
        
        danish_summary = response.choices[0].message.content.strip()
        
                                                                           
        if danish_summary == english_summary or len(danish_summary) < 10:
            print(f"Warning: Translation seems to have failed for: {url[:50]}...")
            return english_summary
        
        print(f"✓ Translated summary for: {url[:50]}...")
        
                                            
        time.sleep(0.1)
        
        return danish_summary
        
    except Exception as e:
        print(f"Error translating summary for {url[:50]}...: {str(e)}")
                                                               
        return english_summary

def get_ai_articles_with_content() -> List[Dict[str, Any]]:
    """Get AI articles with their existing AI classification explanations from JSON files."""
    try:
        db = get_database()
        
                                       
        ai_articles = db.get_recent_ai_articles(limit=1000)                     
        
        if not ai_articles:
            return []
        
                                              
        data_dir = Path("data")
        articles_with_content = []
        
                                     
        danish_summaries_file = data_dir / "danish_summaries.json"
        danish_summaries = {}
        if danish_summaries_file.exists():
            try:
                with open(danish_summaries_file, 'r', encoding='utf-8') as f:
                    danish_summaries = json.load(f)
            except Exception as e:
                pass                                               
        
                                                   
        new_translations = 0
        max_translations_per_load = 10                          
        
                                               
        json_files = list(data_dir.glob("articles_*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    all_articles = json.load(f)
                
                                                      
                for ai_article in ai_articles:
                    for full_article in all_articles:
                        if full_article.get('url') == ai_article.get('url'):
                                                                                       
                            ai_analysis = full_article.get('ai_topic_analysis', {})
                            summary_en = ai_analysis.get('explanation', 'No AI explanation available')
                            
                                                                              
                            if summary_en.startswith('OpenAI: '):
                                summary_en = summary_en[8:]                            
                            
                                                            
                            url = ai_article.get('url', '')
                            if url in danish_summaries:
                                summary_da = danish_summaries[url]
                            else:
                                                                                          
                                if new_translations < max_translations_per_load:
                                    try:
                                        summary_da = generate_danish_summary(summary_en, url)
                                                       
                                        danish_summaries[url] = summary_da
                                        new_translations += 1
                                    except Exception as e:
                                                                                      
                                        summary_da = summary_en
                                else:
                                                                                    
                                    summary_da = summary_en
                            
                                                          
                            ai_topic = ai_analysis.get('topic', 'Unknown Topic')
                            ai_confidence = ai_analysis.get('confidence', 0.0)
                            
                            articles_with_content.append({
                                'title': ai_article.get('title', 'No title'),
                                'summary_en': summary_en,
                                'summary_da': summary_da,
                                'url': url,
                                'domain': ai_article.get('domain', 'Unknown'),
                                'published_date': full_article.get('date_publish', ''),
                                'processed_at': ai_article.get('processed_at', ''),
                                'language': ai_article.get('language', 'Unknown'),
                                'domain_category': ai_article.get('domain_category', 'Unknown'),
                                'ai_topic': ai_topic,
                                'ai_confidence': ai_confidence
                            })
                            break
            except Exception as e:
                st.error(f"Error reading {json_file}: {str(e)}")
                continue
        
                                             
        try:
            with open(danish_summaries_file, 'w', encoding='utf-8') as f:
                json.dump(danish_summaries, f, ensure_ascii=False, indent=2)
            
                                                                
            if new_translations > 0:
                st.info(f"✓ Genereret {new_translations} nye danske sammendrag. Genindlæs siden for at generere flere.")
        except Exception as e:
            pass                                          
        
                                                  
        articles_with_content.sort(key=lambda x: x.get('processed_at', ''), reverse=True)
        
        return articles_with_content
        
    except Exception as e:
        st.error(f"Error getting AI articles with content: {str(e)}")
        return []


def run_pipeline_simple():
    """Run pipeline with simple loading indicator."""
    import subprocess
    import sys
    import os
    from pathlib import Path
    
                                                  
    env = os.environ.copy()
    env['MAX_ARTICLES'] = '0'                  
    
    project_root = Path(__file__).parent
    
                      
    process = subprocess.Popen(
        [sys.executable, 'main.py', '--once'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        cwd=project_root
    )
    
                         
    stdout, _ = process.communicate()
    
    return process.returncode == 0

                    
st.set_page_config(
    page_title="AI Trend Tracker",
    page_icon="images/2. favicon_#f0f0f0-#d9e021.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

                               
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=TASA+Orbiter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
    /* Main container width - FULL WIDTH */
    .main .block-container {
        max-width: none !important;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Alternative approach for container width */
    .stApp > div:first-child {
        max-width: none !important;
        margin: 0;
    }
    
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #d9e021, #f0f0f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif !important;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
    /* Compact buttons (helps pagination) */
    .stButton > button {
        padding: 0.25rem 0.5rem;
        margin: 0 2px;
    }
    
    /* Hide Streamlit header - specific targeting */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Hide Streamlit toolbar */
    div[data-testid="stToolbar"] {
        display: none !important;
    }
    
    /* Hide Streamlit decorations */
    div[data-testid="stDecoration"] {
        display: none !important;
    }
    
    /* Prevent font preload warnings */
    link[rel="preload"][href*="SourceSansVF"] {
        display: none !important;
    }
    
    /* Global font family for all elements - TASA Orbiter */
    * {
        font-family: 'TASA Orbiter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Ensure font is loaded and applied */
    @font-face {
        font-family: 'TASA Orbiter';
        font-display: swap;
    }
    
    /* Force font application on key elements */
    body, html {
        font-family: 'TASA Orbiter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* More aggressive targeting for Streamlit elements */
    .stApp,
    .stApp *,
    .stApp *::before,
    .stApp *::after,
    [data-testid*="st"],
    [class*="st"],
    [class*="css"] {
        font-family: 'TASA Orbiter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Target specific Streamlit components */
    .stMarkdown,
    .stMarkdown *,
    .stButton,
    .stButton *,
    .stSelectbox,
    .stSelectbox *,
    .stTextInput,
    .stTextInput *,
    .stMetric,
    .stMetric *,
    .stContainer,
    .stContainer *,
    .stExpander,
    .stExpander * {
        font-family: 'TASA Orbiter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Force TASA Orbiter on introduction text specifically */
    .stMarkdown div[style*="padding: 20px 0; text-align: center;"] p,
    .stMarkdown div[style*="padding: 20px 0; text-align: center;"] p *,
    .stMarkdown div[style*="color: #555; line-height: 1.6; margin: 0; font-size: 1.1em;"] {
        font-family: 'TASA Orbiter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Target the specific introduction text container */
    .stMarkdown div[style*="padding: 20px 0; text-align: center;"] {
        font-family: 'TASA Orbiter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    .stMarkdown div[style*="padding: 20px 0; text-align: center;"] * {
        font-family: 'TASA Orbiter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Page background - 100% width */
    .stApp {
        background-color: #f0f2f6;
        font-family: 'TASA Orbiter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Ensure all text elements use the font */
    body, html, div, span, p, h1, h2, h3, h4, h5, h6, a, button, input, textarea, select, label, li, ul, ol, table, td, th, tr, caption, legend, fieldset, form, option, optgroup {
        font-family: 'TASA Orbiter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Streamlit specific elements */
    .stApp *, .stApp *::before, .stApp *::after {
        font-family: 'TASA Orbiter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Sticky header menu with typeface */
    .sticky-header {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 60px !important;
        background: linear-gradient(135deg, #d9e021 0%, #f0f0f0 50%) !important;
        z-index: 1000 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding: 0 20px !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1) !important;
        transform: translateY(0) !important;
        transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        will-change: transform !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    .sticky-header.hidden {
        transform: translateY(-100%);
    }
    
    .typeface-logo {
        height: 22px;
        opacity: 0.9;
    }
    
    .language-flags {
        display: flex !important;
        gap: 15px !important;
        align-items: center !important;
    }
    
    .flag-link {
        font-size: 30px !important;
        text-decoration: none !important;
        background: transparent !important;
        border: none !important;
        cursor: pointer !important;
        transition: transform 0.2s ease !important;
        line-height: 1 !important;
        display: inline-block !important;
    }
    
    .flag-link:hover {
        transform: scale(1.1) !important;
        width: auto;
    }
    
    /* Add padding to body to account for sticky header */
    .stApp {
        padding-top: 40px;
    }
    
    /* Main background gradient - yellow to light gray */
    .stMain {
        background: linear-gradient(135deg, #d9e021 0%, #f0f0f0 50%) !important;
    }
    
    /* Vertical block container - black background with white text */
    .stVerticalBlock {
        background-color: #0f0f0f !important;
        border-radius: 15px !important;
        color: white !important;
        padding: 15px !important;
    }
    .st-emotion-cache-wfksaw{
        gap: 0 !important;
    }
    
    /* Make all text inside stVerticalBlock white */
    .stVerticalBlock * {
        color: white !important;
    }
    
    /* Exception: Articles list should use default font, not Halyard Display */
    .stExpander,
    .stExpander *,
    .stExpander .stMarkdown,
    .stExpander .stMarkdown *,
    .stExpander .stMarkdown p,
    .stExpander .stMarkdown strong,
    .stExpander .stMarkdown h1,
    .stExpander .stMarkdown h2,
    .stExpander .stMarkdown h3,
    .stExpander .stMarkdown h4,
    .stExpander .stMarkdown h5,
    .stExpander .stMarkdown h6 {
        font-family: 'TASA Orbiter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Fix article expander text colors - ALL text should be white */
    .stExpander .stMarkdown p,
    .stExpander .stMarkdown h1,
    .stExpander .stMarkdown h2,
    .stExpander .stMarkdown h3,
    .stExpander .stMarkdown h4,
    .stExpander .stMarkdown h5,
    .stExpander .stMarkdown h6,
    .stExpander .stMarkdown span,
    .stExpander .stMarkdown div,
    .stExpander .stMarkdown strong,
    .stExpander .stMarkdown b,
    .stExpander .stMarkdown em,
    .stExpander .stMarkdown i {
        color: white !important;
    }
    
    /* Ensure ALL text in article details is white */
    .stExpander .stMarkdown * {
        color: white !important;
    }
    
    /* Override any specific targeting that might make text black */
    .stExpander .stMarkdown strong,
    .stExpander .stMarkdown b {
        color: white !important;
    }
    
    /* Hide script containers that take up unnecessary space */
    .stElementContainer:has(script),
    .stMarkdown:has(script),
    .stMarkdownContainer:has(script) {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    
    /* Alternative approach - target by content */
    .stElementContainer[data-testid="stElementContainer"]:has(script),
    .stMarkdown[data-testid="stMarkdown"]:has(script) {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    
    /* Smaller font only for article content - more targeted approach */
    .stVerticalBlock .stMarkdown p {
        font-size: 1.1em !important;
        line-height: 1.4 !important;
        font-family: 'TASA Orbiter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    .stVerticalBlock .stMarkdown strong {
        font-size: 0.9em !important;
    }
    
    /* Hide the keyboard_arrow_right text that appears when icons don't load */
    .st-emotion-cache-zkd0x0 {
        font-size: 0 !important;
        visibility: hidden !important;
    }
    
    /* Ensure the actual plus icon is visible */
    .st-emotion-cache-zkd0x0::before {
        content: "+" !important;
        font-size: 16px !important;
        visibility: visible !important;
        display: inline-block !important;
    }
    
    /* Increase font size of article expander titles (the clickable header) */
    .stExpander summary,
    .stExpander details summary,
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] details summary {
        font-size: 1.3em !important;
    }
    
    /* Target all possible Streamlit expander header classes */
    .st-emotion-cache-1xarl8l,
    .st-emotion-cache-1xarl8l p,
    [data-testid="stExpander"] > details > summary,
    [data-testid="stExpander"] > details > summary > div,
    [data-testid="stExpander"] > details > summary > div > p {
        font-size: 1.3em !important;
    }
    
    /* Target by attribute selector for expander headers */
    details[open] > summary,
    details:not([open]) > summary {
        font-size: 1.3em !important;
    }
    
    /* Style for expanded article dropdown details */
    .stExpander .st-emotion-cache-3n56ur {
        background: transparent !important;
        border-radius: 10px !important;
        margin-top: 10px !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* Prevent white background on article title when expanded */
    .stExpander .stMarkdown,
    .stExpander .stMarkdownContainer,
    .stExpander .stMarkdownContainer *,
    .stExpander .stMarkdown * {
        background: transparent !important;
    }
    
    /* Specifically target the title area to prevent white background */
    .stExpander .stMarkdown strong,
    .stExpander .stMarkdown b,
    .stExpander .stMarkdown h1,
    .stExpander .stMarkdown h2,
    .stExpander .stMarkdown h3,
    .stExpander .stMarkdown h4,
    .stExpander .stMarkdown h5,
    .stExpander .stMarkdown h6 {
        background: transparent !important;
    }
    
    /* Target the specific Streamlit class - change white to very dark grey */
    .st-emotion-cache-1tw2ey4 {
        background-color: #495057 !important;
    }
    
    /* Also target any similar classes that might have white backgrounds */
    .stExpander .st-emotion-cache-1tw2ey4,
    .stExpander [class*="st-emotion-cache-1tw2ey4"] {
        background-color: #495057 !important;
    }
    
    
    /* Remove any borders from expander content - more aggressive targeting */
    .stExpander,
    .stExpander *,
    .stExpander .stMarkdown,
    .stExpander .stMarkdownContainer,
    .stExpander .stMarkdownContainer *,
    .stExpander .stMarkdown *,
    .stExpander div,
    .stExpander div * {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* Remove focus borders and outlines */
    .stExpander:focus,
    .stExpander:focus-within,
    .stExpander .stMarkdown:focus,
    .stExpander .stMarkdownContainer:focus,
    .stExpander div:focus,
    .stExpander div:focus-within {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* Target specific Streamlit expander classes that might have borders */
    .stExpander [class*="st-emotion-cache"],
    .stExpander [class*="st-emotion-cache"] * {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* Remove any left border specifically */
    .stExpander .stMarkdown,
    .stExpander .stMarkdownContainer,
    .stExpander .stMarkdownContainer *,
    .stExpander div[class*="st-emotion-cache"] {
        border-left: none !important;
        border-right: none !important;
        border-top: none !important;
        border-bottom: none !important;
    }
    
    /* Make text black in expanded article details */
    .stExpander .st-emotion-cache-3n56ur * {
        color: black !important;
    }
    
    /* Ensure links are visible in expanded content */
    .stExpander .st-emotion-cache-3n56ur a {
        color: #0066cc !important;
        text-decoration: underline !important;
    }
    
    .stExpander .st-emotion-cache-3n56ur a:hover {
        color: #004499 !important;
    }
    
    /* Admin login form input text color - make text black */
    .stTextInput input,
    .stTextInput input[type="text"],
    .stTextInput input[type="password"] {
        color: black !important;
    }
    
    /* Target Streamlit text input specifically */
    div[data-testid="stTextInput"] input {
        color: black !important;
    }
    
    /* Target password input specifically */
    div[data-testid="stTextInput"] input[type="password"] {
        color: black !important;
    }
    
    /* Ensure placeholder text is visible but input text is black */
    .stTextInput input::placeholder {
        color: #666 !important;
    }
    
    .stTextInput input:focus {
        color: black !important;
    }
    
    /* Target all form inputs in the admin login area */
    .stForm .stTextInput input,
    .stForm .stTextInput input[type="text"],
    .stForm .stTextInput input[type="password"] {
        color: black !important;
    }
    
    /* Button styling - white background with black text */
    .stButton > button,
    button {
        background: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
        transition: all 0.3s ease !important;
    }
    
    /* Force black text on all button text elements */
    .stButton > button *,
    button *,
    .stButton > button span,
    button span {
        color: black !important;
    }
    
    /* Button hover effect */
    .stButton > button:hover:not(:disabled),
    button:hover:not(:disabled) {
        background: #f8f9fa !important;
        color: black !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        border-color: #ccc !important;
    }
    
    /* Force black text on hover */
    .stButton > button:hover:not(:disabled) *,
    button:hover:not(:disabled) *,
    .stButton > button:hover:not(:disabled) span,
    button:hover:not(:disabled) span {
        color: black !important;
    }
    
    /* Disabled button styling */
    .stButton > button:disabled,
    button:disabled,
    .stButton > button[disabled],
    button[disabled] {
        background: #cccccc !important;
        color: #666666 !important;
        cursor: not-allowed !important;
        opacity: 0.6 !important;
        transform: none !important;
        box-shadow: none !important;
    }
    
    /* Force gray text on disabled buttons */
    .stButton > button:disabled *,
    button:disabled *,
    .stButton > button[disabled] *,
    button[disabled] *,
    .stButton > button:disabled span,
    button:disabled span,
    .stButton > button[disabled] span,
    button[disabled] span {
        color: #666666 !important;
    }
    
    /* Disabled button hover - no effect */
    .stButton > button:disabled:hover,
    button:disabled:hover,
    .stButton > button[disabled]:hover,
    button[disabled]:hover {
        background: #cccccc !important;
        color: #666666 !important;
        transform: none !important;
        box-shadow: none !important;
    }
    .stHeading {
        margin-top: 10px !important;
        margin-bottom: 10px !important;
    }
    
    /* Make pagination buttons wider */
    .stButton > button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-secondary"] {
        min-width: 120px !important;
        padding: 8px 16px !important;
        background: white !important;
        border: 1px solid #ddd !important;
        color: black !important;
    }
    
    /* Target all buttons in the pagination area */
    .stButton > button {
        min-width: 85px !important;
        padding: 10px 20px !important;
        white-space: nowrap !important;
        background: white !important;
        border: 1px solid #ddd !important;
        color: black !important;
    }
    
    /* Specific targeting for pagination buttons */
    div[data-testid="column"] button {
        min-width: 100px !important;
        padding: 10px 20px !important;
        white-space: nowrap !important;
        margin: 0 10px !important;
        background: white !important;
        border: 1px solid #ddd !important;
        color: black !important;
    }
    
    /* Add spacing between pagination button columns */
    div[data-testid="column"] {
        margin: 0 5px !important;
    }
    
    /* Center the pagination buttons container */
    div[data-testid="column"]:has(button) {
        display: flex !important;
        justify-content: center !important;
        gap: 16px !important;
    }
    
    /* Alternative approach - target the specific pagination area */
    .stContainer > div[data-testid="column"] {
        margin: 0 8px !important;
    }
    
    /* Style horizontal separators (hr elements) */
    hr {
        border: none !important;
        height: 3px !important;
        background: linear-gradient(270deg, #d9e021 0%, #f0f0f0 100%) !important;
        margin: 20px 0 !important;
    }
    
    /* Target Streamlit markdown separators */
    .stMarkdown hr {
        border: none !important;
        height: 3px !important;
        background: linear-gradient(270deg, #d9e021 0%, #f0f0f0 100%) !important;
        margin: 20px 0 !important;
    }
    
    /* Fix refresh charts button text color - more aggressive targeting */
    .stButton > button,
    .stButton > button *,
    .stButton > button span {
        color: black !important;
    }
    
    /* Force white background on all Streamlit button types */
    .stButton > button[data-testid="baseButton-primary"],
    .stButton > button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-primary"],
    button[data-testid="baseButton-secondary"] {
        background: white !important;
        border: 1px solid #ddd !important;
        color: black !important;
    }
    
    /* Force white background on all button variants */
    .stButton > button[type="primary"],
    .stButton > button[type="secondary"],
    button[type="primary"],
    button[type="secondary"] {
        background: white !important;
        border: 1px solid #ddd !important;
        color: black !important;
    }
    
    /* Fix select time period input text color - comprehensive targeting */
    .stSelectbox,
    .stSelectbox *,
    .stSelectbox label,
    .stSelectbox input,
    .stSelectbox div,
    .stSelectbox span {
        color: black !important;
    }
    
    /* Target all form elements */
    .stForm,
    .stForm *,
    .stForm label,
    .stForm input,
    .stForm div,
    .stForm span {
        color: black !important;
    }
    
    /* Force black text on all interactive elements */
    .stApp [data-testid="stSelectbox"] *,
    .stApp [data-testid="stButton"] * {
        color: black !important;
    }
    
    /* Make Plotly chart corners rounder */
    .stPlotlyChart,
    .js-plotly-plot,
    .plot-container.plotly,
    .main-svg {
        border-radius: 15px !important;
    }
    
    /* Yellow gradient border for specific class */
    .st-emotion-cache-1n6tfoc {
        border: 3px solid #f0f0f0 !important;
        border-radius: 10px !important;
    }
    
    
    /* Main content container - simple styling */
    .main .block-container {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        padding: 2rem;
        margin: 1rem auto;
        position: relative !important;
    }
    
    /* Footer styling */
    .footer-container {
        background-color: #f8f9fa;
        border-top: 1px solid #dee2e6;
        padding: 1rem 0;
    }
    
    /* Smooth animation for intro content */
        @keyframes slideDown {
            from { 
                opacity: 0; 
                transform: translateY(-20px); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0); 
            }
        }
    
    /* Language selector styling */
    .stButton > button {
        font-size: 18px !important;
        padding: 8px 12px !important;
        min-height: 40px !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }
    
    /* Compact language selector buttons */
    [data-testid="stButton"]:has(button[title="English"]),
    [data-testid="stButton"]:has(button[title="Dansk"]) {
        margin: 0 !important;
    }
    
    [data-testid="stButton"]:has(button[title="English"]) button,
    [data-testid="stButton"]:has(button[title="Dansk"]) button,
    button[title="English"],
    button[title="Dansk"] {
        font-size: 30px !important;
        line-height: 1 !important;
        padding: 6px 10px !important;
        min-height: 36px !important;
        width: 50px !important;
    }
    
    /* Additional selector for button text content */
    [data-testid="stButton"]:has(button[title="English"]) button > *,
    [data-testid="stButton"]:has(button[title="Dansk"]) button > *,
    [data-testid="stButton"]:has(button[title="English"]) button p,
    [data-testid="stButton"]:has(button[title="Dansk"]) button p,
    [data-testid="stButton"]:has(button[title="English"]) button div,
    [data-testid="stButton"]:has(button[title="Dansk"]) button div,
    button[title="English"] > *,
    button[title="Dansk"] > *,
    button[title="English"] p,
    button[title="Dansk"] p,
    button[title="English"] div,
    button[title="Dansk"] div {
        font-size: 30px !important;
        line-height: 1 !important;
    }
    
    @keyframes slideUp {
        from {
            opacity: 1;
            transform: translateY(0);
            max-height: 500px;
            padding: 20px;
        }
        to {
            opacity: 0;
            transform: translateY(-20px);
            max-height: 0;
            padding: 0 20px;
        }
    }
    
    /* Apply animation to intro content */
    #intro-content {
        animation: slideDown 0.6s ease-out;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

def admin_login_page():
    """Admin login page."""
    st.markdown(f'<h1 class="main-header">🔐 {t("admin_login")} - {t("app_title")}</h1>', unsafe_allow_html=True)
    
                
    with st.container():
        st.markdown(f"### {t('admin_controls')}")
        st.markdown(t('admin_credentials_message'))
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            username = st.text_input(f"{t('username')}:", placeholder=t('enter_username'))
        
        with col2:
            password = st.text_input(f"{t('password')}:", type="password", placeholder=t('enter_password'))
        
                      
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(f"🔑 {t('login')}", type="primary", width='stretch'):
                # Get admin credentials from environment variables
                admin_username = os.getenv('ADMIN_USERNAME', '')
                admin_password = os.getenv('ADMIN_PASSWORD', '')
                
                if not admin_username or not admin_password:
                    st.error("❌ Admin credentials not configured. Please set ADMIN_USERNAME and ADMIN_PASSWORD environment variables.")
                elif username == admin_username and password == admin_password:
                    st.session_state.admin_logged_in = True
                    st.session_state.show_login = False                    
                    st.success(f"✅ {t('login_successful')}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {t('login_failed')}")
        
                     
        with col1:
            if st.button(f"⬅️ {t('back_to_main')}", width='stretch'):
                st.session_state.show_login = False
                st.rerun()
        
                   
        st.info(f"💡 {t('contact_admin_message')}")


                                             


def main():
    """Main Streamlit application."""
    
                              
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    if 'show_login' not in st.session_state:
        st.session_state.show_login = False
                                        
    query_params = st.query_params
    lang_param = query_params.get('lang', 'da')
    
                                           
    if 'language' not in st.session_state:
        st.session_state.language = lang_param
    elif st.session_state.language != lang_param:
        st.session_state.language = lang_param
    
                                                         
    typeface_logo = base64.b64encode(open("images/5. typeface_#0f0f0f.png", "rb").read()).decode()
    
                           
    # Use relative URLs to work with any domain/IP
    en_link = "/?lang=en"
    da_link = "/?lang=da"
    
    st.markdown(f'''
        <div class="sticky-header" id="stickyHeader">
            <img src="data:image/png;base64,{typeface_logo}" class="typeface-logo" alt="Typeface Logo">
            <div class="language-flags">
                <a href="{en_link}" target="_self" class="flag-link" title="English">🇬🇧</a>
                <a href="{da_link}" target="_self" class="flag-link" title="Dansk">🇩🇰</a>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    
    
                                                      
    st.markdown('<div style="display:flex; align-items:center; justify-content:center; gap:8px; text-align:center;"><img src="data:image/png;base64,{}" width="70" style="display:block; align-self:center;"><h1 class="main-header" style="margin:0; line-height:1;">{}</h1></div>'.format(
        base64.b64encode(open("images/2. favicon_#f0f0f0-#d9e021.png", "rb").read()).decode(),
        t('app_title')
    ), unsafe_allow_html=True)
    
                                                                                         
    st.markdown(f"""
    <div style="padding: 0.5rem 0; text-align: center; margin: 10px;">
        <p style="font-size: 1.4rem; line-height: 1.8; color: #333; margin: 0; font-weight: 400;">
            {t('welcome_text')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
                                                 
                                                 
    if 'intro_expanded' not in st.session_state:
        st.session_state.intro_expanded = False
    
                            
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn2:
        if st.button(t('read_more'), width='stretch'):
            st.session_state.intro_expanded = not st.session_state.intro_expanded
    
                                                                   
    if st.session_state.intro_expanded:
        st.markdown(f"""
        <style>
        @keyframes smoothExpand {{
            from {{
                max-height: 0;
                opacity: 0;
                transform: translateY(-10px);
            }}
            to {{
                max-height: 1000px;
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        .intro-expanded-content {{
            animation: smoothExpand 0.5s ease-out forwards;
            overflow: hidden;
        }}
        </style>
        <div class="intro-expanded-content" style="color: white; width: 100%; margin: 0; padding: 0; background: transparent; border-radius: 10px;">
            <p style="margin-bottom: 1rem; text-align: left;">
                {t('detailed_description')}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
                                  
    if st.session_state.show_login:
        admin_login_page()
        return
    
                                                        
    st.markdown(
        """
        <script>
        setTimeout(function(){ window.location.reload(); }, 300000);
        </script>
        """,
        unsafe_allow_html=True
    )
    
                                   
    st.markdown(
        """
        <script>
        (function() {
            let lastScrollTop = 0;
            let isHidden = false;
            let header = null;
            
            function init() {
                header = document.getElementById('stickyHeader');
                if (header) {
                    console.log('Header found, setting up scroll listener');
                    window.addEventListener('scroll', handleScroll, { passive: true });
                } else {
                    console.log('Header not found, retrying...');
                    setTimeout(init, 100);
                }
            }
            
            function handleScroll() {
                if (!header) return;
                
                let scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                
                if (scrollTop > lastScrollTop && scrollTop > 50 && !isHidden) {
                    console.log('Hiding header');
                    header.classList.add('hidden');
                    isHidden = true;
                } else if (scrollTop < lastScrollTop && isHidden) {
                    console.log('Showing header');
                    header.classList.remove('hidden');
                    isHidden = false;
                }
                
                lastScrollTop = scrollTop;
            }
            
            // Start when DOM is ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', init);
            } else {
                init();
            }
        })();
        
        // Function to update admin login state
        function updateAdminState(isLoggedIn) {
            if (isLoggedIn) {
                document.body.classList.add('admin-logged-in');
                // Show script containers when admin is logged in (if needed)
                const scriptContainers = document.querySelectorAll('.stElementContainer:has(script)');
                scriptContainers.forEach(container => {
                    container.style.display = 'block';
                });
            } else {
                document.body.classList.remove('admin-logged-in');
                // Hide script containers when admin is not logged in
                const scriptContainers = document.querySelectorAll('.stElementContainer:has(script)');
                scriptContainers.forEach(container => {
                    container.style.display = 'none';
                });
            }
        }
        
        // Check admin state on page load
        // This will be updated by the Python session state
        updateAdminState(false); // Default to not logged in
        
        // Fix font preload warnings by removing unused preload links
        document.addEventListener('DOMContentLoaded', function() {
            const preloadLinks = document.querySelectorAll('link[rel="preload"][href*="SourceSansVF"]');
            preloadLinks.forEach(link => {
                link.remove();
            });
            
            // Debug font loading
            if (document.fonts) {
                document.fonts.ready.then(function() {
                    console.log('Fonts loaded');
                    // Check if TASA Orbiter is available
                    if (document.fonts.check('16px "TASA Orbiter"')) {
                        console.log('TASA Orbiter font is available');
                    } else {
                        console.log('TASA Orbiter font is not available, using fallback');
                    }
                });
            }
            
            // Hide script containers immediately
            function hideScriptContainers() {
                const scriptContainers = document.querySelectorAll('.stElementContainer:has(script), .stMarkdown:has(script)');
                let hiddenCount = 0;
                scriptContainers.forEach(container => {
                    container.style.display = 'none';
                    container.style.height = '0';
                    container.style.margin = '0';
                    container.style.padding = '0';
                    container.style.overflow = 'hidden';
                    hiddenCount++;
                });
                console.log(`Hidden ${hiddenCount} script containers`);
            }
            
            // Run immediately to hide script containers
            hideScriptContainers();
            setTimeout(hideScriptContainers, 100);
            setTimeout(hideScriptContainers, 500);
            
            // Add button click feedback and state management
            function addButtonFeedback() {
                const buttons = document.querySelectorAll('.stButton > button, button');
                buttons.forEach(button => {
                    // Add click feedback
                    button.addEventListener('click', function(e) {
                        if (!this.disabled) {
                            // Add visual feedback
                            this.style.transform = 'scale(0.95)';
                            setTimeout(() => {
                                this.style.transform = '';
                            }, 150);
                        }
                    });
                    
                    // Ensure disabled state is properly applied
                    if (this.disabled || this.getAttribute('disabled') !== null) {
                        this.style.background = '#cccccc';
                        this.style.color = '#666666';
                        this.style.cursor = 'not-allowed';
                        this.style.opacity = '0.6';
                    }
                });
            }
            
            // Apply button feedback
            addButtonFeedback();
            setTimeout(addButtonFeedback, 500);
            setTimeout(addButtonFeedback, 1000);
            
            // Force TASA Orbiter on introduction text specifically
            function forceIntroTextFont() {
                // Target the introduction text container
                const introContainers = document.querySelectorAll('.stMarkdown div[style*="padding: 20px 0; text-align: center;"]');
                introContainers.forEach(container => {
                    // Apply font to container and all children
                    container.style.fontFamily = "'TASA Orbiter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif";
                    
                    // Apply font to all child elements
                    const allChildren = container.querySelectorAll('*');
                    allChildren.forEach(child => {
                        child.style.fontFamily = "'TASA Orbiter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif";
                    });
                });
                
                // Also target by paragraph content
                const introParagraphs = document.querySelectorAll('.stMarkdown p[style*="color: #555; line-height: 1.6; margin: 0; font-size: 1.1em;"]');
                introParagraphs.forEach(p => {
                    p.style.fontFamily = "'TASA Orbiter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif";
                });
                
                console.log(`Applied TASA Orbiter to ${introContainers.length} intro containers and ${introParagraphs.length} intro paragraphs`);
            }
            
            // Apply intro text font
            forceIntroTextFont();
            setTimeout(forceIntroTextFont, 500);
            setTimeout(forceIntroTextFont, 1000);
            
            // Force font application after page loads - comprehensive approach
            function forceFontOnAllElements() {
                // Get all possible selectors for elements
                const selectors = [
                    'body', 'html', 'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                    'a', 'button', 'input', 'textarea', 'select', 'label', 'li', 'ul', 'ol',
                    'table', 'td', 'th', 'tr', 'caption', 'legend', 'fieldset', 'form',
                    'option', 'optgroup', 'strong', 'em', 'b', 'i', 'small', 'big',
                    '[class*="st"]', '[data-testid*="st"]', '[class*="css"]',
                    '.stMarkdown', '.stButton', '.stSelectbox', '.stTextInput', '.stMetric',
                    '.stContainer', '.stColumn', '.stDataFrame', '.stPlotlyChart',
                    '.stAlert', '.stSuccess', '.stError', '.stWarning', '.stInfo',
                    '.stProgress', '.stSpinner', '.stSidebar', '.stMain'
                ];
                
                let elementsProcessed = 0;
                let articlesSkipped = 0;
                
                selectors.forEach(function(selector) {
                    try {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(function(element) {
                            // Skip if element is inside articles list (stExpander)
                            if (element.closest('.stExpander')) {
                                articlesSkipped++;
                                return;
                            }
                            
                            // Apply font with !important
                            element.style.setProperty('font-family', 
                                "'TASA Orbiter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif", 
                                'important'
                            );
                            elementsProcessed++;
                        });
                    } catch (e) {
                        console.log('Error processing selector:', selector, e);
                    }
                });
                
                console.log(`Font applied to ${elementsProcessed} elements, skipped ${articlesSkipped} article elements`);
            }
            
            // Run immediately and then again after delays to catch dynamically loaded content
            forceFontOnAllElements();
            setTimeout(forceFontOnAllElements, 500);
            setTimeout(forceFontOnAllElements, 1000);
            setTimeout(forceFontOnAllElements, 2000);
            
            // Also run when new content is added (for dynamic updates)
            const observer = new MutationObserver(function(mutations) {
                let shouldUpdate = false;
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                        shouldUpdate = true;
                    }
                });
                if (shouldUpdate) {
                    setTimeout(forceFontOnAllElements, 100);
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        });
        </script>
        """,
        unsafe_allow_html=True
    )
    
                                                  
    if st.session_state.admin_logged_in:
        st.markdown("""
        <script>
        document.body.classList.add('admin-logged-in');
        </script>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <script>
        document.body.classList.remove('admin-logged-in');
        </script>
        """, unsafe_allow_html=True)
    
                                               
    
                                                 
    # Use config storage directory for PID files to ensure correct paths on server
    config = load_config()
    pid_file = config.storage_dir / "pipeline.pid"
    start_time_file = config.storage_dir / "pipeline_start.txt"
    
    def _read_pid() -> int:
        try:
            if pid_file.exists():
                pid_text = pid_file.read_text().strip()
                return int(pid_text) if pid_text else 0
            return 0
        except Exception:
            return 0
    
    def _is_pid_running(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
                                                       
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
                                                        
            return True
        except Exception:
            return False
    
    def _start_pipeline_subprocess() -> bool:
        try:
                                            
            existing_pid = _read_pid()
            if _is_pid_running(existing_pid):
                return True
            
            env = os.environ.copy()
            env['MAX_ARTICLES'] = '0'
            
            # Ensure .env file is loaded - read it directly and add to subprocess environment
            from dotenv import dotenv_values
            env_file = Path(__file__).parent / '.env'
            if env_file.exists():
                # Read .env file directly and add all values to subprocess environment
                env_vars = dotenv_values(env_file)
                for key, value in env_vars.items():
                    # Add all values, including empty ones (they might be needed for validation)
                    if value is not None:  # None means key doesn't exist, empty string is valid
                        env[key] = value
                                                                        
            # Don't redirect stdout/stderr so pipeline logs appear in terminal
            # Logs will also be written to the log file configured in config.py
            proc = subprocess.Popen(
                [sys.executable, 'main.py'],
                cwd=Path(__file__).parent,
                env=env,
                # stdout and stderr are None by default, which means they inherit from parent
                # This allows logs to appear in the Streamlit terminal
            )
            pid_file.parent.mkdir(parents=True, exist_ok=True)
            pid_file.write_text(str(proc.pid))
                               
            try:
                start_time_file.write_text(datetime.now().isoformat())
            except Exception:
                pass
            return True
        except Exception as e:
            st.error(f"Failed to start pipeline: {e}")
            return False
    
    def _stop_pipeline_subprocess() -> bool:
        try:
            pid = _read_pid()
            if pid <= 0:
                return True
                               
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
                          
            time.sleep(1.0)
                                          
            if _is_pid_running(pid):
                try:
                    os.kill(pid, signal.SIGKILL)
                except Exception:
                    pass
                               
            try:
                if pid_file.exists():
                    pid_file.unlink()
            except Exception:
                pass
            return True
        except Exception as e:
            st.error(f"Failed to stop pipeline: {e}")
            return False
    
                              
    current_pid = _read_pid()
    is_running = _is_pid_running(current_pid)
                       
    start_time_val = None
    try:
        if start_time_file.exists():
            start_time_val = start_time_file.read_text().strip()
    except Exception:
        start_time_val = None
                                                               
    last_update_val = None
    try:
        # Use config storage directory for consistency
        data_dir = config.storage_dir
        json_files = list(data_dir.glob("articles_*.json"))
        if json_files:
            latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
            last_update_val = datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
    except Exception:
        last_update_val = None
    status = {
        'status': 'running' if is_running else 'stopped',
        'thread_alive': is_running,
        'is_running': is_running,
        'start_time': start_time_val,
        'last_update': last_update_val,
        'error_message': ''
    }
    
                                                                            
    if st.session_state.admin_logged_in:
                               
        if status['status'] == 'running':
            st.success(f"🟢 {t('pipeline_running_with_interval')}")
            
        elif status['status'] == 'error':
            st.error(f"🔴 {t('pipeline_error')} - {status.get('error_message', t('unknown_error'))}")
        else:
            st.info(f"⚪ {t('pipeline_stopped_click_start')}")
        
                                               
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"▶️ {t('start_button')}", 
                        type="primary", 
                        width='stretch',
                        disabled=status['status'] == 'running'):
                if _start_pipeline_subprocess():
                    st.success("🚀 Pipeline started! Running every 2 hours.")
                    st.rerun()
                else:
                    st.error("❌ Failed to start pipeline")
        
        with col2:
            if st.button(f"⏹️ {t('stop_button')}", 
                        type="secondary", 
                        width='stretch',
                        disabled=status['status'] == 'stopped'):
                with st.spinner("Stopping pipeline..."):
                    stop_result = _stop_pipeline_subprocess()
                    if stop_result:
                        st.success(f"⏹️ {t('tracker_offline')}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to stop pipeline")
                        st.warning("💡 Pipeline may not actually be running")
                        
                                             
                        st.write(f"**Current Status:** {'running' if _is_pid_running(_read_pid()) else 'stopped'}")
                        st.write(f"**PID:** {_read_pid() or 'N/A'}")
                        
                                                     
                        if st.button("🔧 Force Stop", type="secondary", width='stretch'):
                            with st.spinner("Force stopping pipeline..."):
                                force_result = _stop_pipeline_subprocess()
                                if force_result:
                                    st.success("🔧 Pipeline force stopped")
                                    st.rerun()
                                else:
                                    st.error("❌ Force stop also failed")
        
        with col3:
            # Initialize session state for clear database confirmation
            if 'show_clear_confirm' not in st.session_state:
                st.session_state['show_clear_confirm'] = False
            
            if st.button(f"🗑️ {t('clear_database')}", 
                        type="secondary", 
                        width='stretch',
                        help="⚠️ WARNING: This will permanently delete all articles, statistics, and history"):
                st.session_state['show_clear_confirm'] = True
                st.rerun()
            
            # Show confirmation UI if requested
            if st.session_state.get('show_clear_confirm', False):
                st.warning("⚠️ **DANGER ZONE** ⚠️")
                st.error("This action will permanently delete ALL data:")
                st.write("• All articles from the database")
                st.write("• All statistics and analytics")
                st.write("• All processing history")
                st.write("• All AI classifications")
                
                confirm_col1, confirm_col2 = st.columns(2)
                with confirm_col1:
                    if st.button(f"✅ {t('confirm_clear')}", type="primary", width='stretch'):
                        st.session_state['show_clear_confirm'] = False
                        with st.spinner("Clearing database..."):
                            try:
                                db = get_database()
                                
                                # Get the data directory from the database path
                                data_dir = db.db_path.parent.resolve()
                                
                                # Get counts before clearing for verification
                                total_before = db.get_total_article_count()
                                ai_before = db.get_ai_article_count()
                                
                                # Clear database first
                                db.clear_all_data()
                                
                                # Reset database singleton to force fresh connection
                                reset_database_instance()
                                
                                # Verify database was cleared
                                db_new = get_database()
                                total_after = db_new.get_total_article_count()
                                ai_after = db_new.get_ai_article_count()
                                
                                if total_after > 0 or ai_after > 0:
                                    raise Exception(f"Database not fully cleared! Remaining: {total_after} total, {ai_after} AI articles")
                                
                                # Delete all JSON files (articles, metadata, danish summaries)
                                json_files = list(data_dir.glob("articles_*.json"))
                                metadata_files = list(data_dir.glob("metadata_*.json"))
                                danish_summaries_file = data_dir / "danish_summaries.json"
                                
                                deleted_files = 0
                                for file in json_files + metadata_files:
                                    if file.exists():
                                        file.unlink()
                                        deleted_files += 1
                                
                                # Delete danish summaries file
                                if danish_summaries_file.exists():
                                    danish_summaries_file.unlink()
                                    deleted_files += 1
                                
                                # Clear ALL Streamlit caches (data and resource)
                                # This clears all cached data including all @st.cache_data functions
                                try:
                                    st.cache_data.clear()
                                except Exception as cache_error:
                                    print(f"Warning: Could not clear cache_data: {cache_error}")
                                
                                try:
                                    if hasattr(st, 'cache_resource'):
                                        st.cache_resource.clear()
                                except Exception as cache_error:
                                    print(f"Warning: Could not clear cache_resource: {cache_error}")
                                
                                # Note: st.cache is deprecated and doesn't have a .clear() method
                                # Only st.cache_data and st.cache_resource have .clear() methods
                                
                                # Set session state to force refresh
                                st.session_state['db_cleared'] = True
                                st.session_state['last_clear_time'] = time.time()
                                
                                st.success(f"🗑️ Database cleared successfully! Deleted {total_before} articles ({ai_before} AI) and {deleted_files} JSON files.")
                                st.info("All articles, statistics, and history have been permanently deleted. Refreshing page...")
                                time.sleep(1)
                                st.rerun()
                                
                            except Exception as e:
                                import traceback
                                error_details = traceback.format_exc()
                                st.error(f"❌ Failed to clear database: {str(e)}")
                                st.code(error_details, language="python")
                                print(f"Database clear error: {error_details}")  # Log to console
                
                with confirm_col2:
                    if st.button(f"❌ {t('cancel')}", type="secondary", width='stretch'):
                        st.session_state['show_clear_confirm'] = False
                        st.rerun()
    else:
                                             
        if status['status'] == 'running':
            st.success(f"🟢 {t('pipeline_running_with_interval')}")
        elif status['status'] == 'error':
            st.error(f"🔴 {t('pipeline_error')} - {status.get('error_message', t('unknown_error'))}")
    
                        
    st.markdown("---")
    st.subheader(t("live_statistics"))
    
                    
    from database import get_database as _get_db
    try:
        _db = _get_db()
        total_articles = _db.get_total_article_count()
        ai_count = _db.get_ai_article_count()
        class _Stats:
            total_articles_processed = total_articles
            ai_topics_detected = ai_count
        live_stats = _Stats()
    except Exception:
        class _Stats:
            total_articles_processed = 0
            ai_topics_detected = 0
        live_stats = _Stats()
    
                                
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(t('total_articles'), live_stats.total_articles_processed)
    
    with col2:
        st.metric(t('ai_articles'), live_stats.ai_topics_detected)
    
                                                                         
    if status['status'] == 'running':
        st.info(t('tracker_online'))
    else:
        st.info(f"⚪ {t('tracker_offline')}")
    
                                               
    st.markdown("---")
    st.header(f"{t('recent_articles')} ({t('live_updates')})")
    
                                       
    ai_articles = get_ai_articles_with_content()
    
    if ai_articles:
                                                 
        st.markdown("""
            <style>
            /* Reduce spacing in filter section */
            div[data-testid="stMarkdown"] h3 {
                margin-bottom: 0.3rem !important;
                margin-top: 0.3rem !important;
            }
            
            /* Reduce spacing for layout wrapper */
            .st-emotion-cache-18kf3ut {
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                margin-top: 0 !important;
                margin-bottom: 0 !important;
            }
            
            /* Reduce spacing between selectbox elements */
            div[data-testid="stSelectbox"] {
                margin-bottom: 20px !important;
                margin-top: -20px !important;
            }
            
            /* Reduce spacing for element containers with selectbox */
            .st-key-category_filter,
            .st-key-topic_filter {
                margin-top: 0 !important;
                margin-bottom: 0 !important;
                padding-top: 0 !important;
                padding-bottom: 0 !important;
            }
            
            /* Reduce spacing for columns */
            .stColumn {
                padding-top: 0 !important;
                padding-bottom: 0 !important;
            }
            
            /* Compact spacing for elements in article list area */
            [data-testid="stHorizontalBlock"] {
                gap: 0 !important;
            }
            
            /* Reduce spacing in vertical blocks */
            [data-testid="stVerticalBlock"] {
                gap: 0 !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
                                                                       
                                                    
        st.markdown('<div style="margin-top: -10px; margin-bottom: -20px;">', unsafe_allow_html=True)
        
        filter_col1, filter_col2, nav_col = st.columns([2, 2, 1])
        
        with filter_col1:
            st.markdown(f"**{t('category')}**")
                                          
            all_categories = sorted(list(set([article.get('domain_category', 'Unknown') for article in ai_articles])))
            categories_display = [t('all')] + [translate_domain_category(cat) for cat in all_categories]
            
            selected_category = st.selectbox(
                t('category'),
                options=categories_display,
                key='category_filter',
                label_visibility='collapsed'
            )
        
        with filter_col2:
            st.markdown(f"**{t('ai_topic')}**")
                                  
            all_topics = sorted(list(set([article.get('ai_topic', 'Unknown Topic') for article in ai_articles if article.get('ai_topic')])))
            topics_display = [t('all')] + [translate_ai_topic(topic) for topic in all_topics]
            
            selected_topic = st.selectbox(
                t('ai_topic'),
                options=topics_display,
                key='topic_filter',
                label_visibility='collapsed'
            )
        
                                                                                   
        filtered_articles = ai_articles.copy()
        
        if selected_category != t('all'):
                                                                     
            for orig_cat in all_categories:
                if translate_domain_category(orig_cat) == selected_category:
                    filtered_articles = [a for a in filtered_articles if a.get('domain_category') == orig_cat]
                    break
        
        if selected_topic != t('all'):
                                                                  
            for orig_topic in all_topics:
                if translate_ai_topic(orig_topic) == selected_topic:
                    filtered_articles = [a for a in filtered_articles if a.get('ai_topic') == orig_topic]
                    break
        
                                           
        ai_articles = filtered_articles
        
                                     
        if 'articles_page' not in st.session_state:
            st.session_state.articles_page = 1
                                          
        page_size = 10
        total = len(ai_articles)
        total_pages = (total + page_size - 1) // page_size

        page_index = st.session_state.articles_page
        start_idx = (page_index - 1) * page_size
        end_idx = min(start_idx + page_size, total)
        current_items = ai_articles[start_idx:end_idx]

                                                                                  
        with nav_col:
                                                            
            st.markdown("""
                <style>
                /* Align navigation buttons with selectbox */
                [data-testid="stHorizontalBlock"]:has([key="ai_prev_btn"]) {
                    margin-top: 1.5rem !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            bcol1, bcol2 = st.columns(2)
            with bcol1:
                if st.button(t("prev"), key="ai_prev_btn", disabled=(page_index <= 1), width='stretch'):
                    st.session_state.articles_page = max(1, page_index - 1)
                    st.rerun()
            with bcol2:
                if st.button(t("next"), key="ai_next_btn", disabled=(page_index >= total_pages), width='stretch'):
                    st.session_state.articles_page = min(total_pages, page_index + 1)
                    st.rerun()
        
                                        
        st.markdown('</div>', unsafe_allow_html=True)

                                                        
        st.markdown(
            """
            <style>
            /* Target the exact structure for article expander titles */
            [data-testid="stExpander"] summary [data-testid="stMarkdownContainer"],
            [data-testid="stExpander"] summary .st-emotion-cache-17c7e5f,
            [data-testid="stExpander"] summary [data-testid="stMarkdownContainer"] *,
            [data-testid="stExpander"] summary .st-emotion-cache-17c7e5f * {
                font-size: 19px !important;
            }
            </style>
            <script>
            function increaseArticleTitleFontSize() {
                // Target the specific markdown container in expander summaries
                const expanders = document.querySelectorAll('[data-testid="stExpander"]');
                
                expanders.forEach(expander => {
                    const summary = expander.querySelector('summary');
                    if (summary) {
                        // Find the markdown container in the summary
                        const markdownContainer = summary.querySelector('[data-testid="stMarkdownContainer"]');
                        if (markdownContainer) {
                            markdownContainer.style.setProperty('font-size', '18px', 'important');
                            
                            // Also apply to all children
                            const allElements = markdownContainer.querySelectorAll('*');
                            allElements.forEach(el => {
                                el.style.setProperty('font-size', '18px', 'important');
                            });
                        }
                        
                        // Also try by class name
                        const markdownByClass = summary.querySelector('.st-emotion-cache-17c7e5f');
                        if (markdownByClass) {
                            markdownByClass.style.setProperty('font-size', '18px', 'important');
                            const allElements = markdownByClass.querySelectorAll('*');
                            allElements.forEach(el => {
                                el.style.setProperty('font-size', '18px', 'important');
                            });
                        }
                    }
                });
            }
            
            // Run immediately
            setTimeout(increaseArticleTitleFontSize, 100);
            setTimeout(increaseArticleTitleFontSize, 500);
            setTimeout(increaseArticleTitleFontSize, 1000);
            
            // Run on DOM changes
            const observer = new MutationObserver(function() {
                increaseArticleTitleFontSize();
            });
            observer.observe(document.body, { childList: true, subtree: true });
            
            // Also run on interval
            setInterval(increaseArticleTitleFontSize, 300);
            </script>
            """,
            unsafe_allow_html=True
        )
        
                                          
        with st.container():
                                           
            for i, article in enumerate(current_items, start=start_idx + 1):
                                          
                title_display = f"{article['title'][:80]}..." if len(article['title']) > 80 else article['title']
                domain_display = article.get('domain', 'Unknown')
                expander_label = f"+ {title_display} ({domain_display})"
                
                with st.expander(expander_label, expanded=False):
                    
                                     
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**{t('title')}:** {article['title']}")
                        
                                                                    
                        current_lang = get_language()
                        if current_lang == 'da':
                            summary_text = article.get('summary_da', article.get('summary_en', 'No summary available'))
                        else:
                            summary_text = article.get('summary_en', article.get('summary_da', 'No summary available'))
                        
                        st.markdown(f"**{t('summary')}:** {summary_text}")
                        
                        if article['url']:
                            st.markdown(f"**URL:** [{article['domain']}]({article['url']})")
                        else:
                            st.markdown(f"**URL:** Not available")
                    
                    with col2:
                        st.markdown(f"**{t('domain')}:** {article['domain']}")
                        st.markdown(f"**{t('category')}:** {translate_domain_category(article['domain_category'])}")
                        st.markdown(f"**{t('ai_topic')}:** {translate_ai_topic(article.get('ai_topic', 'Unknown'))}")
                        st.markdown(f"**{t('language')}:** {article['language']}")
                        
                                      
                        if article['published_date']:
                            try:
                                                          
                                if 'T' in article['published_date']:
                                    pub_date = datetime.fromisoformat(article['published_date'].replace('Z', '+00:00'))
                                    st.markdown(f"**{t('published')}:** {pub_date.strftime('%Y-%m-%d %H:%M')}")
                                else:
                                    st.markdown(f"**{t('published')}:** {article['published_date']}")
                            except:
                                st.markdown(f"**{t('published')}:** {article['published_date']}")
                        else:
                            st.markdown(f"**{t('published')}:** Not available")
                        
                        if article['processed_at']:
                            try:
                                proc_date = datetime.fromisoformat(article['processed_at'].replace('Z', '+00:00'))
                                st.markdown(f"**{t('processed')}:** {proc_date.strftime('%Y-%m-%d %H:%M')}")
                            except:
                                st.markdown(f"**{t('processed')}:** {article['processed_at']}")

                                                    
    else:
        st.info(t('no_ai_articles_found'))
    
                    
    st.markdown("---")
    st.header(f"{t('ai_articles')} {t('statistics')}")
    
                                         
    st.subheader(t('topics_distribution'))
    
                        
    topics_data = get_ai_articles_by_topic(get_language())
    
    if topics_data:
                                     
        df_topics = pd.DataFrame([
            {t('ai_topics'): topic, t('number_of_articles'): count}
            for topic, count in topics_data.items()
        ])
        
                          
        fig_topics = px.bar(
            df_topics,
            x=t('ai_topics'),
            y=t('number_of_articles'),
            title=t('ai_articles_by_topic'),
            color=t('number_of_articles'),
            color_continuous_scale='Viridis'
        )
        
        fig_topics.update_layout(
            xaxis_title=t('ai_topics'),
            yaxis_title=t('number_of_articles'),
            showlegend=False,
            height=400
        )
        
                                                       
        if len(topics_data) > 3:
            fig_topics.update_xaxes(tickangle=45)
        
        st.plotly_chart(fig_topics, width='stretch')
    else:
        st.info(t('no_ai_topics_data'))
    
                                        
    st.subheader(t('articles_by_domain'))
    
                       
    category_data = get_ai_articles_by_category(get_language())
    
    if category_data:
                                     
        df_categories = pd.DataFrame([
            {t('categories'): category, t('number_of_articles'): count}
            for category, count in category_data.items()
        ])
        
                          
        fig_categories = px.bar(
            df_categories,
            x=t('categories'),
            y=t('number_of_articles'),
            title=t('ai_articles_by_category'),
            color=t('number_of_articles'),
            color_continuous_scale='Viridis'
        )
        
        fig_categories.update_layout(
            xaxis_title=t('categories'),
            yaxis_title=t('number_of_articles'),
            showlegend=False,
            height=400
        )
        
                                                           
        if len(category_data) > 5:
            fig_categories.update_xaxes(tickangle=45)
        
        st.plotly_chart(fig_categories, width='stretch')
    else:
        st.info(t('no_category_data'))
    
                                 
    st.subheader(f"{t('ai_trends')}")

                          
    time_period_options = ['hourly', 'daily', 'weekly', 'monthly', 'yearly']
    time_period_labels = [t(option) for option in time_period_options]
    
    time_period = st.selectbox(
        t('select_time_period'),
        options=time_period_options,
        format_func=lambda x: t(x),
        index=1,                    
        key="trend_time_period"
    )

                    
    trend_data = get_ai_articles_trend_data(time_period, get_language())

    if trend_data:
                            
        df_trend = pd.DataFrame([
            {t('time_period'): k, t('number_of_articles'): trend_data[k]}
            for k in trend_data.keys()
        ])
                    
        fig_trend = px.line(
            df_trend,
            x=t('time_period'),
            y=t('number_of_articles'),
            title=f"{t('ai_articles_trend')} ({t(time_period)})",
            markers=True
        )
        fig_trend.update_layout(
            xaxis_title=(
                t('hours') if time_period == 'hourly' else
                t('days_of_week') if time_period == 'daily' else
                t('weeks') if time_period == 'weekly' else
                t('months') if time_period == 'monthly' else
                t('years')
            ),
            yaxis_title=t('number_of_articles'),
            showlegend=False,
            height=400
        )
                                                                                
        fig_trend.update_xaxes(type='category')
        st.plotly_chart(fig_trend, width='stretch')
    else:
        st.info(f"No trend data available for {time_period} period yet. Run the pipeline to collect articles.")
        
                                                                   
    st.markdown("---")
    
                                                                                   
                                                 
    st.markdown('<div class="footer-section">', unsafe_allow_html=True)
    
                                                 
    st.markdown("""
        <style>
        /* Vertically center footer columns */
        .footer-section [data-testid="column"] > div[data-testid="stVerticalBlock"] {
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            min-height: 100px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    footer_col1, footer_col2, footer_col3 = st.columns([1, 1, 1])

                        
    with footer_col1:
        st.markdown(f"""
        <div style=\"color: #666; display: flex; align-items: center; gap: 18px;\">
            <div>
                <p style=\"margin: 0; font-size: 1.1em; font-weight: 500;\">🤖 {t('app_title')} | Center for AI @ DMJX</p>
                <p style=\"margin: 5px 0 0 0; font-size: 0.9em;\">{t('footer_description')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

                                             
    with footer_col2:
        if st.session_state.admin_logged_in:
            if st.button(f"👤 {t('logout')}", type="secondary", width='stretch'):
                st.session_state.admin_logged_in = False
                st.rerun()
        else:
            if st.button(f"🔐 {t('login')}", type="secondary", width='stretch'):
                st.session_state.show_login = True
                st.rerun()

                         
    with footer_col3:
                                                              
        current_lang = get_language()
        logo_filename = "images/DMJX_lockup_horisontal_DK_Hvid_RGB.png" if current_lang == 'da' else "images/DMJX_lockup_horisontal_UK_Hvid_RGB.png"
        dmjx_logo = base64.b64encode(open(logo_filename, "rb").read()).decode()
        st.markdown(f"""
        <div style=\"padding: 1rem; display: flex; align-items: center; justify-content: flex-end;\">
            <img src=\"data:image/png;base64,{dmjx_logo}\" width=\"310\" style=\"display: block; flex-shrink: 0;\">
        </div>
        """, unsafe_allow_html=True)
    
                                  
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
