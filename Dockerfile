FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including build tools for cryptography
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY ml_service/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download required NLTK data and spaCy model
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')" && \
    python -m spacy download en_core_web_sm

# Copy the entire ml_service directory
COPY ml_service/ ./

# Create necessary directories
RUN mkdir -p trained_models data logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Expose the port
EXPOSE $PORT

# Use the production start command
CMD ["bash", "start_production.sh"]
