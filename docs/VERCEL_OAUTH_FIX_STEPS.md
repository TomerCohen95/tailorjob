# Fix "disabled_client" Error on Vercel - Step by Step

## Problem
Error on https://tailorjob.vercel.app/:
```
Access blocked: Authorization Error
Error 401: disabled_client
The OAuth client was disabled.
```

## IMMEDIATE FIX (5 minutes)

### Step 1: Go to Google Cloud Console
1. Open: https://console.cloud.google.com/apis/credentials
2. Sign in with your Google account that owns the project
3. Find your OAuth 2.0 Client ID (look for "Web client" or similar)

### Step 2: Check if OAuth Client is Disabled
- If you see "Disabled" status → Click on it and **Enable** it
- If it's enabled, proceed to Step 3

### Step 3: Add Vercel URL to Authorized Redirect URIs
1. Click on your OAuth 2.0 Client ID to edit
2. Scroll to **"Authorized redirect URIs"**
3. Add these two URIs (click "+ ADD URI" for each):
   ```
   https://sdclmjzsepnxuhhruazg.supabase.co/auth/v1/callback
   https://tailorjob.vercel.app/auth/callback
   ```
4. Click **SAVE**

### Step 4: Verify Supabase Configuration
1. Go to: https://app.supabase.com/project/sdclmjzsepnxuhhruazg/auth/providers
2. Click on **Google** provider
3. Verify:
   - ✅ **Enabled** is turned ON
   - ✅ **Client ID** matches your Google Cloud Console OAuth client
   - ✅ **Client Secret** matches your Google Cloud Console OAuth client
4. If credentials are wrong or missing, copy them from Google Cloud Console
5. Click **Save**

### Step 5: Update Supabase Site URL
1. Go to: https://app.supabase.com/project/sdclmjzsepnxuhhruazg/settings/api
2. Under **Configuration** → **URL Configuration**:
   - **Site URL**: `https://tailorjob.vercel.app`
3. Under **Redirect URLs**, add:
   ```
   https://tailorjob.vercel.app/**
   https://tailorjob.vercel.app/auth/callback
   ```
4. Click **Save**

### Step 6: Test
1. Clear browser cache/cookies for tailorjob.vercel.app
2. Go to: https://tailorjob.vercel.app/login
3. Click "Sign in with Google"
4. Google account picker should appear
5. Select your account → Should work!

## If It Still Doesn't Work

### Option A: Create New OAuth Client
If the current OAuth client is corrupted or permanently disabled:

1. **Google Cloud Console** → Create Credentials → OAuth 2.0 Client ID
2. Application type: **Web application**
3. Name: "TailorJob Production"
4. Authorized redirect URIs:
   ```
   https://sdclmjzsepnxuhhruazg.supabase.co/auth/v1/callback
   https://tailorjob.vercel.app/auth/callback
   ```
5. Click **Create**
6. Copy the new **Client ID** and **Client Secret**
7. Update in Supabase (Step 4 above)

### Option B: Temporary Workaround - Use Email Auth
If you need immediate access:

1. Go to: https://tailorjob.vercel.app/signup
2. Look for **"Email/Password"** signup option (if available)
3. OR temporarily disable Google OAuth in Supabase and add email auth to frontend

## Why This Happened

The OAuth client was either:
1. **Disabled** in Google Cloud Console (someone clicked "Disable")
2. **Missing Vercel URL** in authorized redirect URIs
3. **Wrong credentials** in Supabase configuration
4. **Vercel domain changed** and OAuth wasn't updated

## Common Mistakes

❌ **Wrong redirect URI format** - Must be exact:
- ✅ `https://sdclmjzsepnxuhhruazg.supabase.co/auth/v1/callback`
- ❌ `https://sdclmjzsepnxuhhruazg.supabase.co/auth/callback` (missing v1)

❌ **Using localhost URIs in production** - Localhost URIs don't work on Vercel

❌ **Not saving changes** in Google Cloud Console or Supabase

## Quick Links

- **Google Cloud Console**: https://console.cloud.google.com/apis/credentials
- **Supabase OAuth Settings**: https://app.supabase.com/project/sdclmjzsepnxuhhruazg/auth/providers
- **Supabase API Settings**: https://app.supabase.com/project/sdclmjzsepnxuhhruazg/settings/api
- **Your App**: https://tailorjob.vercel.app/

## Need Help?

If you're still stuck:
1. Check browser console for errors (F12 → Console tab)
2. Check Supabase logs: https://app.supabase.com/project/sdclmjzsepnxuhhruazg/logs/edge-logs
3. Verify you're using the correct Google account (the one that owns the OAuth client)