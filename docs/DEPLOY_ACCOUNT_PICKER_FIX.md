# Deploy Account Picker Fix to Vercel

## Problem
On https://tailorjob.vercel.app/, Google OAuth auto-selects TomerCohen95@gmail.com without showing account picker.

## Solution Already Implemented
The code fix is already committed:
- `src/pages/Login.tsx` - Added `prompt: 'select_account'`
- `src/pages/Signup.tsx` - Added `prompt: 'select_account'`

## Step 1: Deploy to Vercel

### Option A: Automatic Deployment (Recommended)
```bash
# Push to main branch - Vercel auto-deploys
git checkout main
git merge user/tomercohen/oauth-account-selection-fix
git push origin main

# Vercel will auto-deploy in 1-2 minutes
# Check: https://vercel.com/dashboard
```

### Option B: Manual Deployment via Vercel CLI
```bash
# Install Vercel CLI if not installed
npm i -g vercel

# Deploy to production
vercel --prod

# Wait for deployment to complete
```

### Option C: Redeploy from Vercel Dashboard
1. Go to: https://vercel.com/dashboard
2. Find "tailorjob" project
3. Click on latest deployment
4. Click "Redeploy" button
5. Wait for deployment to complete

## Step 2: Clear Browser Cache for tailorjob.vercel.app

**CRITICAL**: Even after deploying, your browser cache will keep auto-selecting the wrong account.

### Chrome/Edge:
1. Go to: https://tailorjob.vercel.app/
2. Press `Cmd+Shift+Delete` (Mac) or `Ctrl+Shift+Delete` (Windows)
3. Select:
   - ✅ Cookies and other site data
   - ✅ Cached images and files
   - Time range: **Last 24 hours** or **All time**
4. Click "Clear data"

### Alternative - Incognito/Private Window:
1. Open new Incognito window: `Cmd+Shift+N` (Mac) or `Ctrl+Shift+N` (Windows)
2. Go to: https://tailorjob.vercel.app/login
3. Click "Sign in with Google"
4. Account picker should appear!

### Alternative - Clear Google Sessions:
1. Go to: https://myaccount.google.com/permissions
2. Find "TailorJob" or your app
3. Click "Remove access"
4. Go back to https://tailorjob.vercel.app/login
5. Try again - account picker should appear

## Step 3: Test

1. Clear browser cache (Step 2 above)
2. Go to: https://tailorjob.vercel.app/login
3. Click "Sign in with Google"
4. **Expected**: Google account picker appears
5. **Expected**: You can choose which account to use
6. **Expected**: Selected account signs in successfully

## If Still Auto-Selecting Wrong Account

### Nuclear Option - Clear ALL Google OAuth Data:
```bash
# Open Developer Console on https://tailorjob.vercel.app/
# Press F12 → Console tab → Paste this:

// Clear all localStorage
localStorage.clear();

// Clear all sessionStorage  
sessionStorage.clear();

// Clear all cookies
document.cookie.split(";").forEach(function(c) { 
  document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
});

// Reload page
location.reload();
```

Then:
1. Sign out from all Google accounts in browser
2. Go to: https://accounts.google.com/SignOutOptions
3. Click "Sign out of all accounts"
4. Close ALL browser windows
5. Open new browser window
6. Go to: https://tailorjob.vercel.app/login
7. Try Google Sign-In again

## Verify Deployment

Check if the fix is deployed:
```bash
# View deployed code on Vercel
curl https://tailorjob.vercel.app/_next/static/chunks/pages/login-[hash].js | grep "select_account"

# Should output: prompt: 'select_account'
```

Or check in browser:
1. Go to: https://tailorjob.vercel.app/login
2. Open Developer Console (F12)
3. Go to "Sources" tab
4. Search for "login" in file tree
5. Find the `handleGoogleSignIn` function
6. Verify it contains: `queryParams: { prompt: 'select_account' }`

## Timeline

- **Code changes**: ✅ Already committed
- **Deploy to Vercel**: ~2-5 minutes
- **Clear browser cache**: ~1 minute
- **Test**: ~1 minute

**Total**: ~10 minutes to fully resolve

## Quick Commands Summary

```bash
# 1. Deploy (if using Git push)
git checkout main
git merge user/tomercohen/oauth-account-selection-fix
git push origin main

# 2. Wait for Vercel auto-deploy (~2 min)

# 3. Open incognito window and test
# Cmd+Shift+N (Mac) or Ctrl+Shift+N (Windows)
# Navigate to: https://tailorjob.vercel.app/login