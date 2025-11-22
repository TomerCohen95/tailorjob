# Quick Start: Enable Google OAuth (3 Steps)

Your app is already configured! Just need to connect the pieces.

## What's Already Done ✅

- ✅ React app with Google OAuth UI ([`Login.tsx`](src/pages/Login.tsx:32), [`Signup.tsx`](src/pages/Signup.tsx:32))
- ✅ Supabase client configured ([`client.ts`](src/integrations/supabase/client.ts:11))
- ✅ Local config updated ([`config.toml`](supabase/config.toml:1))
- ✅ Supabase CLI installed

## What You Need to Do

### Step 1: Get Google Credentials (5 min)

```bash
# Open Google Cloud Console
open https://console.cloud.google.com/

# Create project → Enable Google+ API → Create OAuth credentials
```

**Need**:
1. Create new project called "TailorJob"
2. Enable Google+ API
3. OAuth consent screen: External, add `supabase.co` as authorized domain
4. Create OAuth Web Client credentials:
   - Redirect URI: `https://izerdjlpdjnorczyxjva.supabase.co/auth/v1/callback`
   - JavaScript origin: `http://localhost:5173`

**Save**:
- Client ID
- Client Secret

### Step 2: Configure Supabase (2 min)

```bash
# Open Supabase Dashboard
open https://supabase.com/dashboard/project/izerdjlpdjnorczyxjva/auth/providers
```

1. Go to Authentication → Providers
2. Enable "Google"
3. Paste Client ID and Client Secret
4. Save

### Step 3: Test (1 min)

```bash
# Dev server should already be running
# Open your app
open http://localhost:5173/signup

# Click "Sign up with Google"
# Authorize with your Google account
# Should redirect to /dashboard
```

## Verify It Works

```bash
# Check Supabase Dashboard → Authentication → Users
# Your Google account should appear there
```

## Quick CLI Reference

```bash
# Login to Supabase (if needed later)
npx supabase login

# Link project (if needed later)
npx supabase link --project-ref izerdjlpdjnorczyxjva

# Check status
npx supabase status
```

## Important URLs

- **Google Cloud Console**: https://console.cloud.google.com/
- **Supabase Dashboard**: https://supabase.com/dashboard/project/izerdjlpdjnorczyxjva
- **Callback URL**: `https://izerdjlpdjnorczyxjva.supabase.co/auth/v1/callback`

## Full Documentation

- [`GOOGLE_OAUTH_SETUP.md`](GOOGLE_OAUTH_SETUP.md) - Detailed step-by-step guide
- [`GOOGLE_OAUTH_CHECKLIST.md`](GOOGLE_OAUTH_CHECKLIST.md) - Complete checklist
- [`setup-oauth-commands.sh`](setup-oauth-commands.sh) - Interactive script

## Troubleshooting

**"redirect_uri_mismatch"**
- Check redirect URI matches exactly: `https://izerdjlpdjnorczyxjva.supabase.co/auth/v1/callback`

**"Access blocked"**
- Add `supabase.co` to authorized domains in OAuth consent screen

**User not created**
- Check Supabase Dashboard → Logs → Auth
- Verify Google provider is enabled

## It's Free! 💰

- Google OAuth: FREE unlimited
- Supabase: FREE up to 50,000 users/month

No credit card needed!

---

**Total time**: ~8 minutes
**Cost**: $0.00
**Result**: Working Google sign-up/sign-in