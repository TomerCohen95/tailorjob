# PayPal Integration Deployment Guide

Complete step-by-step guide for deploying PayPal subscription payments to TailorJob.

---

## 📋 Prerequisites

- PayPal Business account
- Access to PayPal Developer Dashboard
- Supabase project with admin access
- Backend deployed to Render (or similar)
- Frontend deployed to Vercel

---

## 🔧 Part 1: PayPal Configuration

### Step 1: Create PayPal App

1. Go to [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/applications)
2. Click **"Create App"**
3. App Name: `TailorJob Production` (or `TailorJob Sandbox` for testing)
4. App Type: **Merchant**
5. Click **Create App**

### Step 2: Get API Credentials

After creating the app:

1. Copy **Client ID** → Save as `PAYPAL_CLIENT_ID`
2. Click **"Show"** under Secret → Save as `PAYPAL_SECRET`
3. Note the environment (Sandbox or Live)

### Step 3: Create Subscription Plans

1. In PayPal Dashboard, go to **Products & Services** → **Subscriptions**
2. Click **Create Plan**

#### Basic Monthly Plan
- Plan Name: `TailorJob Basic Monthly`
- Plan ID: `P-BASIC-MONTHLY` (auto-generated, copy this!)
- Billing Cycle: Monthly
- Price: $9.99 USD
- Trial Period: Optional (e.g., 7 days free)

#### Basic Yearly Plan
- Plan Name: `TailorJob Basic Yearly`
- Plan ID: `P-BASIC-YEARLY`
- Billing Cycle: Yearly
- Price: $99.99 USD (20% discount)

#### Pro Monthly Plan
- Plan Name: `TailorJob Pro Monthly`
- Plan ID: `P-PRO-MONTHLY`
- Billing Cycle: Monthly
- Price: $19.99 USD

#### Pro Yearly Plan
- Plan Name: `TailorJob Pro Yearly`
- Plan ID: `P-PRO-YEARLY`
- Billing Cycle: Yearly
- Price: $199.99 USD (17% discount)

### Step 4: Configure Webhooks

1. In PayPal App settings, go to **Webhooks**
2. Click **Add Webhook**
3. Webhook URL: `https://tailorjob.onrender.com/api/payments/webhooks/paypal`
4. Select Event Types:
   - ✅ `BILLING.SUBSCRIPTION.ACTIVATED`
   - ✅ `BILLING.SUBSCRIPTION.CANCELLED`
   - ✅ `BILLING.SUBSCRIPTION.SUSPENDED`
   - ✅ `BILLING.SUBSCRIPTION.EXPIRED`
   - ✅ `PAYMENT.SALE.COMPLETED`
   - ✅ `PAYMENT.SALE.REFUNDED`
5. Click **Save**
6. Copy **Webhook ID** → Save as `PAYPAL_WEBHOOK_ID`

---

## 💾 Part 2: Database Setup

### Step 1: Run Migration

```bash
cd backend

# Connect to Supabase
# Option 1: Via Supabase Studio SQL Editor
# - Copy contents of supabase/migrations/20251130000000_add_subscriptions.sql
# - Paste into SQL Editor
# - Click "Run"

# Option 2: Via Supabase CLI (if installed)
supabase db push
```

### Step 2: Verify Tables Created

In Supabase Studio, check these tables exist:
- ✅ `subscriptions`
- ✅ `payments`
- ✅ `usage_tracking`
- ✅ `webhook_events`
- ✅ `profiles` (updated with subscription fields)

### Step 3: Test Database Functions

```sql
-- Test get_current_usage function
SELECT * FROM get_current_usage('your-test-user-uuid');

-- Should return: {"cvs_uploaded": 0, "jobs_matched": 0, ...}
```

---

## 🔌 Part 3: Backend Deployment

### Step 1: Update Environment Variables

Add to Render environment variables:

```bash
# PayPal Configuration
PAYPAL_CLIENT_ID=your-paypal-client-id-here
PAYPAL_SECRET=your-paypal-secret-here
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com  # Sandbox
# PAYPAL_BASE_URL=https://api-m.paypal.com        # Production
PAYPAL_WEBHOOK_ID=your-webhook-id-here
```

### Step 2: Update Plan IDs in Code

Edit [`backend/app/services/paypal_service.py`](backend/app/services/paypal_service.py:18):

