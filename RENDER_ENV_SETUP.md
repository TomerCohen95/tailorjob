# Render Environment Variables Setup

## Current Variables (Already in backend/.env)
These should already be configured on Render:

```bash
SUPABASE_URL=https://sdclmjzsepnxuhhruazg.supabase.co
SUPABASE_KEY=eyJhbGci... (service role key)
UPSTASH_REDIS_URL=rediss://default:AYapAA... (Redis connection string)
AZURE_OPENAI_ENDPOINT=https://eastus.api.cognitive.microsoft.com/
AZURE_OPENAI_KEY=6cfbb5116a5846fcaef1c29cade63138
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","http://localhost:8082"]
ENVIRONMENT=development
```

## NEW Variables to Add on Render

### PayPal Configuration (REQUIRED)
These are needed for the PayPal subscription integration:

```bash
# PayPal API Credentials (get from https://developer.paypal.com/dashboard)
PAYPAL_CLIENT_ID=<your-production-paypal-client-id>
PAYPAL_SECRET=<your-production-paypal-secret>

# PayPal Environment (IMPORTANT: use production URL for real payments)
PAYPAL_BASE_URL=https://api-m.paypal.com

# PayPal Webhook ID (create webhook at https://developer.paypal.com/dashboard)
PAYPAL_WEBHOOK_ID=<your-production-webhook-id>

# PayPal Plan IDs (you mentioned these earlier - production IDs)
PAYPAL_PLAN_ID_BASIC=P-8UV13290MJ233664RNEW6MTY
PAYPAL_PLAN_ID_PRO=P-1KK587352S595433KNEW6LZQ
```

### Frontend URL (OPTIONAL)
```bash
# Auto-detects from request origin if not set
# Set explicitly if you want to override:
FRONTEND_URL=https://tailorjob.vercel.app
```

### Update CORS for Production
```bash
# Update to include production frontend URL:
CORS_ORIGINS=["https://tailorjob.vercel.app"]
```

### Update Environment
```bash
# Change from development to production:
ENVIRONMENT=production
```

## How to Add on Render

1. Go to https://dashboard.render.com
2. Select your backend service
3. Click "Environment" tab in the left sidebar
4. Click "Add Environment Variable" for each new variable
5. After adding all variables, Render will automatically redeploy

## Verification

After deployment, check the logs for:
- `✅ CV Matcher client initialized successfully`
- No errors about missing PayPal configuration
- PayPal endpoints returning 200 OK

## Testing

Test the subscription flow:
1. Visit your production site
2. Go to /pricing
3. Click "Subscribe" for Basic or Pro
4. Complete PayPal flow
5. Check /account to verify subscription shows correctly