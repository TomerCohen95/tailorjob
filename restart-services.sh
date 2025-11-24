#!/bin/bash

# TailorJob Services Restarter
# Usage: ./restart-services.sh

echo "🔄 Restarting TailorJob Services..."
echo ""

# Stop services
./stop-services.sh

echo ""
echo "⏳ Waiting 3 seconds..."
sleep 3

# Start services
./start-services.sh