```python
PLAN_IDS = {
    'basic_monthly': 'P-XXXXX',  # Replace with actual plan IDs from PayPal
    'basic_yearly': 'P-XXXXX',
    'pro_monthly': 'P-XXXXX',
    'pro_yearly': 'P-XXXXX',
}
```

### Step 3: Install Dependencies

Add to [`backend/requirements.txt`](backend/requirements.txt):

```txt
requests==2.31.0  # For PayPal API calls
```

### Step 4: Deploy Backend

```bash
git add -A
git commit -m "feat: add PayPal payment integration"
git push origin main

# Render will auto-deploy
# Wait ~5 minutes for deployment
```

### Step 5: Test API Endpoints

```bash
# Health check
curl https://tailorjob-api.onrender.com/health

# Check payment routes in docs
open https://tailorjob-api.onrender.com/docs
# Look for /api/payments/* endpoints
```

---

## 🎨 Part 4: Frontend Integration

### Step 1: Install PayPal SDK

```bash
cd /path/to/tailorjob
npm install @paypal/react-paypal-js
```

### Step 2: Add Environment Variable

In Vercel:
1. Go to Project Settings → Environment Variables
2. Add: `VITE_PAYPAL_CLIENT_ID` = `your-paypal-client-id`
3. Save

### Step 3: Create Pricing Page

Create [`src/pages/Pricing.tsx`](src/pages/Pricing.tsx) - see implementation plan

### Step 4: Add Route

Update [`src/App.tsx`](src/App.tsx):

```tsx
import Pricing from '@/pages/Pricing'

// Add route
<Route path="/pricing" element={<Pricing />} />
```

### Step 5: Deploy Frontend

```bash
git add -A
git commit -m "feat: add pricing page with PayPal integration"
git push origin main

# Vercel will auto-deploy
```

---

## 🧪 Part 5: Testing

### Sandbox Testing

#### Step 1: Create Test Accounts

