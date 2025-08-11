#!/usr/bin/env bash
# Production Build Script for Render
# This runs when Render builds your service

set -o errexit  # exit on error

echo "🚀 Starting production build process..."

# Update system packages
echo "📦 Updating system packages..."
apt-get update -qq || true

# Install system dependencies for Python packages
echo "🔧 Installing system dependencies..."
apt-get install -y -qq gcc g++ python3-dev || true

# Install Python dependencies
echo "� Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r requirements.txt

# Download spaCy model
echo "🔤 Downloading spaCy English model..."
python -m spacy download en_core_web_sm

# Download NLTK data
echo "� Downloading NLTK data..."
python -c "
import nltk
import ssl
import os

# Create NLTK data directory
nltk_data_dir = os.path.expanduser('~/nltk_data')
os.makedirs(nltk_data_dir, exist_ok=True)

# Handle SSL certificate issues
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download required NLTK data
try:
    nltk.download('punkt', download_dir=nltk_data_dir, quiet=True)
    nltk.download('stopwords', download_dir=nltk_data_dir, quiet=True) 
    nltk.download('vader_lexicon', download_dir=nltk_data_dir, quiet=True)
    print('✅ NLTK data downloaded successfully')
except Exception as e:
    print(f'⚠️  NLTK download warning: {e}')
"

# Create necessary directories
echo "📁 Creating application directories..."
mkdir -p trained_models
mkdir -p logs

# Pre-compile Python files for faster startup
echo "⚡ Pre-compiling Python modules..."
python -m compileall app/ -q || true

# Verify installation
echo "🔍 Verifying installation..."
python -c "
import fastapi
import uvicorn
import spacy
import nltk
import sklearn
import pandas
import numpy
print('✅ All critical packages imported successfully')
"

echo "🎉 Production build completed successfully!"
