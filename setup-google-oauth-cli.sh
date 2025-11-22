#!/bin/bash

# Google OAuth Setup via CLI
# Run this after accepting Google Cloud Terms of Service at https://console.cloud.google.com/

set -e  # Exit on error

echo "================================================"
echo "Google OAuth CLI Setup for TailorJob"
echo "================================================"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    if [ -f ~/google-cloud-sdk/bin/gcloud ]; then
        export PATH="$PATH:$HOME/google-cloud-sdk/bin"
    else
        echo "❌ gcloud CLI not found. Please install it first."
        exit 1
    fi
fi

echo "✅ gcloud CLI found"
echo ""

# Variables
PROJECT_ID="tailorjob-$(date +%s)"
PROJECT_NAME="TailorJob"
REDIRECT_URI="https://sdclmjzsepnxuhhruazg.supabase.co/auth/v1/callback"
JAVASCRIPT_ORIGINS="http://localhost:5173,https://sdclmjzsepnxuhhruazg.supabase.co"

echo "📋 Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Project Name: $PROJECT_NAME"
echo "  Redirect URI: $REDIRECT_URI"
echo ""

# Step 1: Create project
echo "Step 1: Creating Google Cloud project..."
if gcloud projects create "$PROJECT_ID" --name="$PROJECT_NAME"; then
    echo "✅ Project created: $PROJECT_ID"
else
    echo "❌ Failed to create project. Have you accepted Terms of Service?"
    echo "   Go to: https://console.cloud.google.com/"
    exit 1
fi
echo ""

# Step 2: Set current project
echo "Step 2: Setting current project..."
gcloud config set project "$PROJECT_ID"
echo "✅ Current project set to: $PROJECT_ID"
echo ""

# Step 3: Enable required APIs
echo "Step 3: Enabling required APIs..."
echo "  - Enabling IAM API..."
gcloud services enable iam.googleapis.com --project="$PROJECT_ID"
echo "  - Enabling Cloud Resource Manager API..."
gcloud services enable cloudresourcemanager.googleapis.com --project="$PROJECT_ID"
echo "  - Enabling Google+ API..."
gcloud services enable plus.googleapis.com --project="$PROJECT_ID"
echo "✅ APIs enabled"
echo ""

# Step 4: OAuth consent screen configuration
echo "Step 4: OAuth Consent Screen"
echo "⚠️  NOTE: OAuth consent screen MUST be configured via web console"
echo "   This cannot be fully automated via CLI for security reasons"
echo ""
echo "   Please complete these steps in browser:"
echo "   1. Go to: https://console.cloud.google.com/apis/credentials/consent?project=$PROJECT_ID"
echo "   2. Choose 'External' user type"
echo "   3. Fill in:"
echo "      - App name: TailorJob.ai"
echo "      - User support email: tailorjobai@gmail.com"
echo "      - Authorized domains: supabase.co"
echo "      - Developer contact: tailorjobai@gmail.com"
echo "   4. Add scopes: email, profile, openid"
echo "   5. Save and Continue through all steps"
echo ""
read -p "Press Enter after completing OAuth consent screen setup..."
echo ""

# Step 5: Create OAuth credentials
echo "Step 5: Creating OAuth 2.0 credentials..."
echo "⚠️  NOTE: OAuth credentials creation also requires web console"
echo ""
echo "   Please complete these steps:"
echo "   1. Go to: https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"
echo "   2. Click 'Create Credentials' → 'OAuth client ID'"
echo "   3. Choose 'Web application'"
echo "   4. Name: TailorJob Web Client"
echo "   5. Authorized JavaScript origins:"
echo "      - http://localhost:5173"
echo "      - https://sdclmjzsepnxuhhruazg.supabase.co"
echo "   6. Authorized redirect URIs:"
echo "      - $REDIRECT_URI"
echo "   7. Click 'Create'"
echo ""
read -p "Press Enter after creating OAuth credentials..."
echo ""

# Prompt for credentials
echo "📝 Please enter your OAuth credentials:"
read -p "Client ID: " CLIENT_ID
read -sp "Client Secret: " CLIENT_SECRET
echo ""
echo ""

if [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_SECRET" ]; then
    echo "❌ Client ID and Secret are required"
    exit 1
fi

# Step 6: Configure in Supabase
echo "Step 6: Configuring Supabase..."
echo "⚠️  Supabase OAuth configuration via CLI is limited"
echo ""
echo "   Please complete manually:"
echo "   1. Go to: https://supabase.com/dashboard/project/sdclmjzsepnxuhhruazg/auth/providers"
echo "   2. Find 'Google' and toggle it ON"
echo "   3. Enter:"
echo "      Client ID: $CLIENT_ID"
echo "      Client Secret: $CLIENT_SECRET"
echo "   4. Click 'Save'"
echo ""
read -p "Press Enter after configuring Supabase..."
echo ""

# Summary
echo "================================================"
echo "✅ Setup Complete!"
echo "================================================"
echo ""
echo "📋 Summary:"
echo "  Google Cloud Project: $PROJECT_ID"
echo "  Client ID: $CLIENT_ID"
echo "  Redirect URI: $REDIRECT_URI"
echo ""
echo "🧪 Test your setup:"
echo "  1. Open: http://localhost:5173/signup"
echo "  2. Click 'Sign up with Google'"
echo "  3. Should redirect to /dashboard"
echo ""
echo "📚 Documentation:"
echo "  - QUICK_START.md"
echo "  - GOOGLE_OAUTH_SETUP.md"
echo "  - GOOGLE_OAUTH_CHECKLIST.md"
echo ""
echo "💰 Cost: \$0.00 (Free up to 50,000 users/month)"
echo ""
echo "================================================"