1. Go to [PayPal Sandbox Accounts](https://developer.paypal.com/dashboard/accounts)
2. Create **Personal Account** (buyer) - note email/password
3. Create **Business Account** (seller) - note email/password

#### Step 2: Test Subscription Flow

1. Go to `https://tailorjob.vercel.app/pricing`
2. Click **"Subscribe to Basic"**
3. PayPal checkout opens
4. Login with **Personal (buyer) sandbox account**
5. Approve subscription
6. Verify redirect back to app
7. Check subscription activated in Dashboard

#### Step 3: Verify Database

```sql
-- Check subscription created
SELECT * FROM subscriptions WHERE user_id = 'test-user-id';

-- Check payment recorded
SELECT * FROM payments WHERE user_id = 'test-user-id';

-- Check webhook received
SELECT * FROM webhook_events ORDER BY created_at DESC LIMIT 10;
```

#### Step 4: Test Usage Limits

1. Try uploading 4 CVs as free user → Should get 403 error
2. Subscribe to Basic tier
3. Try uploading 4 CVs → Should succeed
4. Try uploading 11th CV → Should get 403 error
5. Upgrade to Pro → Should allow unlimited

#### Step 5: Test Cancellation

1. Go to Settings page
2. Click **"Cancel Subscription"**
3. Confirm cancellation
4. Verify status = `cancelled` in database
5. Verify still have access until period end

### Production Testing

After thorough sandbox testing:

1. Switch `PAYPAL_BASE_URL` to production API
2. Use real PayPal plan IDs
3. Update webhook URL to production
4. Test with small amount first ($0.99 test)
5. Verify webhook delivery in PayPal dashboard
6. Monitor error logs

---

## 📊 Part 6: Monitoring

### Webhook Monitoring

```sql
-- Check webhook processing
SELECT 
    event_type,
    processed,
    error_message,
    created_at
FROM webhook_events
ORDER BY created_at DESC
LIMIT 50;

-- Find failed webhooks
SELECT * FROM webhook_events
WHERE processed = FALSE
ORDER BY created_at DESC;
```

### Subscription Analytics

```sql
-- Active subscriptions by tier
SELECT tier, COUNT(*) as count
FROM subscriptions
WHERE status = 'active'
GROUP BY tier;

-- Monthly recurring revenue
SELECT 
    tier,
    COUNT(*) as subscribers,
    SUM(amount_decimal) as mrr
FROM subscriptions
WHERE status = 'active'
  AND billing_cycle = 'monthly'
GROUP BY tier;

-- Churn rate (last 30 days)
SELECT 
    COUNT(*) as cancelled_count,
    (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM subscriptions WHERE status = 'active')) as churn_rate
FROM subscriptions
WHERE cancelled_at >= NOW() - INTERVAL '30 days';
```

### Usage Tracking

```sql
-- Top users by usage
SELECT 
    u.email,
    ut.cvs_uploaded,
    ut.jobs_matched,
    ut.cvs_tailored,
    s.tier
FROM usage_tracking ut
JOIN profiles p ON ut.user_id = p.id
JOIN subscriptions s ON s.user_id = p.id
JOIN auth.users u ON u.id = p.id
WHERE ut.period_start >= DATE_TRUNC('month', NOW())
ORDER BY ut.cvs_tailored DESC
LIMIT 20;
```

---

## 🚨 Troubleshooting

### Issue: Webhook Not Received

**Solution:**
1. Check webhook URL in PayPal dashboard
2. Verify backend is accessible: `curl https://your-backend.com/health`
3. Check PayPal webhook logs for delivery failures
4. Verify webhook signature validation

### Issue: Subscription Not Activating

**Solution:**
1. Check PayPal subscription status: `GET /v1/billing/subscriptions/{id}`
2. Verify user approved subscription (check PayPal account)
3. Check webhook events table for `BILLING.SUBSCRIPTION.ACTIVATED`
4. Manually activate if webhook failed:
   ```sql
   UPDATE subscriptions 
   SET status = 'active' 
   WHERE paypal_subscription_id = 'I-XXXXX';
   ```

### Issue: Usage Limits Not Enforced

**Solution:**
1. Verify `@require_feature` decorator applied to endpoints
2. Check subscription tier in database matches expected
3. Test `can_use_feature()` function directly:
   ```python
   result = await subscription_service.can_use_feature(user_id, 'cv_upload')
   print(result)  # (True/False, error_message)
   ```

### Issue: Payment Not Recorded

**Solution:**
1. Check `PAYMENT.SALE.COMPLETED` webhook received
2. Verify payment handler in [`backend/app/api/routes/payments.py`](backend/app/api/routes/payments.py:456)
3. Check payments table for transaction
4. Review webhook error logs

---

## 📈 Going Live Checklist

- [ ] Sandbox testing completed (all flows work)
- [ ] Production PayPal app created
- [ ] Production subscription plans created
- [ ] Production webhook configured and tested
- [ ] Environment variables updated to production
- [ ] Plan IDs updated in code
- [ ] Frontend deployed with production PayPal client ID
- [ ] Database migration applied to production
- [ ] Test real subscription flow with $0.99 test
- [ ] Webhook delivery verified in production
- [ ] Usage limits tested and working
- [ ] Monitoring queries set up
- [ ] Error alerting configured
- [ ] Customer support process documented

---

## 💰 Cost Monitoring

### Monthly Costs

```
PayPal Fees: 2.9% + $0.30 per transaction
  - Basic ($9.99): $0.59 fee = $9.40 net (94.1%)
  - Pro ($19.99): $0.88 fee = $19.11 net (95.6%)

Backend (Render): $0-7/month
Database (Supabase): $0 (free tier)
Frontend (Vercel): $0 (free tier)

Total: $0-7/month fixed + transaction fees
```

### Revenue Tracking

```sql
-- Total revenue (last 30 days)
SELECT 
    SUM(amount_decimal) as total_revenue,
    COUNT(*) as transaction_count,
    AVG(amount_decimal) as avg_transaction
FROM payments
WHERE created_at >= NOW() - INTERVAL '30 days'
  AND status = 'completed';
```

---

## 📞 Support

For issues:
1. Check [PayPal Developer Forums](https://www.paypal-community.com/t5/Integration/ct-p/Integration)
2. Review [PayPal REST API Docs](https://developer.paypal.com/docs/api/overview/)
3. Check webhook events table for errors
4. Contact PayPal Support (Business accounts only)

---

## ✅ Success Criteria

Your PayPal integration is working when:

- ✅ Users can subscribe via PayPal checkout
- ✅ Subscriptions appear in database after approval
- ✅ Webhooks are received and processed
- ✅ Usage limits are enforced correctly
- ✅ Payments are recorded in database
- ✅ Cancellations work properly
- ✅ Users can upgrade/downgrade tiers
- ✅ Revenue tracking is accurate

Congratulations! Your payment system is live! 🎉