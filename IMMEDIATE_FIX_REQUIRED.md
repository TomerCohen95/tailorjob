# IMMEDIATE FIX REQUIRED - disabled_client Error

## Current Problem
❌ **Error 401: disabled_client** on https://tailorjob.vercel.app/
❌ Google OAuth is completely broken
❌ Cannot sign in or sign up with Google

## Root Cause
Your Google OAuth client credentials are **DISABLED** in Google Cloud Console.

## IMMEDIATE ACTION REQUIRED (5 minutes)

### Step 1: Enable OAuth Client in Google Cloud Console

1. **Open**: https://console.cloud.google.com/apis/credentials
2. **Sign in** with the Google account that created the OAuth client
3. **Find** your OAuth 2.0 Client ID (looks like: "Web client" or "TailorJob")
4. **Check status**: If it shows "Disabled" → Click on it
5. **Enable it**: Find the "Enable" button and click it
6. **Save changes**

### Step 2: Add Vercel URL to Authorized Redirect URIs

While you're in Google Cloud Console:

1. Click on your OAuth 2.0 Client ID
2. Scroll to **"Authorized redirect URIs"**
3. Click **"+ ADD URI"**
4. Add: `https://sdclmjzsepnxuhhruazg.supabase.co/auth/v1/callback`
5. Click **"+ ADD URI"** again
6. Add: `https://tailorjob.vercel.app/auth/callback`
7. Click **"SAVE"** at the bottom

### Step 3: Test Immediately

1. Go to: https://tailorjob.vercel.app/login
2. Click "Sign in with Google"
3. **Should work now** (may still auto-select account, but won't show disabled_client error)

## If You Don't Have Access to Google Cloud Console

### Option A: Ask Team Member Who Has Access
Someone on your team needs access to Google Cloud Console to enable the OAuth client.

### Option B: Create New OAuth Client
If you can't access the current one:

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click: **"+ CREATE CREDENTIALS"** → **"OAuth 2.0 Client ID"**
3. Application type: **"Web application"**
4. Name: **"TailorJob Production"**
5. Authorized redirect URIs:
   - `https://sdclmjzsepnxuhhruazg.supabase.co/auth/v1/callback`
   - `https://tailorjob.vercel.app/auth/callback`
6. Click **"CREATE"**
7. **Copy** the Client ID and Client Secret
8. Update Supabase:
   - Go to: https://app.supabase.com/project/sdclmjzsepnxuhhruazg/auth/providers
   - Click **"Google"**
   - Paste new **Client ID** and **Client Secret**
   - Click **"Save"**

## Alternative: Disable Google OAuth Temporarily

If you can't fix Google OAuth right now:

1. Go to: https://app.supabase.com/project/sdclmjzsepnxuhhruazg/auth/providers
2. Find **"Google"** provider
3. Toggle it **OFF** (disable)
4. Click **"Save"**
5. Users can still sign up/login with **Email/Password** (if enabled)

## Why This Happened

Someone (or some automated process) **disabled** the OAuth client in Google Cloud Console.

Common causes:
- Accidental click on "Disable" button
- Google security scan flagged something
- Quota/billing issue
- Team member with access disabled it
- Google Cloud project was suspended/disabled

## After Fixing

Once OAuth is working again:
1. Test on Vercel: https://tailorjob.vercel.app/login
2. Deploy the account picker fix (already coded)
3. Clear browser cache to test account selection

## Need Help?

**Supabase Project**: sdclmjzsepnxuhhruazg
**Vercel App**: https://tailorjob.vercel.app/
**Google Cloud Console**: https://console.cloud.google.com/apis/credentials

The fix is in Google Cloud Console, not in the code!