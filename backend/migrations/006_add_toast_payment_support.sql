-- Migration: Add Toast POS integration and DTMF payment support
-- This adds fields for Toast POS sync, DTMF card collection, and payment sessions

-- =============================================================================
-- Toast integration fields for restaurant_accounts
-- =============================================================================
ALTER TABLE restaurant_accounts
ADD COLUMN IF NOT EXISTS toast_enabled BOOLEAN DEFAULT FALSE;

ALTER TABLE restaurant_accounts
ADD COLUMN IF NOT EXISTS toast_client_id VARCHAR(255);

ALTER TABLE restaurant_accounts
ADD COLUMN IF NOT EXISTS toast_client_secret_encrypted TEXT;

ALTER TABLE restaurant_accounts
ADD COLUMN IF NOT EXISTS toast_restaurant_guid VARCHAR(255);

ALTER TABLE restaurant_accounts
ADD COLUMN IF NOT EXISTS toast_encryption_key_id VARCHAR(100);

ALTER TABLE restaurant_accounts
ADD COLUMN IF NOT EXISTS toast_public_key TEXT;

COMMENT ON COLUMN restaurant_accounts.toast_enabled IS 'Whether Toast POS integration is enabled for this restaurant';
COMMENT ON COLUMN restaurant_accounts.toast_client_id IS 'Toast API client ID for OAuth2 authentication';
COMMENT ON COLUMN restaurant_accounts.toast_client_secret_encrypted IS 'Encrypted Toast API client secret';
COMMENT ON COLUMN restaurant_accounts.toast_restaurant_guid IS 'Toast restaurant GUID for API calls';
COMMENT ON COLUMN restaurant_accounts.toast_encryption_key_id IS 'Key ID used for card encryption with Toast';
COMMENT ON COLUMN restaurant_accounts.toast_public_key IS 'Toast public key for card data encryption';

-- =============================================================================
-- Toast item mapping for menu_items
-- =============================================================================
ALTER TABLE menu_items
ADD COLUMN IF NOT EXISTS toast_item_guid VARCHAR(255);

COMMENT ON COLUMN menu_items.toast_item_guid IS 'Manual mapping to Toast menu item GUID';

CREATE INDEX IF NOT EXISTS idx_menu_items_toast_guid ON menu_items(toast_item_guid) WHERE toast_item_guid IS NOT NULL;

-- =============================================================================
-- Payment fields for orders
-- =============================================================================
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS toast_order_guid VARCHAR(255);

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS toast_payment_uuid VARCHAR(255);

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS external_payment_provider VARCHAR(50);

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS card_last_four VARCHAR(4);

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS payment_collected_via VARCHAR(20);

COMMENT ON COLUMN orders.toast_order_guid IS 'Toast POS order GUID for synced orders';
COMMENT ON COLUMN orders.toast_payment_uuid IS 'Toast payment UUID for card payments';
COMMENT ON COLUMN orders.external_payment_provider IS 'Payment provider: toast, stripe, or pay_at_pickup';
COMMENT ON COLUMN orders.card_last_four IS 'Last 4 digits of card used for payment';
COMMENT ON COLUMN orders.payment_collected_via IS 'How payment was collected: dtmf, web, or terminal';

CREATE INDEX IF NOT EXISTS idx_orders_toast_guid ON orders(toast_order_guid) WHERE toast_order_guid IS NOT NULL;

-- =============================================================================
-- Payment sessions table for DTMF card collection state machine
-- =============================================================================
CREATE TABLE IF NOT EXISTS payment_sessions (
    id SERIAL PRIMARY KEY,
    call_id VARCHAR(255) UNIQUE NOT NULL,
    restaurant_id INTEGER NOT NULL REFERENCES restaurant_accounts(id) ON DELETE CASCADE,
    session_id VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    card_number_encrypted TEXT,
    expiry_encrypted TEXT,
    cvv_hash TEXT,
    amount_cents INTEGER,
    toast_payment_uuid VARCHAR(255),
    stripe_payment_intent_id VARCHAR(255),
    guest_identifier VARCHAR(255),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '10 minutes')
);

COMMENT ON TABLE payment_sessions IS 'Tracks DTMF payment collection state for voice calls';
COMMENT ON COLUMN payment_sessions.call_id IS 'Retell call ID - unique per payment attempt';
COMMENT ON COLUMN payment_sessions.session_id IS 'LLM-generated session ID for cart isolation';
COMMENT ON COLUMN payment_sessions.status IS 'State: pending, collecting_card, collecting_expiry, collecting_cvv, authorizing, authorized, failed, cancelled';
COMMENT ON COLUMN payment_sessions.card_number_encrypted IS 'Encrypted card number (never store plaintext)';
COMMENT ON COLUMN payment_sessions.expiry_encrypted IS 'Encrypted expiry date (MMYY format)';
COMMENT ON COLUMN payment_sessions.cvv_hash IS 'Hashed CVV - only used during authorization, then cleared';
COMMENT ON COLUMN payment_sessions.amount_cents IS 'Payment amount in cents';
COMMENT ON COLUMN payment_sessions.toast_payment_uuid IS 'Toast payment UUID if authorized via Toast';
COMMENT ON COLUMN payment_sessions.stripe_payment_intent_id IS 'Stripe PaymentIntent ID if authorized via Stripe';
COMMENT ON COLUMN payment_sessions.guest_identifier IS 'Guest identifier for Toast API';
COMMENT ON COLUMN payment_sessions.expires_at IS 'Session expires after 10 minutes for security';

CREATE INDEX IF NOT EXISTS idx_payment_sessions_call_id ON payment_sessions(call_id);
CREATE INDEX IF NOT EXISTS idx_payment_sessions_restaurant ON payment_sessions(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_payment_sessions_status ON payment_sessions(status);
CREATE INDEX IF NOT EXISTS idx_payment_sessions_expires ON payment_sessions(expires_at);

-- =============================================================================
-- Function to auto-update payment_sessions.updated_at
-- =============================================================================
CREATE OR REPLACE FUNCTION update_payment_sessions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_payment_sessions_updated_at ON payment_sessions;
CREATE TRIGGER trigger_payment_sessions_updated_at
    BEFORE UPDATE ON payment_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_payment_sessions_updated_at();

-- =============================================================================
-- Function to cleanup expired payment sessions
-- =============================================================================
CREATE OR REPLACE FUNCTION cleanup_expired_payment_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM payment_sessions
    WHERE expires_at < NOW()
    AND status NOT IN ('authorized', 'completed');

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_payment_sessions() IS 'Deletes expired payment sessions that are not authorized';
