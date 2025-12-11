# Persistent Log Storage Setup - COMPLETE ✅

## Overview
Successfully configured Loki with persistent Azure File Share storage. All logs are now saved permanently and survive container restarts.

## Setup Summary

### 1. Azure File Share Created
- **Storage Account**: `tailorjobmonitoring`
- **File Share Name**: `loki-data`
- **Quota**: 20 GB
- **Location**: East US
- **Cost**: ~$2.40/month ($0.12/GB/month)

### 2. Loki Container Deployed
- **Container Name**: `tailorjob-loki`
- **Image**: `grafana/loki:2.9.3`
- **URL**: `http://tailorjob-loki.eastus.azurecontainer.io:3100`
- **IP**: `52.146.70.94`
- **Resources**: 1 CPU, 1.5 GB RAM
- **Mount Point**: `/loki` → Azure File Share `loki-data`

### 3. Storage Structure
Files are being written to the Azure File Share in the following structure:
```
loki-data/
├── chunks/                    # Log data (actual log entries)
├── boltdb-shipper-active/    # Active index files
├── boltdb-shipper-cache/     # Index cache
├── wal/                       # Write-ahead log (crash recovery)
├── compactor/                 # Compaction metadata
└── rules/                     # Alerting rules
```

## Verification Steps

### Check Container Status
```bash
az container show \
  --resource-group tailorjob-rg \
  --name tailorjob-loki \
  --query "{state:instanceView.state,ip:ipAddress.ip,fqdn:ipAddress.fqdn}" -o json
```

### Check Loki Health
```bash
curl http://tailorjob-loki.eastus.azurecontainer.io:3100/ready
```

### View Container Logs
```bash
az container logs --resource-group tailorjob-rg --name tailorjob-loki 2>&1 | tail -50
```

### List Files in Azure File Share
```bash
az storage file list \
  --account-name tailorjobmonitoring \
  --share-name loki-data \
  --path "" -o table
```

### Check Disk Usage
```bash
az storage file list \
  --account-name tailorjobmonitoring \
  --share-name loki-data \
  --path "chunks" \
  --query "sum([].properties.contentLength)" -o tsv | awk '{printf "%.2f MB\n", $1/1024/1024}'
```

## Benefits of Persistent Storage

### ✅ Log Retention
- Logs survive container restarts
- No data loss during maintenance
- Full 15-day retention maintained

### ✅ Disaster Recovery
- Can restore logs from Azure File Share
- Write-ahead log prevents data corruption
- Multiple availability zones (Azure handles this)

### ✅ Operational Benefits
- Can safely restart Loki for updates
- Logs accumulate over time for historical analysis
- No need to re-ship old logs

## Cost Breakdown

| Component | Cost |
|-----------|------|
| Azure File Share (20 GB) | ~$2.40/month |
| Loki Container (1 CPU, 1.5 GB) | ~$30/month |
| Data Transfer (minimal) | ~$0.50/month |
| **Total** | **~$33/month** |

## Accessing Logs

### Via Grafana Explore
1. Go to Grafana: http://20.72.174.253:3000
2. Navigate to **Explore**
3. Select **Loki** datasource
4. Query examples:
   ```
   {job="tailorjob-api"}
   {job="tailorjob-api"} |= "error"
   {job="tailorjob-api"} |= "GET"
   ```

### Via Loki API
```bash
# Query recent logs
curl -G "http://tailorjob-loki.eastus.azurecontainer.io:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="tailorjob-api"}' \
  --data-urlencode "start=$(date -u -v-1H '+%s')000000000" \
  --data-urlencode "end=$(date -u '+%s')000000000"
```

### Via Azure Portal
1. Go to Azure Portal → Storage Accounts → tailorjobmonitoring
2. Navigate to File Shares → loki-data
3. Browse directories and download files if needed

## Monitoring the Storage

### Check Space Usage
```bash
# Total size of all files
az storage file list \
  --account-name tailorjobmonitoring \
  --share-name loki-data \
  --path "" \
  --query "sum([].properties.contentLength)" -o tsv | \
  awk '{printf "Total: %.2f GB / 20 GB (%.1f%% used)\n", $1/1024/1024/1024, ($1/1024/1024/1024/20)*100}'
```

### Alerts
Set up alerts if storage exceeds 80% (16 GB):
```bash
# Check if we need more space
USAGE=$(az storage file list --account-name tailorjobmonitoring --share-name loki-data --path "" --query "sum([].properties.contentLength)" -o tsv)
if [ $USAGE -gt 17179869184 ]; then
  echo "⚠️  Storage usage above 80%, consider increasing quota"
fi
```

## Maintenance

### Increase Storage Quota
If you need more space:
```bash
az storage share update \
  --name loki-data \
  --account-name tailorjobmonitoring \
  --quota 50  # Increase to 50 GB
```

