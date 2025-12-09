# Pre-Launch Monitoring Plan - TailorJob

**Budget:** $150/mo Azure credits (mostly unused)  
**Goal:** Launch-ready monitoring with zero additional cost  
**Timeline:** 2-3 days to implement

---

## Executive Summary

**Answer to your questions:**

1. **Azure-hosted Grafana?** ✅ YES - Perfect use of your credits
2. **Is Sentry needed?** ⚠️ YES for frontend errors, but Azure Application Insights can replace it for backend
3. **Alert delivery?** Email + SMS (free) + Slack webhook (free)

**Total Cost:** $0 (uses existing Azure credits)

---

## 🎯 MUST HAVE Before Launch (Priority 1)

These are **non-negotiable** - you need these running before the first customer signs up.

### 1. Site Uptime Monitoring ⭐ CRITICAL

**What:** Is the site up or down?  
**Why:** If site is down, you're losing customers and money  
**Tool:** Azure Application Insights Availability Tests (FREE in Azure)

**Setup (15 minutes):**

```bash
# Create availability test in Azure Portal
az monitor app-insights component create \
  --app tailorjob-app-insights \
  --location eastus \
  --resource-group tailorjob-rg

# Add web test
az monitor app-insights web-test create \
  --resource-group tailorjob-rg \
  --name "Frontend Uptime" \
  --location eastus \
  --web-test-name "https://tailorjob.vercel.app" \
  --web-test-kind ping \
  --frequency 300 \
  --timeout 30 \
  --enabled true

# Add API health check test
az monitor app-insights web-test create \
  --resource-group tailorjob-rg \
  --name "API Health" \
  --location eastus \
  --web-test-name "https://tailorjob-api.azurewebsites.net/health" \
  --web-test-kind ping \
  --frequency 300 \
  --timeout 30 \
  --enabled true
```

**Alerts:**
- Site down for 2+ minutes → **SMS + Email**
- API down for 2+ minutes → **SMS + Email**
- SSL cert expiring in < 7 days → **Email**

---

### 2. Error Tracking ⭐ CRITICAL

**What:** Catch crashes and errors before users report them  
**Why:** Bugs kill conversions and trust

#### Backend Errors (Azure Application Insights)

**Setup (20 minutes):**

```python
# backend/requirements.txt
opencensus-ext-azure==1.1.9
opencensus-ext-fastapi==0.1.1

# backend/app/main.py
from opencensus.ext.azure import metrics_exporter
from opencensus.ext.fastapi import FastAPIMiddleware
from opencensus.stats import stats as stats_module

# Get connection string from Azure Portal
APPINSIGHTS_CONNECTION_STRING = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')

if APPINSIGHTS_CONNECTION_STRING:
    # Add middleware for automatic tracking
    app.add_middleware(
        FastAPIMiddleware,
        connection_string=APPINSIGHTS_CONNECTION_STRING
    )
    
    # Track custom metrics
    exporter = metrics_exporter.new_metrics_exporter(
        connection_string=APPINSIGHTS_CONNECTION_STRING
    )
    
    print("✅ Application Insights enabled")
else:
    print("⚠️ Application Insights not configured")

# Track errors manually
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # This will be auto-captured by App Insights
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

**Environment variable:**
```bash
# Add to Azure App Service configuration
APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=xxx;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/"
```

#### Frontend Errors (Sentry Free Tier)

**Why Sentry for frontend?** Azure App Insights doesn't track frontend well. Sentry free tier (5k errors/mo) is perfect for launch.

**Setup (10 minutes):**

```bash
npm install @sentry/react
```

```typescript
// src/main.tsx
import * as Sentry from '@sentry/react';

if (import.meta.env.PROD) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: 'production',
    integrations: [
      new Sentry.BrowserTracing(),
    ],
    tracesSampleRate: 0.1,  // 10% of transactions
    beforeSend(event) {
      // Don't send errors in development
      if (window.location.hostname === 'localhost') {
        return null;
      }
      return event;
    },
  });
}
```

**Alerts:**
- New error type → **Email immediately**
- Error rate > 10 errors/hour → **Email**
- Specific error count > 50 → **Email**

---

### 3. Payment System Monitoring ⭐ CRITICAL

**What:** Are PayPal payments working?  
**Why:** Broken payments = zero revenue

**Setup (30 minutes):**

```python
# backend/app/services/paypal_monitor.py
from datetime import datetime, timedelta
import asyncio

