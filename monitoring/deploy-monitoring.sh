#!/bin/bash

# TailorJob Monitoring Stack Deployment Script
# Deploys Prometheus, Grafana, Alertmanager, and Discord forwarder

set -e

echo "🚀 TailorJob Monitoring Stack Deployment"
echo "=========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Load environment variables
source .env

# Validate required variables
if [ -z "$DISCORD_WEBHOOK_URL" ]; then
    echo "❌ Error: DISCORD_WEBHOOK_URL not set in .env"
    exit 1
fi

if [ -z "$GRAFANA_ADMIN_PASSWORD" ]; then
    echo "❌ Error: GRAFANA_ADMIN_PASSWORD not set in .env"
    exit 1
fi

echo "✅ Environment variables validated"
echo ""

# Update alertmanager config with Discord webhook
echo "📝 Configuring Alertmanager with Discord webhook..."
sed "s|DISCORD_WEBHOOK_URL_PLACEHOLDER|http://discord-forwarder:5000/webhook|g" alertmanager.yml > alertmanager-configured.yml
mv alertmanager-configured.yml alertmanager.yml
echo "✅ Alertmanager configured"
echo ""

# Build and start containers
echo "🐳 Starting Docker containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo ""
echo "🏥 Checking service health..."

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo "✅ Prometheus is healthy"
else
    echo "❌ Prometheus is not responding"
fi

# Check Grafana
if curl -s http://localhost:3000/api/health > /dev/null; then
    echo "✅ Grafana is healthy"
else
    echo "❌ Grafana is not responding"
fi

# Check Alertmanager
if curl -s http://localhost:9093/-/healthy > /dev/null; then
    echo "✅ Alertmanager is healthy"
else
    echo "❌ Alertmanager is not responding"
fi

# Check Discord Forwarder
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ Discord forwarder is healthy"
else
    echo "❌ Discord forwarder is not responding"
fi

echo ""
echo "✨ Deployment complete!"
echo ""
echo "📊 Access your monitoring stack:"
echo "  Grafana:       http://localhost:3000"
echo "  Prometheus:    http://localhost:9090"
echo "  Alertmanager:  http://localhost:9093"
echo ""
echo "🔐 Grafana credentials:"
echo "  Username: ${GRAFANA_ADMIN_USER:-admin}"
echo "  Password: ${GRAFANA_ADMIN_PASSWORD}"
echo ""
echo "📝 Next steps:"
echo "  1. Open Grafana and login"
echo "  2. Import dashboard from grafana-dashboards/tailorjob-dashboard.json"
echo "  3. Test alerts by triggering /health endpoint failure"
echo "  4. Check Discord for alert notifications"
echo ""
echo "🔧 Management commands:"
echo "  View logs:    docker-compose logs -f"
echo "  Stop:         docker-compose down"
echo "  Restart:      docker-compose restart"
echo "  Update:       docker-compose pull && docker-compose up -d"
echo ""