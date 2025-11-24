#!/bin/bash

# TailorJob Services Stopper
# Usage: ./stop-services.sh

echo "🛑 Stopping TailorJob Services..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0
    else
        return 1
    fi
}

# Stop by PIDs if available
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill -9 $BACKEND_PID 2>/dev/null || true
    rm .backend.pid
fi

if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    echo "Stopping frontend (PID: $FRONTEND_PID)..."
    kill -9 $FRONTEND_PID 2>/dev/null || true
    rm .frontend.pid
fi

# Kill any remaining processes on ports
if check_port 8000; then
    echo "Cleaning up backend on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
fi

if check_port 8080; then
    echo "Cleaning up frontend on port 8080..."
    lsof -ti:8080 | xargs kill -9 2>/dev/null || true
fi

# Also kill any node processes running vite
pkill -f "vite" 2>/dev/null || true

# Kill any uvicorn processes
pkill -f "uvicorn" 2>/dev/null || true

sleep 2

# Verify services are stopped
echo ""
if ! check_port 8000 && ! check_port 8080; then
    echo -e "${GREEN}✓ All services stopped successfully${NC}"
else
    if check_port 8000; then
        echo -e "${RED}⚠ Backend still running on port 8000${NC}"
    fi
    if check_port 8080; then
        echo -e "${RED}⚠ Frontend still running on port 8080${NC}"
    fi
fi

echo ""
echo "To start services again: ./start-services.sh"