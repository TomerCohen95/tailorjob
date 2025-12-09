# Azure Deployment Quickstart - TailorJob Monitoring

Deploy the full monitoring stack to Azure Container Instances in ~5 minutes.

## Prerequisites

1. **Azure CLI installed**
   ```bash
   # macOS
   brew install azure-cli
   
   # Or download from: https://aka.ms/InstallAzureCLIDeb
   ```

2. **Logged in to Azure**
   ```bash
   az login
   ```

3. **Discord webhook created**
   - Go to Discord Server Settings → Integrations → Webhooks
   - Create New Webhook
   - Copy the webhook URL

## Quick Deploy (5 minutes)

### Step 1: Configure Environment (1 min)

```bash
cd monitoring
cp .env.example .env
nano .env  # or use your preferred editor
```

Set these values:
```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN
GRAFANA_ADMIN_PASSWORD=your-strong-password-here
```

### Step 2: Deploy to Azure (3 min)

```bash
./deploy-to-azure.sh
```

This will:
- ✅ Create Azure Storage for persistent data
- ✅ Deploy Prometheus (metrics database)
- ✅ Deploy Grafana (dashboards)
- ✅ Deploy Alertmanager (alert routing)
- ✅ Configure auto-restart on failures
- ✅ Save access URLs to `deployment-urls.txt`

### Step 3: Access Grafana (1 min)

The script will output:
```
🔹 Grafana Dashboard:
   URL:      http://tailorjob-grafana-XXXXX.eastus.azurecontainer.io:3000
   Username: admin
   Password: (from your .env file)
```

Open the URL and login!

## Configure Grafana (5 minutes)

### Add Prometheus Data Source

1. Login to Grafana
2. Go to **Configuration** (⚙️) → **Data Sources**
3. Click **Add data source**
4. Choose **Prometheus**
5. Set URL: `http://tailorjob-prometheus-XXXXX.eastus.azurecontainer.io:9090`
   - (Use the URL from deployment output)
6. Click **Save & Test**

### Import Dashboard

1. Click **+** → **Import**
2. Click **Upload JSON file**
3. Select `grafana-dashboards/tailorjob-dashboard.json`
4. Choose Prometheus data source
5. Click **Import**

Done! You now have a full monitoring dashboard.

## Update Backend to Send Metrics

Your backend needs to point to the deployed Prometheus instance.

### Update prometheus.yml

Edit `monitoring/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'tailorjob-api'
    static_configs:
      - targets: ['YOUR_BACKEND_URL:8000']  # Change this!
```

Replace `YOUR_BACKEND_URL` with your actual backend URL (e.g., `tailorjob-api.azurewebsites.net`)

### Restart Prometheus

```bash
az container restart --resource-group tailorjob-rg --name tailorjob-prometheus
```

## Verify Everything Works

1. **Check Prometheus is scraping**
   - Open Prometheus: `http://tailorjob-prometheus-XXXXX.eastus.azurecontainer.io:9090`
   - Go to Status → Targets
   - Should show your API endpoint as UP

2. **Check Grafana shows data**
   - Open Grafana dashboard
   - Should see request rate, latency graphs
   - If flat, wait 1-2 minutes for first scrape

3. **Test Discord alerts**
   ```bash
   # Trigger a test alert by hitting a non-existent endpoint repeatedly
   for i in {1..50}; do curl http://your-api.com/api/test-404; done
   ```
   
   Should get Discord notification: "⚠️ High Error Rate on TailorJob API"

## Cost Breakdown

**Total: ~$31/month** (from your $150 Azure credits)

- Prometheus container: ~$10/month (1 CPU, 1GB RAM)
- Grafana container: ~$10/month (1 CPU, 1GB RAM)  
- Alertmanager container: ~$5/month (0.5 CPU, 0.5GB RAM)
- Azure Storage: ~$1/month
- Data transfer: ~$5/month

## Management Commands

### View Logs
```bash
# Grafana logs
az container logs --resource-group tailorjob-rg --name tailorjob-grafana --tail 100

# Prometheus logs
az container logs --resource-group tailorjob-rg --name tailorjob-prometheus --tail 100

# Alertmanager logs
az container logs --resource-group tailorjob-rg --name tailorjob-alertmanager --tail 100
```

### Restart Containers
```bash
az container restart --resource-group tailorjob-rg --name tailorjob-grafana
az container restart --resource-group tailorjob-rg --name tailorjob-prometheus
az container restart --resource-group tailorjob-rg --name tailorjob-alertmanager
```

### Check Status
```bash
az container show --resource-group tailorjob-rg --name tailorjob-grafana --query instanceView.state
```

### Update Configuration

1. Edit the config file (e.g., `prometheus.yml`)
2. Upload to Azure Storage:
   ```bash
   az storage file upload \
     --account-name tailorjobmonitoring \
     --share-name prometheus-data \
     --source prometheus.yml \
     --path prometheus.yml
   ```
3. Restart container:
   ```bash
   az container restart --resource-group tailorjob-rg --name tailorjob-prometheus
   ```

### Delete Everything
```bash
# Delete all monitoring containers
az container delete --resource-group tailorjob-rg --name tailorjob-prometheus --yes
az container delete --resource-group tailorjob-rg --name tailorjob-grafana --yes
az container delete --resource-group tailorjob-rg --name tailorjob-alertmanager --yes

# Delete storage (optional - this deletes your data!)
az storage account delete --name tailorjobmonitoring --resource-group tailorjob-rg --yes
```

## Troubleshooting

### Container won't start
```bash
# Check logs
az container logs --resource-group tailorjob-rg --name tailorjob-grafana

# Check events
az container show --resource-group tailorjob-rg --name tailorjob-grafana --query instanceView
```

### No data in Grafana
1. Check Prometheus targets: Should show your API as UP
2. Verify backend has `/metrics` endpoint: `curl http://your-api/metrics`
3. Check if backend imported `setup_metrics()` in main.py
4. Verify firewall allows Prometheus to reach your API

### Discord alerts not working
1. Check Alertmanager is running: `az container show --name tailorjob-alertmanager`
2. Verify Discord webhook URL in `.env`
3. Check Alertmanager logs for errors
4. Test webhook manually:
   ```bash
   curl -X POST $DISCORD_WEBHOOK_URL \
     -H "Content-Type: application/json" \
     -d '{"content": "Test from TailorJob"}'
   ```

### High costs
- Monitoring should cost ~$31/month
- If higher, check:
  - Are containers properly sized? (Don't need more than 1 CPU)
  - Is data transfer unusually high? (Should be <100GB/month)
  - Are there failed/restarting containers? (Check logs)

## Next Steps

Now that monitoring is deployed:

1. ✅ Monitor your app for 24-48 hours
2. ✅ Adjust alert thresholds if getting too many/few alerts
3. ✅ Move to security fixes from `PRODUCTION_SECURITY_AUDIT.md`
4. ✅ Prepare for production launch

## Support

- **Prometheus docs**: https://prometheus.io/docs/
- **Grafana docs**: https://grafana.com/docs/
- **Azure Container Instances**: https://docs.microsoft.com/azure/container-instances/

---

**Deployment created**: Auto-generated by deploy-to-azure.sh
**Resource Group**: tailorjob-rg
**Location**: eastus