-- Migration: Add PayPal subscription and payment tables
-- Created: 2025-11-30
-- Description: Adds subscriptions, payments, usage_tracking, and webhook_events tables for PayPal integration

-- ============================================================================
-- SUBSCRIPTIONS TABLE
-- ============================================================================
-- Stores user subscription information linked to PayPal subscriptions

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- PayPal Data
    paypal_subscription_id TEXT UNIQUE NOT NULL,
    paypal_plan_id TEXT NOT NULL,
    paypal_payer_id TEXT,
    
    -- Subscription Details
    tier TEXT NOT NULL CHECK (tier IN ('free', 'basic', 'pro', 'enterprise')),
    status TEXT NOT NULL CHECK (status IN ('active', 'cancelled', 'expired', 'suspended', 'pending')),
    
    -- Billing
    amount_decimal NUMERIC(10,2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    billing_cycle TEXT NOT NULL CHECK (billing_cycle IN ('monthly', 'yearly')),
    
    -- Dates
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    trial_end TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT subscriptions_user_id_unique UNIQUE(user_id)
);

-- Indexes for subscriptions
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_paypal_id ON subscriptions(paypal_subscription_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_tier ON subscriptions(tier);
CREATE INDEX idx_subscriptions_period_end ON subscriptions(current_period_end);

-- ============================================================================
-- PAYMENTS TABLE
-- ============================================================================
-- Stores individual payment transactions

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,
    
    -- PayPal Data
    paypal_payment_id TEXT UNIQUE NOT NULL,
    paypal_order_id TEXT,
    
    -- Payment Details
    amount_decimal NUMERIC(10,2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    
    -- Type
    payment_type TEXT NOT NULL CHECK (payment_type IN ('subscription', 'one_time')),
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for payments
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_subscription_id ON payments(subscription_id);
CREATE INDEX idx_payments_paypal_id ON payments(paypal_payment_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_created_at ON payments(created_at);

-- ============================================================================
-- USAGE TRACKING TABLE
-- ============================================================================
-- Tracks user feature usage per billing period

CREATE TABLE usage_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Period
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    
    -- Usage Counters
    cvs_uploaded INTEGER NOT NULL DEFAULT 0,
    jobs_matched INTEGER NOT NULL DEFAULT 0,
    cvs_tailored INTEGER NOT NULL DEFAULT 0,
    pdfs_exported INTEGER NOT NULL DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT usage_tracking_user_period_unique UNIQUE(user_id, period_start)
);

-- Indexes for usage_tracking
CREATE INDEX idx_usage_tracking_user_id ON usage_tracking(user_id);
CREATE INDEX idx_usage_tracking_period ON usage_tracking(period_start, period_end);

-- ============================================================================
-- WEBHOOK EVENTS TABLE
-- ============================================================================
-- Stores PayPal webhook events for audit and retry

CREATE TABLE webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- PayPal Data
    paypal_event_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,
    resource_type TEXT,
    
    -- Payload (full webhook body)
    payload JSONB NOT NULL,
    
    -- Processing Status
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    processed_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for webhook_events
CREATE INDEX idx_webhook_events_paypal_id ON webhook_events(paypal_event_id);
CREATE INDEX idx_webhook_events_type ON webhook_events(event_type);
CREATE INDEX idx_webhook_events_processed ON webhook_events(processed);
CREATE INDEX idx_webhook_events_created_at ON webhook_events(created_at);

-- ============================================================================
-- UPDATE PROFILES TABLE
-- ============================================================================
-- Add subscription fields to existing profiles table

ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS subscription_tier TEXT NOT NULL DEFAULT 'free' 
    CHECK (subscription_tier IN ('free', 'basic', 'pro', 'enterprise'));

ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS subscription_status TEXT NOT NULL DEFAULT 'active'
    CHECK (subscription_status IN ('active', 'cancelled', 'expired', 'suspended', 'pending'));

CREATE INDEX IF NOT EXISTS idx_profiles_subscription_tier ON profiles(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_profiles_subscription_status ON profiles(subscription_status);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payments_updated_at
    BEFORE UPDATE ON payments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_usage_tracking_updated_at
    BEFORE UPDATE ON usage_tracking
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_events ENABLE ROW LEVEL SECURITY;

-- Subscriptions: Users can only access their own subscriptions
CREATE POLICY "Users can view their own subscriptions"
    ON subscriptions FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own subscriptions"
    ON subscriptions FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own subscriptions"
    ON subscriptions FOR UPDATE
    USING (user_id = auth.uid());

-- Payments: Users can only access their own payments
CREATE POLICY "Users can view their own payments"
    ON payments FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own payments"
    ON payments FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Usage Tracking: Users can only access their own usage
CREATE POLICY "Users can view their own usage"
    ON usage_tracking FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own usage"
    ON usage_tracking FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own usage"
    ON usage_tracking FOR UPDATE
    USING (user_id = auth.uid());

-- Webhook Events: Only backend service can access (no user access)
-- Backend uses service role key, which bypasses RLS

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get current period usage for a user
CREATE OR REPLACE FUNCTION get_current_usage(p_user_id UUID)
RETURNS TABLE (
    cvs_uploaded INTEGER,
    jobs_matched INTEGER,
    cvs_tailored INTEGER,
    pdfs_exported INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ut.cvs_uploaded,
        ut.jobs_matched,
        ut.cvs_tailored,
        ut.pdfs_exported
    FROM usage_tracking ut
    WHERE ut.user_id = p_user_id
      AND ut.period_start <= NOW()
      AND ut.period_end > NOW()
    LIMIT 1;
    
    -- If no record exists for current period, return zeros
    IF NOT FOUND THEN
        RETURN QUERY SELECT 0, 0, 0, 0;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to initialize usage for new billing period
CREATE OR REPLACE FUNCTION initialize_usage_period(
    p_user_id UUID,
    p_period_start TIMESTAMPTZ,
    p_period_end TIMESTAMPTZ
) RETURNS UUID AS $$
DECLARE
    v_usage_id UUID;
BEGIN
    INSERT INTO usage_tracking (
        user_id,
        period_start,
        period_end,
        cvs_uploaded,
        jobs_matched,
        cvs_tailored,
        pdfs_exported
    ) VALUES (
        p_user_id,
        p_period_start,
        p_period_end,
        0, 0, 0, 0
    )
    ON CONFLICT (user_id, period_start) DO NOTHING
    RETURNING id INTO v_usage_id;
    
    RETURN v_usage_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to increment usage counter
CREATE OR REPLACE FUNCTION increment_usage(
    p_user_id UUID,
    p_feature TEXT,
    p_amount INTEGER DEFAULT 1
) RETURNS BOOLEAN AS $$
DECLARE
    v_period_start TIMESTAMPTZ;
    v_period_end TIMESTAMPTZ;
BEGIN
    -- Get current period (start of month to end of month)
    v_period_start := date_trunc('month', NOW());
    v_period_end := (date_trunc('month', NOW()) + interval '1 month');
    
    -- Ensure usage record exists for current period
    INSERT INTO usage_tracking (
        user_id,
        period_start,
        period_end,
        cvs_uploaded,
        jobs_matched,
        cvs_tailored,
        pdfs_exported
    ) VALUES (
        p_user_id,
        v_period_start,
        v_period_end,
        0, 0, 0, 0
    )
    ON CONFLICT (user_id, period_start) DO NOTHING;
    
    -- Increment the appropriate counter
    CASE p_feature
        WHEN 'cv_upload' THEN
            UPDATE usage_tracking
            SET cvs_uploaded = cvs_uploaded + p_amount
            WHERE user_id = p_user_id
              AND period_start = v_period_start;
        WHEN 'job_match' THEN
            UPDATE usage_tracking
            SET jobs_matched = jobs_matched + p_amount
            WHERE user_id = p_user_id
              AND period_start = v_period_start;
        WHEN 'tailor_cv' THEN
            UPDATE usage_tracking
            SET cvs_tailored = cvs_tailored + p_amount
            WHERE user_id = p_user_id
              AND period_start = v_period_start;
        WHEN 'export_pdf' THEN
            UPDATE usage_tracking
            SET pdfs_exported = pdfs_exported + p_amount
            WHERE user_id = p_user_id
              AND period_start = v_period_start;
    END CASE;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- DEFAULT FREE SUBSCRIPTIONS
-- ============================================================================
-- Create free tier subscriptions for all existing users

INSERT INTO subscriptions (
    user_id,
    paypal_subscription_id,
    paypal_plan_id,
    tier,
    status,
    amount_decimal,
    currency,
    billing_cycle,
    current_period_start,
    current_period_end
)
SELECT 
    id as user_id,
    'free_' || id::text as paypal_subscription_id,
    'free_plan' as paypal_plan_id,
    'free' as tier,
    'active' as status,
    0.00 as amount_decimal,
    'USD' as currency,
    'monthly' as billing_cycle,
    NOW() as current_period_start,
    NOW() + interval '1 month' as current_period_end
FROM auth.users
ON CONFLICT (user_id) DO NOTHING;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE subscriptions IS 'User subscription data linked to PayPal subscriptions';
COMMENT ON TABLE payments IS 'Individual payment transactions for audit trail';
COMMENT ON TABLE usage_tracking IS 'Feature usage tracking per billing period for tier limits';
COMMENT ON TABLE webhook_events IS 'PayPal webhook events for processing and audit';

COMMENT ON COLUMN subscriptions.tier IS 'Subscription tier: free, basic, pro, enterprise';
COMMENT ON COLUMN subscriptions.status IS 'Subscription status: active, cancelled, expired, suspended, pending';
COMMENT ON COLUMN subscriptions.current_period_start IS 'Start of current billing period';
COMMENT ON COLUMN subscriptions.current_period_end IS 'End of current billing period (renewal date)';

COMMENT ON FUNCTION get_current_usage IS 'Get current billing period usage for a user';
COMMENT ON FUNCTION increment_usage IS 'Increment usage counter for a feature';
COMMENT ON FUNCTION initialize_usage_period IS 'Initialize usage tracking for new billing period';