class PayPalMonitor:
    def __init__(self):
        self.last_successful_payment = None
        self.failed_webhooks = []
    
    async def check_health(self):
        """Run every 10 minutes"""
        
        # Check recent payment success
        recent_payments = await supabase.table('payments')\
            .select('*')\
            .gte('created_at', (datetime.utcnow() - timedelta(hours=24)).isoformat())\
            .execute()
        
        if recent_payments.data:
            failed = [p for p in recent_payments.data if p['status'] == 'failed']
            success_rate = 1 - (len(failed) / len(recent_payments.data))
            
            if success_rate < 0.9:  # < 90% success
                await self.send_alert(
                    severity='high',
                    message=f"PayPal payment success rate: {success_rate:.1%} (last 24h)"
                )
        
        # Check webhook delivery
        recent_webhooks = await supabase.table('webhook_events')\
            .select('*')\
            .gte('created_at', (datetime.utcnow() - timedelta(hours=1)).isoformat())\
            .execute()
        
        if recent_webhooks.data:
            unprocessed = [w for w in recent_webhooks.data if not w['processed']]
            if len(unprocessed) > 3:
                await self.send_alert(
                    severity='high',
                    message=f"{len(unprocessed)} PayPal webhooks not processed"
                )
    
    async def send_alert(self, severity: str, message: str):
        """Send alert via email and log"""
        logger.error(f"[{severity.upper()}] {message}")
        
        # Send email alert (using Azure Communication Services - FREE tier)
        # Or use SendGrid free tier (100 emails/day)
        # Implementation below

# Add to main.py
paypal_monitor = PayPalMonitor()

@app.on_event("startup")
async def start_paypal_monitor():
    async def monitor_loop():
        while True:
            try:
                await paypal_monitor.check_health()
            except Exception as e:
                logger.error(f"PayPal monitor error: {e}")
            await asyncio.sleep(600)  # Every 10 minutes
    
    asyncio.create_task(monitor_loop())
```

**Alerts:**
- Payment success rate < 90% → **Email immediately**
- Webhook not processed in 1 hour → **Email**
- Zero payments in 7 days → **Email** (sanity check)

---

### 4. API Performance ⭐ CRITICAL

**What:** How fast are API responses?  
**Why:** Slow API = frustrated users = churn

**Setup with Prometheus (Self-hosted on Azure):**

```python
# backend/requirements.txt
prometheus-client==0.18.0
prometheus-fastapi-instrumentator==6.1.0

# backend/app/main.py
from prometheus_client import make_asgi_app, Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

# Metrics endpoint for Prometheus to scrape
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Auto-instrument FastAPI
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics"],
    inprogress_name="fastapi_inprogress_requests",
    inprogress_labels=True,
)

instrumentator.instrument(app).expose(app)

# Custom metrics
cv_parse_duration = Histogram(
    'cv_parse_duration_seconds',
    'Time to parse CV',
    buckets=[1, 2, 5, 10, 30, 60]
)

ai_match_duration = Histogram(
    'ai_match_duration_seconds',
    'Time to run AI matching',
    buckets=[0.5, 1, 2, 5, 10]
)

paypal_api_calls = Counter(
    'paypal_api_calls_total',
    'PayPal API calls',
    ['operation', 'status']
)

# Use in code
@cv_parse_duration.time()
async def parse_cv(file_path: str):
    # parsing logic
    pass

# For PayPal calls
try:
    result = await paypal_service.create_subscription(...)
    paypal_api_calls.labels(operation='create_subscription', status='success').inc()
except Exception:
    paypal_api_calls.labels(operation='create_subscription', status='error').inc()
    raise
```

**Alerts:**
- API p95 latency > 2 seconds → **Email**
- API error rate > 5% → **Email immediately**
- Specific endpoint failing → **Email**

---

## 🔧 Azure Setup: Self-Hosted Monitoring Stack

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Azure Container Instance (Monitoring Stack)             │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Prometheus  │  │   Grafana    │  │  Alertmanager│ │
│  │  (scraper)   │──│  (dashboards)│──│  (alerts)    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         │                                     │          │
│         │ Scrapes /metrics every 15s          │          │
│         ↓                                     ↓          │
└─────────────────────────────────────────────────────────┘
         │                                     │
         │                                     │ Sends alerts
         ↓                                     ↓
┌─────────────────┐                    ┌─────────────────┐
│ TailorJob API   │                    │ Email/Slack     │
│ /metrics        │                    │                 │
└─────────────────┘                    └─────────────────┘
```

### Cost Breakdown (Azure)

