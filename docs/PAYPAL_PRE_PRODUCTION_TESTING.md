# PayPal Pre-Production Testing Guide

Complete guide for testing PayPal subscriptions before going live with real money.

---

## 🎯 Current Status

### ✅ **Backend: Ready**
- All payment APIs implemented
- Webhook processing complete
- Usage enforcement ready
- Database migration ready

### ⚠️ **Frontend: Not Yet Implemented**
You do **NOT** have a ready screen for the integration yet. The frontend pricing page and PayPal buttons still need to be built.

**What's Missing:**
- Pricing page UI
- PayPal button integration
- Subscription context
- Usage display components

---

## 🧪 Testing Strategy: PayPal Sandbox

PayPal provides a **Sandbox environment** that lets you test the entire payment flow with **fake money** and **test accounts**.

### How Sandbox Works

```
Real PayPal          Sandbox PayPal
─────────────────    ─────────────────────────
💰 Real money        🎮 Fake money
👤 Real accounts     🤖 Test accounts  
✅ Goes live         🧪 Safe testing
⚠️ Real charges      ✨ No charges
```

---

## 📝 Pre-Production Testing Checklist

### Phase 1: Setup (30 minutes)

#### Step 1: Create Sandbox App
1. Go to [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/)
2. Click **"My Apps & Credentials"**
3. Under **Sandbox**, click **"Create App"**
4. App Name: `TailorJob Sandbox`
5. Copy **Sandbox Client ID** and **Secret**

#### Step 2: Create Test Accounts
1. Go to **Sandbox** → **Accounts**
2. Create **Personal Account** (buyer):
   - Email: `buyer-tailorjob@personal.example.com`
   - Password: `Test1234!`
   - Balance: $5,000 (fake money)
3. Create **Business Account** (seller):
   - Email: `seller-tailorjob@business.example.com` 
   - Password: `Test1234!`
   - Will receive payments

#### Step 3: Create Sandbox Subscription Plans

1. Go to **Sandbox** → **Products & Services** → **Subscriptions**
2. **Important**: Switch to Sandbox mode (toggle in top right)
3. Create plans:

**Basic Monthly Sandbox Plan:**
```
Name: TailorJob Basic Monthly (Sandbox)
Plan ID: P-SANDBOX-BASIC-MONTHLY (copy this!)
Price: $0.01 USD (for easier testing)
Billing: Monthly
Trial: 3 days free
```

**Pro Monthly Sandbox Plan:**
```
Name: TailorJob Pro Monthly (Sandbox)  
Plan ID: P-SANDBOX-PRO-MONTHLY (copy this!)
Price: $0.02 USD
Billing: Monthly
Trial: 3 days free
```

#### Step 4: Configure Backend for Sandbox

Update [`backend/.env`](backend/.env):
```bash
# Use SANDBOX credentials and URL
PAYPAL_CLIENT_ID=your-sandbox-client-id
PAYPAL_SECRET=your-sandbox-secret
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
PAYPAL_WEBHOOK_ID=your-sandbox-webhook-id
```

Update [`backend/app/services/paypal_service.py`](backend/app/services/paypal_service.py:18) with sandbox plan IDs:
```python
PLAN_IDS = {
    'basic_monthly': 'P-SANDBOX-BASIC-MONTHLY',
    'pro_monthly': 'P-SANDBOX-PRO-MONTHLY',
}
```

#### Step 5: Configure Sandbox Webhook

1. In your Sandbox app settings, go to **Webhooks**
2. Add webhook URL: `https://your-backend-url.com/api/payments/webhooks/paypal`
3. Select events (same as production)
4. Copy **Webhook ID** → update `.env`

---

### Phase 2: Manual API Testing (1 hour)

Test backend APIs directly before building frontend.

#### Test 1: Create Subscription

```bash
# Create subscription (get approval URL)
curl -X POST https://your-backend.com/api/payments/subscriptions/create \
  -H "X-User-Id: your-test-user-uuid" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "basic_monthly",
    "return_url": "https://yoursite.com/success",
    "cancel_url": "https://yoursite.com/cancel"
  }'

# Response:
{
  "subscription_id": "I-SANDBOX123",
  "approval_url": "https://www.sandbox.paypal.com/...",
  "status": "APPROVAL_PENDING"
}
```

#### Test 2: Approve Subscription (Manual)

1. Copy `approval_url` from response
2. Open in browser
3. Login with **Personal (buyer) sandbox account**
4. Click **"Agree & Subscribe"**
5. Get redirected to `return_url`

#### Test 3: Activate Subscription

