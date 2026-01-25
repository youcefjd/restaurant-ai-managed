-- Complete Database Schema for Restaurant AI Platform
-- This script creates all tables, indexes, and functions from scratch

-- ============================================
-- CORE TABLES
-- ============================================

-- Restaurant Accounts (Multi-tenant)
CREATE TABLE IF NOT EXISTS restaurant_accounts (
    id SERIAL PRIMARY KEY,
    business_name VARCHAR(255) NOT NULL,
    owner_name VARCHAR(255),
    owner_email VARCHAR(255) NOT NULL UNIQUE,
    owner_phone VARCHAR(20),
    phone VARCHAR(20),
    password_hash VARCHAR(255),

    -- Twilio integration
    twilio_phone_number VARCHAR(20) UNIQUE,

    -- Operating hours
    opening_time VARCHAR(10),
    closing_time VARCHAR(10),
    operating_days JSONB,

    -- Subscription
    subscription_tier VARCHAR(20) NOT NULL DEFAULT 'free',
    subscription_status VARCHAR(20) NOT NULL DEFAULT 'trial',

    -- Stripe integration
    stripe_customer_id VARCHAR(255) UNIQUE,
    stripe_account_id VARCHAR(255) UNIQUE,

    -- Platform settings
    platform_commission_rate NUMERIC(5,2) NOT NULL DEFAULT 10.0,
    commission_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Tax rate (configurable per restaurant)
    tax_rate DECIMAL(5,4) DEFAULT 0.0800,

    -- Trial limits
    trial_ends_at TIMESTAMPTZ,
    trial_order_limit INTEGER NOT NULL DEFAULT 10,
    trial_orders_used INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT check_commission_rate_valid CHECK (platform_commission_rate >= 0 AND platform_commission_rate <= 100)
);

CREATE INDEX IF NOT EXISTS idx_accounts_email ON restaurant_accounts(owner_email);
CREATE INDEX IF NOT EXISTS idx_accounts_subscription ON restaurant_accounts(subscription_status, is_active);
CREATE INDEX IF NOT EXISTS idx_accounts_business_name ON restaurant_accounts(business_name);

-- Restaurants (Physical Locations)
CREATE TABLE IF NOT EXISTS restaurants (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES restaurant_accounts(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255) NOT NULL,
    opening_time TIME NOT NULL,
    closing_time TIME NOT NULL,
    booking_duration_minutes INTEGER NOT NULL DEFAULT 90,
    max_party_size INTEGER NOT NULL DEFAULT 10,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT check_booking_duration_positive CHECK (booking_duration_minutes > 0),
    CONSTRAINT check_max_party_size_positive CHECK (max_party_size > 0)
);

CREATE INDEX IF NOT EXISTS idx_restaurants_account ON restaurants(account_id);
CREATE INDEX IF NOT EXISTS idx_restaurants_name ON restaurants(name);

-- Tables (Restaurant Seating)
CREATE TABLE IF NOT EXISTS tables (
    id SERIAL PRIMARY KEY,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    table_number VARCHAR(20) NOT NULL,
    capacity INTEGER NOT NULL,
    location VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT uq_restaurant_table_number UNIQUE (restaurant_id, table_number),
    CONSTRAINT check_capacity_positive CHECK (capacity > 0)
);

CREATE INDEX IF NOT EXISTS idx_restaurant_active_tables ON tables(restaurant_id, is_active);

-- Customers
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    notes TEXT,
    total_bookings INTEGER NOT NULL DEFAULT 0,
    no_shows INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT check_total_bookings_non_negative CHECK (total_bookings >= 0),
    CONSTRAINT check_no_shows_non_negative CHECK (no_shows >= 0)
);

CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_phone_created ON customers(phone, created_at DESC);

-- Bookings
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    table_id INTEGER NOT NULL REFERENCES tables(id) ON DELETE RESTRICT,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    booking_date TIMESTAMPTZ NOT NULL,
    booking_time TIME NOT NULL,
    party_size INTEGER NOT NULL,
    duration_minutes INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    special_requests TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT check_party_size_positive CHECK (party_size > 0),
    CONSTRAINT check_duration_positive CHECK (duration_minutes > 0)
);

