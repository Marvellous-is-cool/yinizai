#!/usr/bin/env bash
# Production Start Script for Render
set -o errexit

echo "🌟 Starting Yinizai ML Service in production mode..."

# Set production environment variables
export PYTHONPATH="${PYTHONPATH}:${PWD}"
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Print startup info
echo "📊 Service Configuration:"
echo "  - Environment: ${ENVIRONMENT:-production}"
echo "  - Port: ${PORT:-10000}"
echo "  - Workers: ${WORKERS:-1}"
echo "  - Log Level: ${LOG_LEVEL:-warning}"
echo "  - Database: ${DB_HOST:-not-configured}"

# Health check before starting
echo "🔍 Running pre-flight checks..."
python -c "
import sys
print(f'Python version: {sys.version}')

# Test critical imports
try:
    import fastapi
    print('✅ FastAPI OK')
    import uvicorn  
    print('✅ Uvicorn OK')
    import sqlalchemy
    print('✅ SQLAlchemy OK')
    import pandas
    print('✅ Pandas OK')
    import sklearn
    print('✅ Scikit-learn OK')
    print('✅ Core dependencies OK')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)

# Test database connection (optional - don't fail if DB not ready)
try:
    from app.models.database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ Database connection OK')
except Exception as e:
    print(f'⚠️  Database connection warning: {e}')
    print('   Service will start but database features may be limited')
"

echo "🚀 Starting FastAPI server..."

# Optimize for free tier (512MB limit)
# Use single worker to reduce memory footprint
WORKERS=${WORKERS:-1}
if [ "${RENDER}" = "true" ] && [ "${RENDER_SERVICE_TYPE}" = "web" ]; then
    WORKERS=1  # Force single worker on Render free tier
fi

echo "  - Memory optimization: Using ${WORKERS} worker(s) for free tier"

# Use Gunicorn with optimized settings for low memory
exec gunicorn app.main:app \
    --bind 0.0.0.0:${PORT:-10000} \
    --workers ${WORKERS} \
    --worker-class uvicorn.workers.UvicornWorker \
    --worker-connections 100 \
    --max-requests 100 \
    --max-requests-jitter 10 \
    --timeout 30 \
    --keep-alive 2 \
    --log-level ${LOG_LEVEL:-warning} \
    --access-logfile - \
    --error-logfile -