### Restart Loki Container
Safe to restart now that storage is persistent:
```bash
az container restart --resource-group tailorjob-rg --name tailorjob-loki
```

### Backup Logs
Optional: Download entire file share for backup:
```bash
mkdir -p loki-backup
az storage file download-batch \
  --destination loki-backup/ \
  --source loki-data \
  --account-name tailorjobmonitoring
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    TailorJob Application                      │
│  https://tailorjob-api.azurewebsites.net                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Logs via HTTP (LokiHandler)
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Loki Container (ACI)                            │
│  http://tailorjob-loki.eastus.azurecontainer.io:3100        │
│                                                               │
│  ┌────────────┐         ┌─────────────┐                     │
│  │  Ingester  │────────▶│ Write-Ahead │                     │
│  └────────────┘         │     Log     │                     │
│        │                └─────────────┘                     │
│        │                      │                              │
│        ▼                      ▼                              │
│  ┌────────────────────────────────────┐                     │
│  │   Azure File Share (Persistent)    │                     │
│  │                                     │                     │
│  │  /loki/chunks/    ← Log Data       │                     │
│  │  /loki/index/     ← Index Files    │                     │
│  │  /loki/wal/       ← WAL            │                     │
│  └────────────────────────────────────┘                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Query logs
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   Grafana (ACI)                              │
│  http://20.72.174.253:3000                                   │
│  - Explore logs in real-time                                │
│  - Build dashboards                                          │
│  - Set up alerts                                             │
└─────────────────────────────────────────────────────────────┘
```

## What's Stored?

### Application Logs
- ✅ All HTTP requests (method, path, status, duration)
- ✅ Error messages and stack traces
- ✅ CV parsing operations
- ✅ Job matching operations
- ✅ Authentication events
- ✅ PayPal webhook events
- ✅ Background worker activity

### Log Format
```json
{
  "timestamp": "2025-12-11T10:17:36Z",
  "level": "INFO",
  "logger": "uvicorn.access",
  "message": "GET /api/health - Status: 200 - Duration: 0.003s",
  "labels": {
    "job": "tailorjob-api",
    "environment": "production",
    "service": "fastapi"
  }
}
```

## Success Indicators

✅ **Storage Created**: Azure File Share `loki-data` with 20 GB quota
✅ **Container Running**: Loki container active at tailorjob-loki.eastus.azurecontainer.io
✅ **Files Being Written**: 6 directories created (chunks, index, wal, etc.)
✅ **Health Check Passing**: Loki `/ready` endpoint returns 200
✅ **Persistence Verified**: Files visible in Azure Storage Explorer
✅ **Grafana Connected**: Can query logs via Grafana Explore

## Next Steps

1. ✅ **Test Log Queries** in Grafana Explore
2. ⏳ **Monitor for 24 hours** to ensure stability
3. ⏳ **Set up retention policy** if 15 days is too long/short
4. ⏳ **Create log-based dashboards** in Grafana
5. ⏳ **Set up log-based alerts** for errors

## Troubleshooting

### No logs appearing in Loki?
```bash
# Check backend is sending logs
az webapp log tail --name tailorjob-api --resource-group tailorjob-rg

# Check LOKI_URL is set
az webapp config appsettings list --name tailorjob-api --resource-group tailorjob-rg --query "[?name=='LOKI_URL'].value" -o tsv

# Check Loki is receiving data
curl "http://tailorjob-loki.eastus.azurecontainer.io:3100/loki/api/v1/label/__name__/values"
```

### Container keeps restarting?
```bash
# Check container logs for errors
az container logs --resource-group tailorjob-rg --name tailorjob-loki

# Check storage account key is correct
az storage account keys list --resource-group tailorjob-rg --account-name tailorjobmonitoring
```

### Storage full?
```bash
# Check current usage
az storage share show --name loki-data --account-name tailorjobmonitoring --query "properties.quota"

# Increase quota
az storage share update --name loki-data --account-name tailorjobmonitoring --quota 50
```

## Comparison: Before vs After

| Feature | Before (Ephemeral) | After (Persistent) |
|---------|-------------------|-------------------|
| **Storage Location** | Container filesystem | Azure File Share |
| **Survives Restart** | ❌ No | ✅ Yes |
| **Retention** | Until restart | 15 days |
| **Data Loss Risk** | High | Low |
| **Historical Analysis** | Limited | Full |
| **Cost** | $30/month | $33/month |

## Conclusion

✅ **Persistent log storage is now active!**

All system logs are being written to Azure File Share and will survive container restarts. You can explore what happened in your system by:

1. **Real-time**: Use Grafana Explore to search logs
2. **Historical**: Query Loki API for past 15 days
3. **Backup**: Download files from Azure Storage if needed

The extra $3/month provides peace of mind and full operational visibility into your production system.