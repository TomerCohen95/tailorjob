#!/bin/bash

# Azure App Service startup script for FastAPI
# This uses Gunicorn with Uvicorn workers for production

# Default to port 8000 if not set by Azure
PORT="${PORT:-8000}"

# Start Gunicorn with Uvicorn workers
# - 4 workers (adjust based on your App Service plan)
# - Uvicorn worker class for async support
# - Bind to 0.0.0.0 to accept external connections
# - Timeout of 120s for long-running requests (CV parsing)
exec gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -