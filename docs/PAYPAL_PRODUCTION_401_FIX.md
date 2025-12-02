# PayPal 401 Unauthorized Error - Production Fix

## Problem
Production backend on Render is returning:
```
Failed to create subscription: Error: Failed to create subscription: 401 Client Error: Unauthorized for url: https://api-m.sandbox.paypal.com/v1/oauth2/token
```

## Root Cause
The PayPal credentials configured in Render are either:
1. Missing or empty
2. Incorrect (wrong Client ID or Secret)
3. Mismatched (sandbox credentials with production URL, or vice versa)

## Solution

### Step 1: Verify PayPal Credentials

1. Go to [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/applications)
2. Select your app (or create new one if needed)
3. Copy the correct credentials:
   - **Client ID**: Shows immediately
   - **Secret**: Click "Show" to reveal it

### Step 2: Determine Environment

**For Sandbox Testing:**
- Use Sandbox credentials from your sandbox app
- Base URL: `https://api-m.sandbox.paypal.com`

**For Production:**
- Use Live credentials from your live app
- Base URL: `https://api-m.paypal.com`

### Step 3: Update Render Environment Variables

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Select your backend service (e.g., `tailorjob-backend`)
3. Go to **Environment** tab
4. Update/Add these variables:

```bash
# PayPal Credentials
PAYPAL_CLIENT_ID=your-actual-client-id-here
PAYPAL_SECRET=your-actual-secret-here

# For Sandbox Testing
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com

# OR for Production (after testing)
# PAYPAL_BASE_URL=https://api-m.paypal.com
```

5. Click **Save Changes**
6. Render will automatically redeploy

### Step 4: Update Plan IDs

Make sure the PayPal Plan IDs in your environment match your actual plans:

```bash
# In Render Environment Variables
PAYPAL_PLAN_ID_BASIC=P-YOUR-ACTUAL-BASIC-PLAN-ID
PAYPAL_PLAN_ID_PRO=P-YOUR-ACTUAL-PRO-PLAN-ID
```

To find your Plan IDs:
1. Go to PayPal Dashboard → Products & Services → Subscriptions
2. Find your plans and copy the Plan IDs (format: `P-XXXXXXXXXX`)

### Step 5: Verify Configuration

After deployment completes (~5 minutes), test:

```bash
# Check if backend can authenticate with PayPal
curl -X POST https://tailorjob.onrender.com/api/payments/subscriptions/create \
  -H "Authorization: Bearer YOUR_SUPABASE_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "basic_monthly",
    "return_url": "https://tailorjob.vercel.app/account?success=true",
    "cancel_url": "https://tailorjob.vercel.app/pricing?cancelled=true"
  }'
```

Expected response (success):
```json
{
  "subscription_id": "I-XXXXXXXXXX",
  "approval_url": "https://www.sandbox.paypal.com/...",
  "status": "APPROVAL_PENDING"
}
```

Error response (still failing):
```json
{
  "detail": "Failed to create subscription: 401 Client Error..."
}
```

## Common Mistakes

### ❌ Wrong: Empty or placeholder values
```bash
PAYPAL_CLIENT_ID=
PAYPAL_SECRET=your-secret-here  # placeholder text
```

### ✅ Correct: Actual credentials
```bash
PAYPAL_CLIENT_ID=AeXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
PAYPAL_SECRET=EPXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXxxx
```

### ❌ Wrong: Mismatched environment
```bash
# Using sandbox credentials with production URL
PAYPAL_CLIENT_ID=AeXXXX-sandbox-XXXXX
PAYPAL_BASE_URL=https://api-m.paypal.com  # production URL
```

### ✅ Correct: Matched environment
```bash
# Sandbox credentials with sandbox URL
PAYPAL_CLIENT_ID=AeXXXX-sandbox-XXXXX
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
```

## Testing Checklist

After updating credentials:

- [ ] Backend deployed successfully
- [ ] Environment variables saved in Render
- [ ] Can create subscription (no 401 error)
- [ ] Approval URL returns successfully
- [ ] Can complete subscription flow in PayPal
- [ ] Subscription activates in database

## Debug Commands

Check if credentials are loaded:
```python
# In backend Python shell or logs
from app.config import settings
print(f"Client ID: {settings.PAYPAL_CLIENT_ID[:10]}...")  # First 10 chars
print(f"Secret: {settings.PAYPAL_SECRET[:10]}...")
print(f"Base URL: {settings.PAYPAL_BASE_URL}")
```

Test PayPal authentication directly:
```python
from app.services.paypal_service import paypal_service
try:
    token = paypal_service._get_access_token()
    print(f"✅ Authentication successful! Token: {token[:20]}...")
except Exception as e:
    print(f"❌ Authentication failed: {e}")
```

## Next Steps

Once authentication works:

1. **Test subscription flow** end-to-end in sandbox
2. **Set up webhooks** for subscription events
3. **Switch to production** when ready:
   - Create production PayPal app
   - Get production credentials
   - Update `PAYPAL_BASE_URL` to production
   - Create production subscription plans
   - Update plan IDs

## Support

If still having issues:

1. **Check Render logs** for detailed error messages
2. **Verify credentials** are exactly as shown in PayPal Dashboard (no extra spaces)
3. **Create new PayPal app** if credentials seem corrupted
4. **Contact PayPal Support** if authentication persists with correct credentials

---

## Quick Fix Summary

```bash
# 1. Get PayPal credentials from dashboard
# 2. Update Render environment variables:
PAYPAL_CLIENT_ID=your-real-client-id
PAYPAL_SECRET=your-real-secret
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com

# 3. Save and wait for auto-deploy
# 4. Test subscription creation from frontend
```

✅ **Success**: You should now be able to create PayPal subscriptions without 401 errors!