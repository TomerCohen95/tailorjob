# Fixing Google OAuth "disabled_client" Error on Vercel

## Problem
When deployed to Vercel, Google Sign-In shows:
```
Access blocked: Authorization Error
Error 401: disabled_client
The OAuth client was disabled.
```

## Root Cause
Google OAuth credentials in Supabase are either:
1. Disabled in Google Cloud Console
2. Not configured for Vercel production URLs
3. Using incorrect/expired credentials

## Solution

### Step 1: Check Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Find your OAuth 2.0 Client ID (the one used for Supabase)
4. Check if it's **disabled** - if yes, enable it
5. Verify **Authorized redirect URIs** include:
   ```
   https://<your-supabase-project>.supabase.co/auth/v1/callback
   https://<your-vercel-domain>.vercel.app/auth/v1/callback
   ```

### Step 2: Update Supabase OAuth Settings

1. Go to [Supabase Dashboard](https://app.supabase.com/)
2. Select your project: `sdclmjzsepnxuhhruazg`
3. Navigate to **Authentication** → **Providers**
4. Click on **Google**
5. Verify/Update:
   - **Client ID** (from Google Cloud Console)
   - **Client Secret** (from Google Cloud Console)
   - **Authorized Client IDs** (optional, for additional security)
6. Click **Save**

### Step 3: Add Vercel Domain to Supabase Site URL

1. In Supabase Dashboard → **Settings** → **API**
2. Update **Site URL** to your Vercel production URL:
   ```
   https://your-app-name.vercel.app
   ```
3. Add to **Redirect URLs**:
   ```
   https://your-app-name.vercel.app/**
   https://your-app-name.vercel.app/auth/callback
   ```

### Step 4: Create New OAuth Client (If Current One is Problematic)

If the current OAuth client is disabled and can't be re-enabled:

1. **Create New OAuth Client in Google Cloud Console:**
   ```bash
   # Go to: APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID
   # Application type: Web application
   # Name: "TailorJob Production"
   # Authorized redirect URIs:
   #   - https://sdclmjzsepnxuhhruazg.supabase.co/auth/v1/callback
   #   - https://your-vercel-app.vercel.app/auth/callback
   ```

2. **Update Supabase with New Credentials:**
   - Copy new Client ID and Client Secret
   - Update in Supabase → Authentication → Providers → Google

### Step 5: Environment Variables

Ensure Vercel has the correct environment variables:

```bash
# In Vercel Dashboard → Settings → Environment Variables
VITE_SUPABASE_URL=https://sdclmjzsepnxuhhruazg.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=eyJhbGci...
VITE_SUPABASE_PROJECT_ID=sdclmjzsepnxuhhruazg
```

### Step 6: Alternative - Disable Google OAuth Temporarily

If you don't want Google OAuth for testing:

1. In Supabase Dashboard → Authentication → Providers
2. Disable **Google** provider
3. Use **Email/Password** authentication instead

## Quick Fix Commands

```bash
# 1. Check current Supabase project
echo "Project: sdclmjzsepnxuhhruazg"
echo "URL: https://sdclmjzsepnxuhhruazg.supabase.co"

# 2. Redeploy on Vercel after fixing OAuth
vercel --prod

# 3. Test locally first
npm run dev
# Try Google Sign-In on localhost:5173
```

## Testing After Fix

1. Clear browser cache/cookies
2. Try Google Sign-In again
3. Check browser console for any errors
4. Verify redirect URL in address bar during OAuth flow

## Common Issues

**Issue**: "redirect_uri_mismatch"
- **Fix**: Add exact redirect URI to Google Cloud Console

**Issue**: Still getting "disabled_client"
- **Fix**: Create completely new OAuth client and update Supabase

**Issue**: Works locally but not on Vercel
- **Fix**: Ensure Vercel domain is in Google Cloud authorized URIs

## Notes

- Google OAuth requires **verified domain** for production apps
- During development, you can use test users in Google Cloud Console
- Supabase handles OAuth flow automatically once configured correctly