```bash
# After PayPal approval, activate in your system
curl -X POST https://your-backend.com/api/payments/subscriptions/activate \
  -H "X-User-Id: your-test-user-uuid" \
  -d "subscription_id=I-SANDBOX123"

# Response:
{
  "success": true,
  "subscription": {...},
  "message": "Welcome to TailorJob Basic!"
}
```

#### Test 4: Check Subscription Status

```bash
# Get current subscription
curl https://your-backend.com/api/payments/subscriptions/me \
  -H "X-User-Id: your-test-user-uuid"

# Response:
{
  "tier": "basic",
  "status": "active",
  "usage": {"cvs": 0, "matches": 0, ...},
  "limits": {"cvs": 10, "matches": 50, ...}
}
```

#### Test 5: Test Usage Limits

```bash
# Try to upload 11th CV (should fail for Basic tier)
for i in {1..11}; do
  curl -X POST https://your-backend.com/api/cv/upload \
    -H "X-User-Id: your-test-user-uuid" \
    -F "file=@test-cv-$i.pdf"
done

# 11th upload should return 403:
{
  "detail": {
    "error": "Basic tier limit reached (10 cvs)",
    "upgrade_to": "pro",
    "message": "Upgrade to Pro for unlimited!"
  }
}
```

#### Test 6: Cancel Subscription

```bash
curl -X POST https://your-backend.com/api/payments/subscriptions/cancel \
  -H "X-User-Id: your-test-user-uuid" \
  -d "reason=Testing cancellation"

# Response:
{
  "success": true,
  "message": "Subscription cancelled. You can continue using until end of billing period.",
  "period_end": "2025-02-01T00:00:00Z"
}
```

#### Test 7: Verify Webhook Delivery

```bash
# Check webhook events received
curl https://your-backend.com/api/payments/webhooks/events \
  -H "X-User-Id: admin"

# Or check database directly:
SELECT * FROM webhook_events ORDER BY created_at DESC LIMIT 10;
```

---

### Phase 3: Build Minimal Test UI (2 hours)

Since frontend isn't ready, create a **minimal test page** for manual testing.

#### Option A: Simple HTML Page

Create `test-paypal.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>PayPal Test Page</title>
    <script src="https://www.paypal.com/sdk/js?client-id=YOUR-SANDBOX-CLIENT-ID&vault=true"></script>
</head>
<body>
    <h1>PayPal Subscription Test</h1>
    
    <div id="paypal-button-basic"></div>
    <div id="paypal-button-pro"></div>
    
    <script>
        // Basic tier button
        paypal.Buttons({
            createSubscription: function(data, actions) {
                return actions.subscription.create({
                    'plan_id': 'P-SANDBOX-BASIC-MONTHLY'
                });
            },
            onApprove: function(data, actions) {
                alert('Subscription ID: ' + data.subscriptionID);
                // Call your backend to activate
                fetch('https://your-backend.com/api/payments/subscriptions/activate', {
                    method: 'POST',
                    headers: {
                        'X-User-Id': 'test-user-uuid',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        subscription_id: data.subscriptionID
                    })
                });
            }
        }).render('#paypal-button-basic');
        
        // Pro tier button (similar)
    </script>
</body>
</html>
```

#### Option B: Use PayPal Postman Collection

