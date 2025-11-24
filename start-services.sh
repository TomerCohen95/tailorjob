#!/bin/bash

# TailorJob Services Starter
# Usage: ./start-services.sh

set -e

echo "🚀 Starting TailorJob Services..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
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

# Kill processes on ports if running
echo "🧹 Cleaning up existing processes..."
if check_port 8000; then
    echo "  Stopping backend on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
fi

if check_port 8080; then
    echo "  Stopping frontend on port 8080..."
    lsof -ti:8080 | xargs kill -9 2>/dev/null || true
fi

sleep 2

# Create logs directory
mkdir -p logs

# Start Backend
echo ""
echo -e "${BLUE}📦 Starting Backend (FastAPI)...${NC}"
cd backend
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

source venv/bin/activate
nohup uvicorn app.main:app --reload --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

sleep 3

if check_port 8000; then
    echo -e "${GREEN}✓ Backend started on http://localhost:8000${NC}"
    echo "  PID: $BACKEND_PID"
    echo "  Logs: tail -f logs/backend.log"
else
    echo "❌ Failed to start backend"
    exit 1
fi

# Start Frontend
echo ""
echo -e "${BLUE}🎨 Starting Frontend (Vite)...${NC}"
nohup npm run dev > logs/frontend.log 2>&1 &
FRONTEND_PID=$!

sleep 3

if check_port 8080; then
    echo -e "${GREEN}✓ Frontend started on http://localhost:8080${NC}"
    echo "  PID: $FRONTEND_PID"
    echo "  Logs: tail -f logs/frontend.log"
else
    echo "❌ Failed to start frontend"
    exit 1
fi

# Save PIDs for stop script
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

echo ""
echo -e "${GREEN}🎉 All services started successfully!${NC}"
echo ""
echo "📊 Service Status:"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:8080"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "📝 View logs:"
echo "  Backend:  tail -f logs/backend.log"
echo "  Frontend: tail -f logs/frontend.log"
echo ""
echo "🛑 To stop services: ./stop-services.sh"