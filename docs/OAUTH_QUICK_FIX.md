# Quick Fix: Google OAuth "disabled_client" on Vercel

## Immediate Actions

### Option 1: Fix Google OAuth (Recommended)

1. **Go to Google Cloud Console**
   - URL: https://console.cloud.google.com/apis/credentials
   - Find your OAuth 2.0 Client ID
   - Check if **disabled** → Enable it

2. **Add Vercel URL to Authorized Redirect URIs**
   ```
   https://sdclmjzsepnxuhhruazg.supabase.co/auth/v1/callback
   https://your-vercel-app.vercel.app/auth/callback
   ```

3. **Update Supabase**
   - Go to: https://app.supabase.com/project/sdclmjzsepnxuhhruazg/auth/providers
   - Check Google provider credentials are correct
   - Save changes

4. **Redeploy Vercel**
   ```bash
   vercel --prod
   ```

### Option 2: Disable Google OAuth Temporarily

If you just want to test without Google OAuth:

1. **Supabase Dashboard** → Authentication → Providers
2. **Disable** Google provider
3. Use Email/Password authentication instead

### Option 3: Use Email Authentication Instead

Your app already supports email/password - just skip Google Sign-In:

1. Click "Sign up" instead of "Sign in with Google"
2. Create account with email/password
3. Continue using the app

## Check Current Status

```bash
# View your Supabase project
echo "Project ID: sdclmjzsepnxuhhruazg"
echo "Dashboard: https://app.supabase.com/project/sdclmjzsepnxuhhruazg"

# Check Vercel deployment
vercel ls
```

## Why This Happens

- Google OAuth client was disabled in Google Cloud Console
- OR redirect URIs don't include your Vercel domain
- OR Supabase has wrong/expired OAuth credentials

## Full Documentation

See [`FIXING_GOOGLE_OAUTH_VERCEL.md`](./FIXING_GOOGLE_OAUTH_VERCEL.md) for complete step-by-step guide.