1. Import [PayPal API Postman Collection](https://www.postman.com/paypal/workspace/paypal-public-api)
2. Configure Sandbox credentials
3. Test all subscription endpoints
4. Verify webhook delivery

---

### Phase 4: Full Integration Testing (3 hours)

Once you build the frontend pricing page:

#### Scenario 1: New User Subscribe to Basic

1. **User visits pricing page** → `/pricing`
2. **Clicks "Subscribe to Basic ($9.99/month)"**
3. **PayPal modal opens** with sandbox login
4. **User logs in** with Personal sandbox account
5. **Approves subscription**
6. **Redirects back** to success page
7. **Backend activates subscription** via webhook
8. **User sees "Welcome to Basic!"** message
9. **Verify database**: subscription status = `active`, tier = `basic`

#### Scenario 2: Basic User Hits Limit

1. **User uploads 10 CVs** (Basic tier limit)
2. **Try to upload 11th CV**
3. **Gets 403 error** with upgrade prompt
4. **Clicks "Upgrade to Pro"**
5. **Completes Pro subscription** ($19.99/month)
6. **Can now upload unlimited CVs**

#### Scenario 3: User Cancels Subscription

1. **User goes to Settings**
2. **Clicks "Cancel Subscription"**
3. **Confirms cancellation**
4. **Subscription status** = `cancelled`
5. **User can still use** until period end
6. **After period ends**, downgraded to Free tier

#### Scenario 4: Webhook Processing

1. **PayPal sends webhook** for `BILLING.SUBSCRIPTION.ACTIVATED`
2. **Backend verifies signature**
3. **Stores event** in `webhook_events` table
4. **Updates subscription** status to `active`
5. **Verify**: All data consistent in database

---

## 🔍 Monitoring During Testing

### Check Logs

```bash
# Backend logs
tail -f /var/log/backend.log

# Look for:
✓ "Subscription created: I-SANDBOX123"
✓ "Webhook received: BILLING.SUBSCRIPTION.ACTIVATED"
✓ "Payment recorded: $0.01"
```

### Check Database

```sql
-- Active subscriptions
SELECT * FROM subscriptions WHERE status = 'active';

-- Recent payments
SELECT * FROM payments ORDER BY created_at DESC LIMIT 10;

-- Webhook events
SELECT 
    event_type,
    processed,
    created_at
FROM webhook_events
ORDER BY created_at DESC
LIMIT 20;

-- Usage tracking
SELECT * FROM usage_tracking
WHERE user_id = 'test-user-uuid';
```

### Check PayPal Dashboard

1. Go to **Sandbox** → **Transactions**
2. See all test transactions
3. Verify webhooks sent
4. Check subscription status

---

## ⚠️ Common Testing Issues

### Issue 1: Webhook Not Received

**Symptom**: Subscription created but not activated in database

**Solution**:
1. Check webhook URL is publicly accessible
2. Verify webhook ID in `.env`
3. Check PayPal webhook logs for delivery failures
4. Test webhook manually: `curl -X POST https://your-backend.com/api/payments/webhooks/paypal`

### Issue 2: Signature Verification Fails

**Symptom**: Webhook received but rejected with 401

**Solution**:
1. Verify `PAYPAL_WEBHOOK_ID` matches sandbox webhook
2. Check headers are correct in request
3. Use PayPal's webhook simulator to test

### Issue 3: Wrong Plan ID

**Symptom**: "Unknown plan_id" error

**Solution**:
1. Update plan IDs in code to match sandbox plans
2. Verify plan IDs in PayPal sandbox dashboard
3. Check `PLAN_IDS` dictionary in `paypal_service.py`

---

## 🚀 Going Live Checklist

After successful sandbox testing:

- [ ] All 6 webhook events tested
- [ ] All 3 tiers tested (Free, Basic, Pro)
- [ ] Usage limits enforced correctly
- [ ] Cancellation works
- [ ] Upgrade/downgrade works
- [ ] Database consistent after all operations
- [ ] No errors in logs

**Then:**

1. Create **Production PayPal App**
2. Create **Real subscription plans** (with real prices)
3. Update `.env` with **production credentials**
4. Update `PAYPAL_BASE_URL` to production
5. Update **plan IDs** in code
6. Configure **production webhook**
7. Test with **$0.01 real charge** first
8. Monitor closely for 24 hours
9. Gradually increase prices to actual ($9.99, $19.99)

---

## 📊 Test Data Summary

### Sandbox Accounts
| Type | Email | Password | Balance |
|------|-------|----------|---------|
| Personal (Buyer) | `buyer-tailorjob@personal.example.com` | `Test1234!` | $5,000 |
| Business (Seller) | `seller-tailorjob@business.example.com` | `Test1234!` | $0 |

### Sandbox Plans
| Tier | Plan ID | Price | Billing |
|------|---------|-------|---------|
| Basic | `P-SANDBOX-BASIC-MONTHLY` | $0.01 | Monthly |
| Pro | `P-SANDBOX-PRO-MONTHLY` | $0.02 | Monthly |

### Test Users in Your System
| User UUID | Email | Tier |
|-----------|-------|------|
| `test-free-user` | `free@test.com` | Free |
| `test-basic-user` | `basic@test.com` | Basic |
| `test-pro-user` | `pro@test.com` | Pro |

---

## 🎓 Key Takeaways

1. **Sandbox is 100% safe** - No real money involved
2. **Test everything** before production
3. **Use low prices** ($0.01) for sandbox testing
4. **Frontend not required** to test backend APIs
5. **Build minimal UI** for manual testing first
6. **Verify webhooks** are received and processed
7. **Check database** after every operation
8. **Only go live** after thorough testing

---

## 📞 Need Help?

- [PayPal Sandbox Guide](https://developer.paypal.com/docs/api-basics/sandbox/)
- [PayPal Testing Best Practices](https://developer.paypal.com/docs/integration/testing/)
- [Webhook Simulator](https://developer.paypal.com/developer/webhooksSimulator)

Happy testing! 🧪✨