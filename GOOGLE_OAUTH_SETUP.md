# Google OAuth Setup Guide for TailorJob.ai

This guide provides step-by-step instructions to configure free Google signup/signin for your application.

## Prerequisites

- Google account
- Supabase project (already created: `izerdjlpdjnorczyxjva`)
- Node.js and npm installed

## Architecture Overview

```
User Browser
    ↓
React App (Login/Signup pages)
    ↓
Supabase Auth (signInWithOAuth)
    ↓
Google OAuth 2.0
    ↓
Redirect back to Supabase
    ↓
Redirect to /dashboard
```

## Step 1: Create Google Cloud Console Project

### Manual Steps (Google Cloud Console)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project details:
   - **Project name**: `TailorJob` (or your preferred name)
   - **Organization**: (optional)
4. Click "Create"
5. Wait for project creation and select it

## Step 2: Enable Google+ API

### Manual Steps

1. In Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google+ API"
3. Click on it and click "Enable"

## Step 3: Configure OAuth Consent Screen

### Manual Steps

1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose **External** user type (for public apps)
3. Click "Create"
4. Fill in required fields:
   - **App name**: `TailorJob.ai`
   - **User support email**: your email
   - **App logo**: (optional, upload your logo)
   - **Application home page**: `https://izerdjlpdjnorczyxjva.supabase.co`
   - **Authorized domains**: 
     - `supabase.co`
     - (add your custom domain if you have one)
   - **Developer contact email**: your email
5. Click "Save and Continue"
6. **Scopes**: Click "Add or Remove Scopes"
   - Add: `email`, `profile`, `openid` (should be automatically selected)
7. Click "Save and Continue"
8. **Test users**: (optional for testing phase)
   - Add your email and test user emails
9. Click "Save and Continue"
10. Review and click "Back to Dashboard"

## Step 4: Create OAuth 2.0 Credentials

### Manual Steps

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Choose **Web application**
4. Configure:
   - **Name**: `TailorJob Web Client`
   - **Authorized JavaScript origins**:
     - `http://localhost:5173` (for development)
     - `https://izerdjlpdjnorczyxjva.supabase.co`
     - (add your production domain when ready)
   - **Authorized redirect URIs**:
     - `https://izerdjlpdjnorczyxjva.supabase.co/auth/v1/callback`
     - `http://localhost:54321/auth/v1/callback` (for local Supabase)
5. Click "Create"
6. **IMPORTANT**: Copy and save:
   - **Client ID**: `YOUR_GOOGLE_CLIENT_ID`
   - **Client Secret**: `YOUR_GOOGLE_CLIENT_SECRET`

## Step 5: Install and Configure Supabase CLI

### CLI Commands

```bash
# Check if Supabase CLI is installed
npx supabase --version

# If not installed, install globally
npm install -g supabase

# Or use via npx (recommended)
npx supabase --version
```

### Link to Remote Project

```bash
# Login to Supabase
npx supabase login

# Link to your remote project
npx supabase link --project-ref izerdjlpdjnorczyxjva

# When prompted, you may need your database password
# You can find it in your Supabase dashboard under Project Settings → Database
```

## Step 6: Configure Google OAuth in Supabase

### Option A: Using Supabase Dashboard (Recommended for First Setup)

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project: `izerdjlpdjnorczyxjva`
3. Go to "Authentication" → "Providers"
4. Find "Google" and toggle it ON
5. Enter your credentials:
   - **Client ID**: (paste from Step 4)
   - **Client Secret**: (paste from Step 4)
6. Click "Save"

### Option B: Using CLI (Alternative)

```bash
# Get current auth config
npx supabase secrets list

# Set Google OAuth secrets
npx supabase secrets set GOOGLE_CLIENT_ID="YOUR_GOOGLE_CLIENT_ID"
npx supabase secrets set GOOGLE_CLIENT_SECRET="YOUR_GOOGLE_CLIENT_SECRET"
```

## Step 7: Update Local Configuration

### Update supabase/config.toml

