# Deploy to Render Using CLI

## Install Render CLI

```bash
# Install Render CLI
brew install render  # macOS
# or
npm install -g @render-oss/cli  # npm
```

## Login to Render

```bash
render login
# This will open a browser for authentication
```

## Deploy from CLI

### Option 1: Deploy Using render.yaml (Recommended)

```bash
# From project root
render blueprint launch

# This will:
# - Read render.yaml
# - Create the service
# - Deploy automatically
```

### Option 2: Create Service Manually via CLI

```bash
# Create a new web service
render services create web \
  --name tailorjob-api \
  --repo https://github.com/TomerCohen95/tailorjob \
  --branch main \
  --root-dir backend \
  --build-command "pip install -r requirements.txt" \
  --start-command "uvicorn app.main:app --host 0.0.0.0 --port \$PORT" \
  --runtime python \
  --plan free

# Set environment variables
render env set \
  --service tailorjob-api \
  SUPABASE_URL="https://sdclmjzsepnxuhhruazg.supabase.co" \
  SUPABASE_KEY="your_key" \
  AZ_OPENAI_ENDPOINT="your_endpoint" \
  AZ_OPENAI_API_KEY="your_key" \
  AZ_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini" \
  CORS_ORIGINS='["https://tailorjob.vercel.app"]'
```

## Check Deployment Status

```bash
# List all services
render services list

# Get service details
render services get tailorjob-api

# View logs
render logs tailorjob-api

# Tail logs (follow)
render logs tailorjob-api --tail
```

## Redeploy

```bash
# Trigger a new deployment
render services deploy tailorjob-api

# Or redeploy with specific commit
render services deploy tailorjob-api --commit abc123
```

## Update Environment Variables

```bash
# Set a single variable
render env set --service tailorjob-api AZ_OPENAI_API_KEY="new_key"

# Set multiple variables
render env set --service tailorjob-api \
  VAR1="value1" \
  VAR2="value2"

# List all environment variables
render env list --service tailorjob-api
```

## Delete Service

```bash
render services delete tailorjob-api
```

## Quick Start Commands

```bash
# 1. Install CLI
brew install render

# 2. Login
render login

# 3. Deploy (using render.yaml)
render blueprint launch

# 4. Check status
render services list

# 5. View logs
render logs tailorjob-api --tail
```

## Troubleshooting

### Authentication Issues
```bash
# Re-login
render logout
render login
```

### Build Failures
```bash
# Check logs
render logs tailorjob-api

# Redeploy
render services deploy tailorjob-api
```

### Environment Variable Issues
```bash
# List current env vars
render env list --service tailorjob-api

# Update env var
render env set --service tailorjob-api KEY="value"
```

## CI/CD with Render CLI

You can also use Render CLI in CI/CD:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Render
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install Render CLI
        run: npm install -g @render-oss/cli
      
      - name: Deploy to Render
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
        run: render services deploy tailorjob-api
```

## Notes

- The CLI uses the same authentication as the web dashboard
- `render.yaml` is the easiest way to deploy
- Environment variables can be set via CLI or dashboard
- Logs are real-time with `--tail` flag

## Full Documentation

https://render.com/docs/cli