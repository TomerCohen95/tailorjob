# Azure App Service Restart Required

## Problem
GitHub Actions deployment completed successfully, but the `/metrics` endpoint returns 404.
The monitoring code exists in the deployed commit but Azure hasn't picked it up.

## Deployed Commit
- **Commit**: `172ab8e` - "trigger: Force backend redeployment with monitoring"
- **Includes**: Monitoring infrastructure (commit `13428c4`)
- **GitHub Actions**: ✅ Completed successfully at 2025-12-09 12:17:33 UTC
- **Status**: `/metrics` endpoint still returns 404

## Root Cause
Azure App Service may have:
1. Cached the old deployment
2. Failed to restart properly after deployment
3. Deployment succeeded but service didn't reload

## Solution: Manual Azure Restart

### Option 1: Azure Portal (Easiest)
1. Go to https://portal.azure.com
2. Navigate to **App Services** → **tailorjob-api**
3. Click **Restart** in the top menu
4. Wait 1-2 minutes for restart to complete
5. Test: `curl https://tailorjob-api.azurewebsites.net/metrics`

### Option 2: Azure CLI
```bash
# Login to Azure
az login

# Restart the app service
az webapp restart \
  --name tailorjob-api \
  --resource-group tailorjob-rg

# Wait 1 minute
sleep 60

# Test the endpoint
curl -s https://tailorjob-api.azurewebsites.net/metrics | head -20
```

### Option 3: Force Stop and Start
```bash
# Stop the app
az webapp stop \
  --name tailorjob-api \
  --resource-group tailorjob-rg

# Wait 30 seconds
sleep 30

# Start the app
az webapp start \
  --name tailorjob-api \
  --resource-group tailorjob-rg

# Wait 1 minute for startup
sleep 60

# Test
curl https://tailorjob-api.azurewebsites.net/metrics
```

## Verification Steps

### 1. Check Deployment Logs
```bash
az webapp log tail \
  --name tailorjob-api \
  --resource-group tailorjob-rg
```

Look for:
- ✅ `Prometheus metrics enabled at /metrics`
- ✅ `Starting TailorJob API...`
- ❌ Any ImportError for prometheus packages

### 2. Test Endpoint
```bash
# Should return HTTP 200
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  https://tailorjob-api.azurewebsites.net/metrics

# Should show Prometheus metrics
curl https://tailorjob-api.azurewebsites.net/metrics | head -30
```

Expected output:
```
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 123.0
...
```

### 3. Check App Settings
```bash
az webapp config appsettings list \
  --name tailorjob-api \
  --resource-group tailorjob-rg \
  --output table
```

Ensure these exist:
- `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
- `WEBSITE_HTTPLOGGING_RETENTION_DAYS=7`

## If Still Not Working

### Check Deployed Files
```bash
# Download deployment package
az webapp deployment source show \
  --name tailorjob-api \
  --resource-group tailorjob-rg
```

### Manual Redeploy
If restart doesn't work, trigger another deployment:
```bash
cd /Users/tomercohen/toco/tailorjob

# Make a tiny change to force redeploy
echo "# Force redeploy" >> backend/README.md
git add backend/README.md
git commit -m "fix: Force Azure App Service to redeploy with monitoring"
git push origin main

# Wait 5 minutes for deployment
sleep 300

# Test
curl https://tailorjob-api.azurewebsites.net/metrics
```

## Success Indicators

When working correctly, you should see:
1. **HTTP 200** from `/metrics` endpoint
2. **Prometheus metrics** in plain text format
3. **Grafana Dashboard** showing data
4. **Discord alerts** when thresholds exceeded

## Monitoring URLs

Once working:
- **Metrics**: https://tailorjob-api.azurewebsites.net/metrics
- **Prometheus**: http://tailorjob-prometheus-1765272255.eastus.azurecontainer.io:9090
- **Grafana**: http://tailorjob-grafana-1765272324.eastus.azurecontainer.io:3000
- **Alertmanager**: http://tailorjob-alertmanager-1765272394.eastus.azurecontainer.io:9093

## Next Steps After Restart

Once `/metrics` is live:
1. Verify Prometheus is scraping: http://tailorjob-prometheus-1765272255.eastus.azurecontainer.io:9090/targets
2. Configure Grafana dashboard (login: admin/admin)
3. Test alerts by triggering a condition
4. Review [`PRODUCTION_SECURITY_AUDIT.md`](PRODUCTION_SECURITY_AUDIT.md) for critical fixes

## Contact
If issues persist after restart, check:
- GitHub Actions logs: https://github.com/TomerCohen95/tailorjob/actions
- Azure App Service logs in portal
- Deployment logs in Deployment Center