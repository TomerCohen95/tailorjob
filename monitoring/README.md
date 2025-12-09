# TailorJob Monitoring Stack

Complete monitoring setup with Prometheus, Grafana, Alertmanager, and Discord notifications.

## 🎯 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Discord webhook URL (see setup below)
- Access to Azure or any server to run containers

### Setup Steps

#### 1. Get Discord Webhook URL

1. Open your Discord server
2. Go to Server Settings → Integrations → Webhooks
3. Click "New Webhook"
4. Name it "TailorJob Alerts"
5. Select the channel for alerts (e.g., #monitoring)
6. Copy the Webhook URL

#### 2. Configure Environment

```bash
cd monitoring
cp .env.example .env
nano .env
```

Fill in:
```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
GRAFANA_ADMIN_PASSWORD=your-strong-password-here
```

#### 3. Deploy

```bash
chmod +x deploy-monitoring.sh
./deploy-monitoring.sh
```

#### 4. Access Grafana

Open http://localhost:3000 (or your server IP)
- Username: `admin`
- Password: (what you set in .env)

#### 5. Import Dashboard

1. In Grafana, click "+" → "Import"
2. Upload `grafana-dashboards/tailorjob-dashboard.json`
3. Select "Prometheus" as data source
4. Click "Import"

### 🎉 Done!

You now have:
- ✅ Prometheus collecting metrics from your API
- ✅ Grafana visualizing the metrics
- ✅ Alertmanager routing alerts
- ✅ Discord receiving notifications

---

## 📊 What's Being Monitored

### Critical Alerts (Discord @everyone)

- **Site Down**: API unreachable for 2+ minutes
- **High Error Rate**: >5% of requests failing
- **PayPal Issues**: Payment failure rate >10%

### Warning Alerts (Discord notification)

- **High API Latency**: p95 latency >2s for 10+ minutes
- **Queue Backlog**: >50 CVs waiting to parse for 15+ minutes
- **High Cancellation Rate**: >2 subscription cancellations per hour

### Info Alerts (Discord quiet)

- **No Signups**: Zero signups in 24 hours
- **Business metrics**: Daily summaries

---

## 🔧 Configuration Files

### `prometheus.yml`
- Scrapes metrics from your API every 15s
- Evaluates alert rules every 15s
- Connects to Alertmanager

### `alerts.yml`
- Defines all alert conditions
- Groups alerts by severity
- Sets thresholds for each metric

### `alertmanager.yml`
- Routes alerts to Discord
- Groups alerts to reduce noise
- Manages alert lifecycle

### `docker-compose.yml`
- Orchestrates all services
- Handles networking
- Manages volumes for persistence

---

## 📈 Accessing Services

| Service | URL | Purpose |
|---------|-----|---------|
| Grafana | http://localhost:3000 | Dashboards & visualization |
| Prometheus | http://localhost:9090 | Metrics database & queries |
| Alertmanager | http://localhost:9093 | Alert management |

---

## 🐛 Troubleshooting

### Discord alerts not working

```bash
# Check forwarder logs
docker logs tailorjob-discord-forwarder

# Test webhook manually
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{"alerts":[{"labels":{"alertname":"TestAlert","severity":"info"},"annotations":{"summary":"Test"}}]}'
```

### Prometheus not scraping

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check if API metrics endpoint works
curl https://tailorjob-api.azurewebsites.net/metrics
```

### Grafana dashboard empty

1. Check data source: Configuration → Data Sources → Prometheus
2. Verify connection: Click "Save & Test"
3. Check Prometheus has data: http://localhost:9090/graph

---

## 🔄 Management Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f prometheus
docker-compose logs -f grafana
docker-compose logs -f discord-forwarder

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v

# Update containers
docker-compose pull
docker-compose up -d
```

---

## 🚨 Testing Alerts

### Test Critical Alert

```bash
# Trigger a test error on your API
curl -X POST https://tailorjob-api.azurewebsites.net/test-error

# Or stop the API to trigger "Site Down" alert
```

### Check Alert Status

```bash
# View active alerts in Alertmanager
curl http://localhost:9093/api/v2/alerts

# View alerts in Prometheus
curl http://localhost:9090/api/v1/alerts
```

---

## 📝 Customizing Alerts

### Add New Alert

Edit `alerts.yml`:

```yaml
- alert: MyNewAlert
  expr: my_metric > 100
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "My metric is high"
    description: "Current value: {{ $value }}"
    action: "Check the logs"
```

Reload Prometheus:
```bash
docker-compose restart prometheus
```

### Change Discord Message Format

Edit `discord-webhook-forwarder.py` and rebuild:
```bash
docker-compose build discord-forwarder
docker-compose up -d discord-forwarder
```

---

## 🎨 Customizing Dashboards

### Modify Existing Dashboard

1. Open dashboard in Grafana
2. Click settings (gear icon)
3. Click "JSON Model"
4. Make changes
5. Click "Save" → "Save JSON to file"
6. Replace `grafana-dashboards/tailorjob-dashboard.json`

### Add New Panel

1. Click "Add panel"
2. Write PromQL query
3. Configure visualization
4. Save dashboard
5. Export JSON for version control

---

## 💰 Cost on Azure

Running on Azure Container Instance:

```
4 containers × $0.013/hour = $0.052/hour
= ~$37/month

Your Azure credits: $150/month
Remaining for app: $113/month
```

---

## 🔒 Security Notes

- Grafana admin password is set via environment variable
- Prometheus and Alertmanager have no auth (run behind firewall or VPN)
- Discord webhook URL is sensitive (never commit to git)
- All data stays in your environment (no cloud services)

---

## 📚 Learning Resources

- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Tutorials](https://grafana.com/tutorials/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Discord Webhook Guide](https://support.discord.com/hc/en-us/articles/228383668)

---

## 🆘 Support

If you encounter issues:

1. Check service logs: `docker-compose logs -f`
2. Verify environment variables: `cat .env`
3. Test connectivity: `curl http://localhost:9090/-/healthy`
4. Review alert rules: `cat alerts.yml`

Common fixes:
- **Port conflict**: Change ports in `docker-compose.yml`
- **Permission denied**: Run with `sudo` or add user to docker group
- **Out of memory**: Reduce retention time in prometheus config