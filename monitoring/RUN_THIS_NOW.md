# Deploy Monitoring to Azure - Run This Now

## Step 1: Get Discord Webhook (2 minutes)

1. Open Discord
2. Go to your server settings
3. Click **Integrations** → **Webhooks**
4. Click **New Webhook**
5. Name it "TailorJob Alerts"
6. Copy the webhook URL (looks like: `https://discord.com/api/webhooks/123456/abcdef`)

## Step 2: Configure Environment (1 minute)

```bash
cd monitoring
cp .env.example .env
```

Edit `.env` file and set:
```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ACTUAL_WEBHOOK_HERE
GRAFANA_ADMIN_PASSWORD=YourStrongPassword123!
```

## Step 3: Login to Azure (30 seconds)

```bash
az login
```

Your browser will open - login with your Azure account.

## Step 4: Deploy (3 minutes)

```bash
./deploy-to-azure.sh
```

That's it! The script will:
- ✅ Create storage for persistent data
- ✅ Deploy Prometheus, Grafana, Alertmanager
- ✅ Configure everything automatically
- ✅ Give you the Grafana URL at the end

## Step 5: Access Grafana

The script will output something like:
```
Grafana Dashboard: http://tailorjob-grafana-123456.eastus.azurecontainer.io:3000
Username: admin
Password: (your password from .env)
```

Open that URL and login!

---

## If You Get Errors

### "DISCORD_WEBHOOK_URL not set"
- Edit `monitoring/.env` and add your webhook URL

### "Not logged in to Azure"
- Run: `az login`

### "Resource group not found"
- The script will create it automatically

### "Permission denied"
- Run: `chmod +x deploy-to-azure.sh`

---

## After Deployment

1. Open Grafana URL
2. Login (admin / your-password)
3. Add Prometheus data source:
   - URL: `http://tailorjob-prometheus-XXXXX.eastus.azurecontainer.io:9090`
   - (Use the Prometheus URL from deployment output)
4. Import dashboard from `grafana-dashboards/tailorjob-dashboard.json`

Done! Your monitoring is live.

---

**Cost**: ~$31/month from your $150 Azure credits
**Time to deploy**: ~5 minutes total