Add the following auth configuration:

```toml
[auth]
enabled = true
site_url = "http://localhost:5173"
additional_redirect_urls = ["https://izerdjlpdjnorczyxjva.supabase.co"]

[auth.external.google]
enabled = true
client_id = "env(GOOGLE_CLIENT_ID)"
secret = "env(GOOGLE_CLIENT_SECRET)"
redirect_uri = "https://izerdjlpdjnorczyxjva.supabase.co/auth/v1/callback"
```

### Create .env.local (for local secrets if needed)

```bash
# Create a local environment file (do not commit to git)
touch .env.local

# Add to .gitignore if not already there
echo ".env.local" >> .gitignore
```

## Step 8: Test the OAuth Flow

### Testing Steps

1. Start your dev server (already running):
   ```bash
   npm run dev
   ```

2. Open browser to `http://localhost:5173`

3. Navigate to `/signup` or `/login`

4. Click "Sign up with Google" or "Sign in with Google"

5. Expected flow:
   - Redirects to Google login
   - Shows consent screen (first time)
   - Redirects back to your app
   - Creates user in Supabase Auth
   - Redirects to `/dashboard`

### Verify in Supabase Dashboard

1. Go to "Authentication" → "Users"
2. Check if new user appears after successful signup
3. Verify user metadata includes Google profile info

## Step 9: Production Checklist

### Before Going Live

- [ ] Update OAuth consent screen to "Published" status
- [ ] Add production domain to authorized origins
- [ ] Add production redirect URI to Google Cloud Console
- [ ] Update `site_url` in Supabase project settings
- [ ] Test OAuth flow on production domain
- [ ] Set up email templates in Supabase (optional)
- [ ] Configure rate limiting (optional)

### Environment Variables for Production

```bash
# Production .env
VITE_SUPABASE_URL="https://izerdjlpdjnorczyxjva.supabase.co"
VITE_SUPABASE_PUBLISHABLE_KEY="your-anon-key"
```

## Troubleshooting

### Error: "redirect_uri_mismatch"

- Check that redirect URI in Google Cloud Console exactly matches Supabase callback URL
- Format: `https://YOUR_PROJECT_REF.supabase.co/auth/v1/callback`

### Error: "Access blocked: This app's request is invalid"

- Ensure OAuth consent screen is properly configured
- Verify that you've added required scopes (email, profile, openid)
- Check that authorized domains include `supabase.co`

### Error: "invalid_client"

- Verify Client ID and Client Secret are correct
- Check they're properly saved in Supabase dashboard

### Users Not Being Created

- Check Supabase logs: Dashboard → Logs → Auth
- Verify Google provider is enabled in Supabase
- Check browser console for JavaScript errors

## Security Best Practices

1. **Never commit secrets**: Keep `.env` and `.env.local` in `.gitignore`
2. **Use environment variables**: Store credentials as env vars, not in code
3. **Restrict domains**: Only add necessary domains to authorized origins
4. **Monitor usage**: Regularly check Google Cloud Console quotas
5. **Rotate secrets**: Periodically update OAuth credentials

## Cost Considerations

- **Google OAuth 2.0**: Free for standard authentication
- **Supabase Auth**: Free tier includes 50,000 monthly active users
- **No credit card required** for basic setup

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Supabase CLI Reference](https://supabase.com/docs/reference/cli)

## Summary of CLI Commands

```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
npx supabase login

# Link project
npx supabase link --project-ref izerdjlpdjnorczyxjva

# Check status
npx supabase status

# View secrets (if configured via CLI)
npx supabase secrets list

# Set secrets (alternative to dashboard)
npx supabase secrets set GOOGLE_CLIENT_ID="your-client-id"
npx supabase secrets set GOOGLE_CLIENT_SECRET="your-client-secret"
```

## Next Steps After Setup

1. Test the complete authentication flow
2. Implement user profile management
3. Add role-based access control (if needed)
4. Set up email notifications (optional)
5. Configure session timeout settings
6. Add social login for other providers (GitHub, etc.)