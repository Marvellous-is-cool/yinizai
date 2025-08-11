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
echo "  - Workers: 2"
echo "  - Log Level: ${LOG_LEVEL:-info}"
echo "  - Database: ${DB_HOST:-not-configured}"

# Health check before starting
echo "🔍 Running pre-flight checks..."
python -c "
import sys
print(f'Python version: {sys.version}')

# Test critical imports
try:
    import fastapi, uvicorn, sqlalchemy
    print('✅ Core dependencies OK')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)

# Test database connection
try:
    from app.models.database import engine
    with engine.connect() as conn:
        conn.execute(\"SELECT 1\")
    print('✅ Database connection OK')
except Exception as e:
    print(f'⚠️  Database connection warning: {e}')
    print('   Service will start but database features may be limited')
"

echo "🚀 Starting FastAPI server..."

# Start the FastAPI application with production settings
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-10000} \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --log-level ${LOG_LEVEL:-info} \
    --timeout-keep-alive 30 \
    --access-log \
    --no-use-colors \
    --loop asyncio
