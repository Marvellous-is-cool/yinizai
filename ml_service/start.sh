#!/bin/bash

# Yinizai ML Service Startup Script

echo "🚀 Starting Yinizai ML Analysis Service..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Download spaCy model
echo "🔤 Downloading spaCy English model..."
python -m spacy download en_core_web_sm

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.example .env
    echo "⚠️ Please edit .env file with your database credentials before proceeding!"
    echo "Press Enter to continue after updating .env file..."
    read
fi

# Create directories
mkdir -p trained_models
mkdir -p data

# Ask user if they want to set up sample data
echo "📊 Do you want to set up sample data? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "🗂️ Setting up sample database..."
    python setup_database.py
fi

# Start the service
echo "🌟 Starting ML service..."
echo "Service will be available at: http://localhost:8000"
echo "API documentation at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the service"

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