```
Azure Container Instance (B1s):
- 1 vCPU, 1GB RAM
- $0.013/hour = ~$10/month
- Perfect for Prometheus + Grafana + Alertmanager

Azure Storage (for metrics retention):
- 10GB = $0.20/month

Total: ~$11/month (from your $150 credits)
```

### Quick Deploy Script

```bash
# deploy-monitoring.sh
#!/bin/bash

RG="tailorjob-rg"
LOCATION="eastus"
ACI_NAME="tailorjob-monitoring"

# Create container instance
az container create \
  --resource-group $RG \
  --name $ACI_NAME \
  --image grafana/grafana:latest \
  --dns-name-label tailorjob-grafana \
  --ports 3000 \
  --cpu 1 \
  --memory 1 \
  --environment-variables \
    GF_SECURITY_ADMIN_PASSWORD=<change-me> \
    GF_INSTALL_PLUGINS=grafana-piechart-panel \
  --location $LOCATION

# Get the FQDN
GRAFANA_URL=$(az container show --resource-group $RG --name $ACI_NAME --query ipAddress.fqdn --output tsv)

echo "Grafana URL: http://${GRAFANA_URL}:3000"
echo "Username: admin"
echo "Password: <change-me>"

# Create Prometheus container
az container create \
  --resource-group $RG \
  --name tailorjob-prometheus \
  --image prom/prometheus:latest \
  --dns-name-label tailorjob-prometheus \
  --ports 9090 \
  --cpu 1 \
  --memory 1 \
  --location $LOCATION

# Create Alertmanager container
az container create \
  --resource-group $RG \
  --name tailorjob-alertmanager \
  --image prom/alertmanager:latest \
  --dns-name-label tailorjob-alertmanager \
  --ports 9093 \
  --cpu 0.5 \
  --memory 0.5 \
  --location $LOCATION
```

---

## 📧 Alert Delivery Setup

### Option 1: Email (FREE, built into Azure)

```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'smtp.office365.com:587'
  smtp_from: 'alerts@yourdomain.com'
  smtp_auth_username: 'alerts@yourdomain.com'
  smtp_auth_password: 'your-password'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'email-alerts'

receivers:
  - name: 'email-alerts'
    email_configs:
      - to: 'your-email@gmail.com'
        require_tls: true
        headers:
          Subject: '🚨 TailorJob Alert: {{ .GroupLabels.alertname }}'
```

### Option 2: Slack (FREE webhook)

```yaml
# alertmanager.yml (add to receivers)
receivers:
  - name: 'slack-critical'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        title: '🚨 Critical Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
        send_resolved: true
```

**Create Slack webhook:**
1. Go to https://api.slack.com/apps
2. Create new app → Incoming Webhooks
3. Copy webhook URL
4. Paste into alertmanager config

### Option 3: SMS (Azure Communication Services FREE tier)

```python
# backend/app/services/alerts.py
from azure.communication.sms import SmsClient

sms_client = SmsClient.from_connection_string(
    os.getenv('AZURE_COMMUNICATION_CONNECTION_STRING')
)

async def send_critical_alert(message: str):
    """Send SMS for critical issues"""
    try:
        sms_client.send(
            from_="+1234567890",  # Your Azure phone number
            to=["+972-your-number"],
            message=f"🚨 TailorJob: {message}"
        )
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
```

**Azure Communication Services FREE tier:**
- $1.00 credit/month = ~60 SMS messages
- Perfect for critical alerts only

---

## 📊 Minimal Grafana Dashboard (Copy-Paste)

Save this as `tailorjob-dashboard.json` and import to Grafana:

```json
{
  "dashboard": {
    "title": "TailorJob - Pre-Launch Monitoring",
    "panels": [
      {
        "title": "API Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "API Latency (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "PayPal API Calls",
        "targets": [
          {
            "expr": "paypal_api_calls_total"
          }
        ],
        "type": "stat"
      },
      {
        "title": "Active Users (last 5 min)",
        "targets": [
          {
            "expr": "count(http_requests_total{endpoint=\"/api/cv/list\"})"
          }
        ],
        "type": "stat"
      }
    ]
  }
}
```

---

## 🚀 Implementation Timeline

### Day 1 (4 hours) - Critical Path

```
✅ 09:00-10:00  Set up Azure Application Insights (backend)
✅ 10:00-10:30  Add Sentry to frontend
✅ 10:30-11:30  Deploy Prometheus + Grafana on Azure
✅ 11:30-12:00  Configure Prometheus scraping
✅ 13:00-14:00  Set up Alertmanager with email
✅ 14:00-15:00  Create basic Grafana dashboard
✅ 15:00-16:00  Test all alerts (trigger manually)
```

