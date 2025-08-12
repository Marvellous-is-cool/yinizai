FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    curl \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Copy requirements first for better layer caching
COPY ml_service/requirements.txt ./

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download only essential NLTK data (reduce memory usage)
RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('vader_lexicon', quiet=True)" && \
    python -m spacy download en_core_web_sm --quiet || echo "SpaCy model download failed, will use fallback"

# Copy the entire ml_service directory
COPY ml_service/ ./

# Create necessary directories
RUN mkdir -p trained_models data logs

# Set environment variables for memory optimization
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=10000
ENV WORKERS=1

# Optimize Python memory usage
ENV PYTHONHASHSEED=random
ENV MALLOC_MMAP_THRESHOLD_=131072
ENV MALLOC_TRIM_THRESHOLD_=131072
ENV MALLOC_MMAP_MAX_=65536

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=40s --retries=2 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Expose the port
EXPOSE $PORT

# Use the production start command
CMD ["bash", "start_production.sh"]
