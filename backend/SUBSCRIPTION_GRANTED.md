# Pro Subscription Granted

## Summary
Successfully granted Pro subscription to `tailorjobai@gmail.com`

## Details
- **User ID**: `12601009-4532-4c5f-89f5-1f1685d13fea`
- **Email**: `tailorjobai@gmail.com`
- **Subscription Tier**: Pro
- **Status**: Active
- **Valid Until**: 2026-12-07
- **PayPal Subscription ID**: `MANUAL_PRO_12601009` (manual/complimentary)

## Pro Benefits Activated
✅ Unlimited CV uploads  
✅ Unlimited job matches  
✅ Unlimited CV tailoring  
✅ Unlimited PDF exports  
✅ Premium v5 matcher with enhanced discipline matching  

## Scripts Created
- `grant_pro_subscription.py` - Grant pro by email (requires user to exist)
- `grant_pro_by_id.py` - Grant pro by user ID
- `list_users.py` - List all users in database
- `find_user_by_email.py` - Find user by email
- `update_user_email.py` - Update user's email in profiles table

## Usage
To grant pro subscription to another user:
```bash
cd backend
source venv/bin/activate

# Method 1: By email (if user exists)
python grant_pro_subscription.py

# Method 2: By user ID
python list_users.py  # Get user ID
python grant_pro_by_id.py <user_id>
```

## Date
2025-12-07