### Day 2 (2 hours) - Polish

```
✅ 09:00-10:00  Add PayPal monitoring
✅ 10:00-11:00  Set up Slack webhook
✅ 11:00-12:00  Document runbook (how to respond to alerts)
```

---

## ✅ Pre-Launch Checklist

Before you launch to first customer:

- [ ] **Uptime monitoring active** (Azure App Insights web tests)
- [ ] **Error tracking working** (test by throwing error)
- [ ] **Alerts delivering to email** (test by triggering alert)
- [ ] **Grafana dashboard accessible** (bookmark URL)
- [ ] **PayPal monitoring running** (check logs)
- [ ] **You can access logs** (know where to look)
- [ ] **Runbook created** (what to do when alerts fire)

---

## 🎯 What You'll Actually Monitor Day 1

**You will receive alerts for:**

1. **Site is down** → SMS + Email (fix immediately)
2. **API throwing 500 errors** → Email (investigate within 1 hour)
3. **PayPal payment failed** → Email (check PayPal dashboard)
4. **Frontend JavaScript error** → Email daily digest

**You will check Grafana for:**

1. **How many users are active** (once per day)
2. **API response times** (if users complain about slowness)
3. **Error trends** (weekly review)

**You will NOT monitor day 1:**

- Business metrics (too early, no users yet)
- Detailed performance traces (overkill)
- Log aggregation (use Azure App Insights built-in)
- Cost tracking (not needed until scale)

---

## 📱 Sample Alert Messages

### Critical (SMS + Email)
```
🚨 TailorJob CRITICAL
Site Down: tailorjob.vercel.app
Detected: 2024-12-09 14:32 UTC
Action: Check Vercel dashboard
```

### High (Email)
```
⚠️ TailorJob Alert
Error Rate Spike: 12 errors/min (normal: 0-2)
Endpoint: /api/matching/analyze
Action: Check Application Insights logs
Dashboard: [link]
```

### Medium (Email Daily)
```
📊 TailorJob Daily Summary
Uptime: 99.95%
Errors: 3 (all handled)
Active users: 12
Slow API calls: /api/tailor/generate-pdf (4.2s avg)
```

---

## 💰 Total Cost Breakdown

```
Azure Container Instance (monitoring):     $11/mo
Azure Application Insights:                 FREE (5GB/mo)
Sentry (free tier):                         $0
Slack webhook:                              $0
Email alerts:                               $0
SMS alerts (Azure Comm Services):           $0 (60 SMS/mo free)
───────────────────────────────────────────────────
TOTAL:                                      $11/mo

Your Azure credits:                         $150/mo
Remaining for compute:                      $139/mo
```

---

## 🎓 Learning Resources

**After launch, when you have time:**

1. Grafana tutorial: https://grafana.com/docs/grafana/latest/getting-started/
2. Prometheus best practices: https://prometheus.io/docs/practices/naming/
3. Azure App Insights docs: https://docs.microsoft.com/en-us/azure/azure-monitor/

---

## Quick Start Commands

```bash
# 1. Deploy monitoring stack
./deploy-monitoring.sh

# 2. Add env var to backend
az webapp config appsettings set \
  --resource-group tailorjob-rg \
  --name tailorjob-api \
  --settings APPLICATIONINSIGHTS_CONNECTION_STRING="<from-portal>"

# 3. Get Grafana URL
az container show \
  --resource-group tailorjob-rg \
  --name tailorjob-monitoring \
  --query ipAddress.fqdn -o tsv

# 4. Open Grafana
# http://<fqdn>:3000
# Login: admin / <your-password>

# 5. Add Prometheus data source in Grafana
# URL: http://tailorjob-prometheus:9090

# 6. Import dashboard (paste JSON)

# 7. Test alert
curl https://tailorjob-api.azurewebsites.net/trigger-test-error
```

---

## Summary

**What you're getting:**
- ✅ Site uptime monitoring
- ✅ Error tracking (frontend + backend)
- ✅ API performance monitoring
- ✅ Payment system monitoring
- ✅ Grafana dashboards
- ✅ Email + SMS + Slack alerts

**What it costs:**
- $11/month from your $150 Azure credits
- Zero additional spend
- Zero new subscriptions needed

**Time to implement:**
- 4-6 hours total
- Most of it is waiting for Azure deployments

**What you'll know:**
- Is my site up?
- Are users experiencing errors?
- Are payments working?
- Is the API fast enough?

This is everything you need to launch confidently. No more, no less.