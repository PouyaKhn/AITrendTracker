#!/bin/bash

# Development Environment Setup Script
# This script creates/activates a virtual environment, installs requirements, and provides activation instructions

set -e  # Exit on any error

echo "🚀 Setting up development environment for News Scraping Service..."
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed or not in PATH"
    echo "Please install Python 3 before running this script"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ Found $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Verify virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Error: Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated: $VIRTUAL_ENV"

# Upgrade pip
echo "📋 Upgrading pip..."
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed successfully"
else
    echo "⚠️  Warning: requirements.txt not found in current directory"
fi

# Test imports
echo "🧪 Testing package imports..."
python3 -c "
try:
    import newsplease
    import schedule
    import tqdm
    import requests
    import boto3
    import dateutil
    import loguru
    import pytest
    import dotenv
    import transformers
    import torch
    print('✅ All packages imported successfully!')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📝 NEXT STEPS:"
echo "==============="
echo ""
echo "To activate the virtual environment in the future, run:"
echo ""
echo "  Linux/macOS (bash/zsh):"
echo "    source venv/bin/activate"
echo ""
echo "  Windows (Command Prompt):"
echo "    venv\\Scripts\\activate.bat"
echo ""
echo "  Windows (PowerShell):"
echo "    venv\\Scripts\\Activate.ps1"
echo ""
echo "  Fish Shell:"
echo "    source venv/bin/activate.fish"
echo ""
echo "  C Shell (csh/tcsh):"
echo "    source venv/bin/activate.csh"
echo ""
echo "You can verify the virtual environment is active by checking that"
echo "'(venv)' appears at the beginning of your command prompt, or by running:"
echo ""
echo "  echo \$VIRTUAL_ENV    # Linux/macOS"
echo "  echo %VIRTUAL_ENV%   # Windows Command Prompt"
echo "  echo \$env:VIRTUAL_ENV # Windows PowerShell"
echo ""
echo "🚀 You can now run the application:"
echo "   python main.py                  # Continuous mode"
echo "   python main.py --once          # Single batch test"
echo ""
