#!/bin/bash
# Quick script to restart Prometheus on Azure Container Instances

echo "=== Restarting Prometheus on Azure ==="
echo ""

# Delete old container if it exists (ignore errors)
echo "1. Cleaning up old Prometheus container..."
az container delete --resource-group tailorjob-rg --name tailorjob-prometheus --yes 2>/dev/null
echo "   Done"
echo ""

# Create new Prometheus container
echo "2. Creating new Prometheus container..."
az container create \
  --resource-group tailorjob-rg \
  --name tailorjob-prometheus \
  --image prom/prometheus:latest \
  --os-type Linux \
  --dns-name-label tailorjob-prometheus \
  --ports 9090 \
  --cpu 1 \
  --memory 1 \
  --location eastus \
  --ip-address Public \
  --environment-variables \
    PROMETHEUS_RETENTION_TIME=15d \
  --command-line "/bin/prometheus --config.file=/etc/prometheus/prometheus.yml --storage.tsdb.path=/prometheus --storage.tsdb.retention.time=15d --web.console.libraries=/usr/share/prometheus/console_libraries --web.console.templates=/usr/share/prometheus/consoles" \
  --query "{fqdn:ipAddress.fqdn,ip:ipAddress.ip,state:provisioningState}" \
  -o json

echo ""
echo "3. Prometheus restarted!"
echo ""
echo "Access Prometheus at: http://tailorjob-prometheus.eastus.azurecontainer.io:9090"
echo ""
echo "Note: It may take 30-60 seconds for Prometheus to fully start"
echo ""