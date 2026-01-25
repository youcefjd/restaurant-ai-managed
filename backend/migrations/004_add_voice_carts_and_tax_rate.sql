-- Migration: Add voice_carts table and tax_rate column
-- This migration adds persistent cart storage for voice calls
-- and allows restaurants to configure their own tax rate.

-- Voice carts table for persistent cart storage
CREATE TABLE IF NOT EXISTS voice_carts (
    call_id TEXT PRIMARY KEY,
    restaurant_id INTEGER REFERENCES restaurant_accounts(id) ON DELETE CASCADE,
    items JSONB DEFAULT '[]'::jsonb,
    customer_phone TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '2 hours')
);

-- Index for efficient cleanup of expired carts
CREATE INDEX IF NOT EXISTS idx_voice_carts_expires ON voice_carts(expires_at);

-- Index for looking up carts by restaurant
CREATE INDEX IF NOT EXISTS idx_voice_carts_restaurant ON voice_carts(restaurant_id);

-- Add tax_rate column to restaurant_accounts (default 8%)
ALTER TABLE restaurant_accounts
ADD COLUMN IF NOT EXISTS tax_rate DECIMAL(5,4) DEFAULT 0.0800;

-- Comment for documentation
COMMENT ON COLUMN restaurant_accounts.tax_rate IS 'Tax rate as decimal (e.g., 0.0800 for 8%)';
COMMENT ON TABLE voice_carts IS 'Temporary cart storage for voice ordering calls';
COMMENT ON COLUMN voice_carts.expires_at IS 'Carts automatically expire after 2 hours';

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_voice_cart_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
DROP TRIGGER IF EXISTS voice_carts_updated_at ON voice_carts;
CREATE TRIGGER voice_carts_updated_at
    BEFORE UPDATE ON voice_carts
    FOR EACH ROW
    EXECUTE FUNCTION update_voice_cart_updated_at();

-- Function to clean up expired carts (can be called periodically)
CREATE OR REPLACE FUNCTION cleanup_expired_voice_carts()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM voice_carts WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
