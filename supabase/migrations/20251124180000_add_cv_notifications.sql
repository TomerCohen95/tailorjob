-- Add notifications table for CV parsing completion
CREATE TABLE IF NOT EXISTS cv_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    cv_id UUID NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('cv_parsed', 'cv_error')),
    message TEXT NOT NULL,
    read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Index for efficient querying
    CONSTRAINT cv_notifications_user_id_idx UNIQUE (user_id, cv_id, type)
);

-- Create index for faster queries by user
CREATE INDEX IF NOT EXISTS cv_notifications_user_id_idx ON cv_notifications(user_id, read, created_at DESC);

-- Enable RLS
ALTER TABLE cv_notifications ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own notifications
CREATE POLICY "Users can view their own notifications"
    ON cv_notifications FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Backend can insert notifications (we'll use service role)
CREATE POLICY "Service role can insert notifications"
    ON cv_notifications FOR INSERT
    WITH CHECK (true);

-- Policy: Users can update their own notifications (mark as read)
CREATE POLICY "Users can update their own notifications"
    ON cv_notifications FOR UPDATE
    USING (auth.uid() = user_id);

-- Policy: Users can delete their own notifications
CREATE POLICY "Users can delete their own notifications"
    ON cv_notifications FOR DELETE
    USING (auth.uid() = user_id);