CREATE INDEX IF NOT EXISTS idx_restaurant_date_status ON bookings(restaurant_id, booking_date, status);
CREATE INDEX IF NOT EXISTS idx_customer_bookings ON bookings(customer_id, booking_date);
CREATE INDEX IF NOT EXISTS idx_table_date_time ON bookings(table_id, booking_date, booking_time);
CREATE INDEX IF NOT EXISTS idx_bookings_restaurant_date ON bookings(restaurant_id, booking_date);
CREATE INDEX IF NOT EXISTS idx_bookings_table_date_status ON bookings(table_id, booking_date, status);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES restaurant_accounts(id) ON DELETE CASCADE,
    restaurant_id INTEGER REFERENCES restaurants(id) ON DELETE CASCADE,
    customer_id INTEGER REFERENCES customers(id) ON DELETE RESTRICT,

    -- Order type and timing
    order_type VARCHAR(20) NOT NULL DEFAULT 'takeout',
    order_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    scheduled_time TIMESTAMPTZ,

    -- Delivery info
    delivery_address TEXT,

    -- Order details
    order_items JSONB NOT NULL,
    subtotal INTEGER NOT NULL,
    tax INTEGER NOT NULL DEFAULT 0,
    delivery_fee INTEGER NOT NULL DEFAULT 0,
    total INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    special_instructions TEXT,

    -- Payment fields
    payment_status VARCHAR(20) NOT NULL DEFAULT 'unpaid',
    payment_method VARCHAR(30),
    payment_intent_id VARCHAR(255),

    -- Customer info (denormalized)
    customer_name VARCHAR(100),
    customer_phone VARCHAR(20),
    customer_email VARCHAR(255),

    -- AI conversation reference
    conversation_id VARCHAR(255),

    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT check_subtotal_non_negative CHECK (subtotal >= 0),
    CONSTRAINT check_tax_non_negative CHECK (tax >= 0),
    CONSTRAINT check_delivery_fee_non_negative CHECK (delivery_fee >= 0),
    CONSTRAINT check_total_non_negative CHECK (total >= 0)
);

