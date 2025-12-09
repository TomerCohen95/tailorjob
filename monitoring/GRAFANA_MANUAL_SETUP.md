# Grafana Manual Setup Guide

## Access Information

**Grafana URL**: http://20.72.174.253:3000
**Prometheus URL**: http://tailorjob-prometheus.eastus.azurecontainer.io:9090
**Alertmanager URL**: http://48.195.182.9:9093

## Step 1: Login to Grafana

1. Navigate to http://20.72.174.253:3000
2. Login with your credentials (password has been changed from default)

## Step 2: Add Prometheus Data Source

1. Click the menu icon (☰) in the top left
2. Go to **Connections** → **Data sources**
3. Click **Add data source**
4. Select **Prometheus**
5. Configure:
   - **Name**: Prometheus
   - **URL**: `http://tailorjob-prometheus.eastus.azurecontainer.io:9090`
   - **Access**: Server (default)
6. Click **Save & Test**

## Step 3: Import Dashboard

### Option A: Import via UI
1. Click the menu icon (☰) → **Dashboards**
2. Click **New** → **Import**
3. Click **Upload JSON file**
4. Select `monitoring/grafana-dashboards/tailorjob-dashboard.json`
5. Select **Prometheus** as the data source
6. Click **Import**

### Option B: Import via API (if you know the API key)
```bash
curl -X POST http://20.72.174.253:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d @monitoring/grafana-dashboards/tailorjob-dashboard.json
```

## Step 4: Verify Metrics

1. Open the imported dashboard
2. You should see:
   - **API Requests**: Rate of requests per second
   - **Error Rates**: 4xx and 5xx error percentages
   - **Response Times**: P50, P95, P99 latencies
   - **Resource Usage**: CPU and memory if available

## Step 5: Configure Alerting (Optional)

1. Click the menu icon (☰) → **Alerting** → **Contact points**
2. Add Discord webhook:
   - **Name**: Discord
   - **Type**: Webhook
   - **URL**: Your Discord webhook URL
3. Go to **Notification policies**
4. Configure alert routing to Discord

## Troubleshooting

### Data Source Connection Failed
- Verify Prometheus is running: `curl http://tailorjob-prometheus.eastus.azurecontainer.io:9090/-/healthy`
- Check Prometheus targets: `curl http://tailorjob-prometheus.eastus.azurecontainer.io:9090/api/v1/targets`

### No Data in Dashboard
- Wait 1-2 minutes for initial scrape
- Generate some API traffic: visit https://tailorjob-api.azurewebsites.net/api/health
- Check if metrics endpoint is working: `curl https://tailorjob-api.azurewebsites.net/metrics`

### Dashboard Not Showing
- Verify time range is set to "Last 15 minutes" or "Last 1 hour"
- Check that Prometheus data source is selected
- Refresh the dashboard

## Current Monitoring Stack Status

✅ **Prometheus**: Running and scraping TailorJob API successfully
- FQDN: tailorjob-prometheus.eastus.azurecontainer.io
- Status: Target "tailorjob-api" is UP
- Scrape interval: 15 seconds

✅ **Grafana**: Running
- FQDN: 20.72.174.253:3000
- Status: Accessible
- Note: Default password has been changed

✅ **Alertmanager**: Running
- FQDN: 48.195.182.9:9093
- Status: Accessible
- Configuration: Alerts route to Discord

✅ **Backend /metrics**: Working
- URL: https://tailorjob-api.azurewebsites.net/metrics
- Status: Returns Prometheus metrics successfully

## Next Steps

1. Login to Grafana and add Prometheus data source
2. Import the TailorJob dashboard
3. Generate some API traffic to see metrics populate
4. Set up alerting rules in Grafana
5. Change Grafana admin password to a secure value