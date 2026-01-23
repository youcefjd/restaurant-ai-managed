-- Audit logging migration
-- Run this in Supabase SQL Editor
-- Tracks all admin actions for security and compliance

-- ============================================
-- AUDIT LOGS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),

    -- Who performed the action
    admin_id INTEGER REFERENCES auth.users(id),
    admin_email TEXT,

    -- What action was performed
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,  -- 'restaurant', 'order', 'commission', etc.
    resource_id TEXT,              -- ID of the affected resource

    -- Before and after state (for changes)
    old_value JSONB,
    new_value JSONB,

    -- Request context
    ip_address TEXT,
    user_agent TEXT,

    -- Additional context
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_admin ON audit_logs(admin_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

-- ============================================
-- AUDIT LOG FUNCTIONS
-- ============================================

-- Helper function to insert audit logs
CREATE OR REPLACE FUNCTION log_admin_action(
    p_admin_email TEXT,
    p_action TEXT,
    p_resource_type TEXT,
    p_resource_id TEXT DEFAULT NULL,
    p_old_value JSONB DEFAULT NULL,
    p_new_value JSONB DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS INTEGER AS $$
DECLARE
    v_id INTEGER;
BEGIN
    INSERT INTO audit_logs (admin_email, action, resource_type, resource_id, old_value, new_value, metadata)
    VALUES (p_admin_email, p_action, p_resource_type, p_resource_id, p_old_value, p_new_value, p_metadata)
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;


-- ============================================
-- EXAMPLE AUDIT QUERIES
-- ============================================

-- Get recent admin activity:
-- SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 100;

-- Get all actions by a specific admin:
-- SELECT * FROM audit_logs WHERE admin_email = 'admin@example.com' ORDER BY timestamp DESC;

-- Get all changes to a specific restaurant:
-- SELECT * FROM audit_logs WHERE resource_type = 'restaurant' AND resource_id = '123';

-- Get commission changes:
-- SELECT * FROM audit_logs WHERE action = 'commission_update' ORDER BY timestamp DESC;