CREATE INDEX IF NOT EXISTS idx_order_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_customer_orders ON orders(customer_id, order_date);
CREATE INDEX IF NOT EXISTS idx_orders_account_status_created ON orders(account_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_account_created_desc ON orders(account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_account_order_date ON orders(account_id, order_date);
CREATE INDEX IF NOT EXISTS idx_orders_account_payment_status ON orders(account_id, payment_status);

-- Deliveries
CREATE TABLE IF NOT EXISTS deliveries (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
    driver_name VARCHAR(255),
    driver_phone VARCHAR(20),
    estimated_delivery_time TIMESTAMPTZ,
    actual_delivery_time TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'assigned',
    tracking_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_delivery_status ON deliveries(status);

-- ============================================
-- MENU SYSTEM
-- ============================================

-- Menus
CREATE TABLE IF NOT EXISTS menus (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES restaurant_accounts(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    available_days JSONB,
    available_start_time VARCHAR(10),
    available_end_time VARCHAR(10),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_menus_account ON menus(account_id);

-- Menu Categories
CREATE TABLE IF NOT EXISTS menu_categories (
    id SERIAL PRIMARY KEY,
    menu_id INTEGER NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_menu_category_order ON menu_categories(menu_id, display_order);

-- Menu Items
CREATE TABLE IF NOT EXISTS menu_items (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES menu_categories(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price_cents INTEGER NOT NULL,
    dietary_tags JSONB,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    image_url VARCHAR(500),
    preparation_time_minutes INTEGER,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT check_price_non_negative CHECK (price_cents >= 0)
);

CREATE INDEX IF NOT EXISTS idx_category_item_order ON menu_items(category_id, display_order);
CREATE INDEX IF NOT EXISTS idx_menu_items_name ON menu_items(name);
CREATE INDEX IF NOT EXISTS idx_menu_items_category_available ON menu_items(category_id, is_available);

-- Menu Modifiers
CREATE TABLE IF NOT EXISTS menu_modifiers (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    price_adjustment_cents INTEGER NOT NULL DEFAULT 0,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    modifier_group VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_modifiers_item ON menu_modifiers(item_id);

-- ============================================
-- COMMUNICATIONS & TRANSCRIPTS
-- ============================================

-- Transcripts (SMS and Voice)
CREATE TABLE IF NOT EXISTS transcripts (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES restaurant_accounts(id) ON DELETE CASCADE,
    transcript_type VARCHAR(20) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    twilio_phone VARCHAR(20),
    conversation_id VARCHAR(255) NOT NULL,
    messages JSONB NOT NULL,
    summary TEXT,
    outcome VARCHAR(100),
    duration_seconds INTEGER,
    order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_account_transcripts ON transcripts(account_id, created_at);
CREATE INDEX IF NOT EXISTS idx_transcript_type ON transcripts(transcript_type, created_at);
CREATE INDEX IF NOT EXISTS idx_transcripts_customer_phone ON transcripts(customer_phone);
CREATE INDEX IF NOT EXISTS idx_transcripts_conversation_id ON transcripts(conversation_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_account_created_desc ON transcripts(account_id, created_at DESC);

-- ============================================
-- ADMIN & NOTIFICATIONS
-- ============================================

-- Admin Notifications
CREATE TABLE IF NOT EXISTS admin_notifications (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    account_id INTEGER REFERENCES restaurant_accounts(id) ON DELETE SET NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notification_type ON admin_notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_notification_unread ON admin_notifications(is_read, created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_unread_created ON admin_notifications(is_read, created_at DESC) WHERE is_read = false;

-- ============================================
-- VOICE CARTS (for persistent cart storage)
-- ============================================

CREATE TABLE IF NOT EXISTS voice_carts (
    call_id TEXT PRIMARY KEY,
    restaurant_id INTEGER REFERENCES restaurant_accounts(id) ON DELETE CASCADE,
    items JSONB DEFAULT '[]'::jsonb,
    customer_phone TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '2 hours')
);

CREATE INDEX IF NOT EXISTS idx_voice_carts_expires ON voice_carts(expires_at);
CREATE INDEX IF NOT EXISTS idx_voice_carts_restaurant ON voice_carts(restaurant_id);

-- ============================================
-- AUDIT LOGS
-- ============================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    admin_email TEXT,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    old_value JSONB,
    new_value JSONB,
    ip_address TEXT,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_admin ON audit_logs(admin_email, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Auto-update updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all relevant tables
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('restaurant_accounts', 'restaurants', 'customers', 'bookings', 'orders', 'deliveries', 'menus', 'menu_items', 'transcripts', 'voice_carts')
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS update_%s_updated_at ON %s', t, t);
        EXECUTE format('CREATE TRIGGER update_%s_updated_at BEFORE UPDATE ON %s FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()', t, t);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Voice cart cleanup function
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

-- Audit logging helper
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
-- ANALYTICS RPC FUNCTIONS
-- ============================================

-- Daily order stats
CREATE OR REPLACE FUNCTION get_daily_order_stats(
    p_account_id INTEGER,
    p_start_date DATE,
    p_end_date DATE
)
RETURNS TABLE (
    order_date DATE,
    order_count BIGINT,
    revenue_cents BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        DATE(o.created_at) as order_date,
        COUNT(*)::BIGINT as order_count,
        COALESCE(SUM(o.total), 0)::BIGINT as revenue_cents
    FROM orders o
    WHERE o.account_id = p_account_id
      AND DATE(o.created_at) BETWEEN p_start_date AND p_end_date
      AND o.status != 'cancelled'
    GROUP BY DATE(o.created_at)
    ORDER BY order_date;
END;
$$ LANGUAGE plpgsql;

-- Hourly distribution
CREATE OR REPLACE FUNCTION get_hourly_distribution(
    p_account_id INTEGER,
    p_start_date DATE,
    p_end_date DATE
)
RETURNS TABLE (
    hour_of_day INTEGER,
    order_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        EXTRACT(HOUR FROM o.created_at)::INTEGER as hour_of_day,
        COUNT(*)::BIGINT as order_count
    FROM orders o
    WHERE o.account_id = p_account_id
      AND DATE(o.created_at) BETWEEN p_start_date AND p_end_date
      AND o.status != 'cancelled'
    GROUP BY EXTRACT(HOUR FROM o.created_at)
    ORDER BY hour_of_day;
END;
$$ LANGUAGE plpgsql;

-- Order analytics summary
CREATE OR REPLACE FUNCTION get_order_analytics_summary(
    p_account_id INTEGER,
    p_start_date DATE,
    p_end_date DATE
)
RETURNS TABLE (
    total_orders BIGINT,
    total_revenue_cents BIGINT,
    avg_order_value_cents BIGINT,
    takeout_orders BIGINT,
    delivery_orders BIGINT,
    unique_customers BIGINT,
    repeat_orders BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_orders,
        COALESCE(SUM(o.total), 0)::BIGINT as total_revenue_cents,
        CASE
            WHEN COUNT(*) > 0 THEN (COALESCE(SUM(o.total), 0) / COUNT(*))::BIGINT
            ELSE 0
        END as avg_order_value_cents,
        COUNT(*) FILTER (WHERE o.order_type = 'takeout')::BIGINT as takeout_orders,
        COUNT(*) FILTER (WHERE o.order_type = 'delivery')::BIGINT as delivery_orders,
        COUNT(DISTINCT o.customer_phone)::BIGINT as unique_customers,
        (COUNT(*) - COUNT(DISTINCT o.customer_phone))::BIGINT as repeat_orders
    FROM orders o
    WHERE o.account_id = p_account_id
      AND DATE(o.created_at) BETWEEN p_start_date AND p_end_date
      AND o.status != 'cancelled';
END;
$$ LANGUAGE plpgsql;

-- Platform revenue breakdown (admin)
CREATE OR REPLACE FUNCTION get_platform_revenue_breakdown(
    p_start_date DATE,
    p_end_date DATE
)
RETURNS TABLE (
    account_id INTEGER,
    business_name TEXT,
    order_count BIGINT,
    revenue_cents BIGINT,
    commission_rate NUMERIC,
    commission_cents BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ra.id as account_id,
        ra.business_name::TEXT,
        COUNT(o.id)::BIGINT as order_count,
        COALESCE(SUM(o.total), 0)::BIGINT as revenue_cents,
        COALESCE(ra.platform_commission_rate, 10.0) as commission_rate,
        (COALESCE(SUM(o.total), 0) * COALESCE(ra.platform_commission_rate, 10.0) / 100)::BIGINT as commission_cents
    FROM restaurant_accounts ra
    LEFT JOIN orders o ON o.account_id = ra.id
        AND o.order_date BETWEEN p_start_date AND p_end_date
    GROUP BY ra.id, ra.business_name, ra.platform_commission_rate
    HAVING COUNT(o.id) > 0
    ORDER BY revenue_cents DESC;
END;
$$ LANGUAGE plpgsql;

-- Platform stats (admin dashboard)
CREATE OR REPLACE FUNCTION get_platform_stats()
RETURNS TABLE (
    total_restaurants BIGINT,
    active_restaurants BIGINT,
    total_orders BIGINT,
    orders_today BIGINT,
    total_revenue_cents BIGINT,
    revenue_today_cents BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*)::BIGINT FROM restaurant_accounts) as total_restaurants,
        (SELECT COUNT(*)::BIGINT FROM restaurant_accounts WHERE is_active = true) as active_restaurants,
        (SELECT COUNT(*)::BIGINT FROM orders) as total_orders,
        (SELECT COUNT(*)::BIGINT FROM orders WHERE DATE(created_at) = CURRENT_DATE) as orders_today,
        (SELECT COALESCE(SUM(total), 0)::BIGINT FROM orders) as total_revenue_cents,
        (SELECT COALESCE(SUM(total), 0)::BIGINT FROM orders WHERE DATE(created_at) = CURRENT_DATE) as revenue_today_cents;
END;
$$ LANGUAGE plpgsql;

-- Today's orders
CREATE OR REPLACE FUNCTION get_today_orders(p_account_id INTEGER)
RETURNS TABLE (
    id INTEGER,
    customer_name TEXT,
    customer_phone TEXT,
    status TEXT,
    total INTEGER,
    order_type TEXT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.id,
        o.customer_name::TEXT,
        o.customer_phone::TEXT,
        o.status::TEXT,
        o.total,
        o.order_type::TEXT,
        o.created_at
    FROM orders o
    WHERE o.account_id = p_account_id
      AND DATE(o.created_at) = CURRENT_DATE
    ORDER BY o.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Active orders
CREATE OR REPLACE FUNCTION get_active_orders(p_account_id INTEGER)
RETURNS TABLE (
    id INTEGER,
    customer_name TEXT,
    customer_phone TEXT,
    status TEXT,
    total INTEGER,
    order_type TEXT,
    order_items JSONB,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.id,
        o.customer_name::TEXT,
        o.customer_phone::TEXT,
        o.status::TEXT,
        o.total,
        o.order_type::TEXT,
        o.order_items,
        o.created_at
    FROM orders o
    WHERE o.account_id = p_account_id
      AND o.status IN ('pending', 'confirmed', 'preparing', 'ready', 'out_for_delivery')
    ORDER BY
        CASE o.status
            WHEN 'pending' THEN 1
            WHEN 'confirmed' THEN 2
            WHEN 'preparing' THEN 3
            WHEN 'ready' THEN 4
            WHEN 'out_for_delivery' THEN 5
        END,
        o.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- ENABLE ROW LEVEL SECURITY (Optional)
-- ============================================

-- Note: RLS policies can be added here if needed
-- For now, we use service role key which bypasses RLS

-- ============================================
-- GRANT PERMISSIONS
-- ============================================

-- Grant permissions to anon and authenticated roles
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;
