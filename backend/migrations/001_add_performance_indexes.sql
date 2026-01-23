-- Performance indexes migration
-- Run this in Supabase SQL Editor
-- These indexes significantly improve query performance at scale

-- ============================================
-- ORDERS TABLE INDEXES
-- ============================================

-- Critical for dashboard queries (filtering by account + status + date)
CREATE INDEX IF NOT EXISTS idx_orders_account_status_created
ON orders(account_id, status, created_at DESC);

-- Critical for analytics (date range queries)
CREATE INDEX IF NOT EXISTS idx_orders_account_created_desc
ON orders(account_id, created_at DESC);

-- For order date filtering
CREATE INDEX IF NOT EXISTS idx_orders_account_order_date
ON orders(account_id, order_date);

-- For payment status queries
CREATE INDEX IF NOT EXISTS idx_orders_account_payment_status
ON orders(account_id, payment_status);

-- ============================================
-- BOOKINGS TABLE INDEXES
-- ============================================

-- Critical for availability checking
CREATE INDEX IF NOT EXISTS idx_bookings_restaurant_date
ON bookings(restaurant_id, booking_date);

-- For table availability queries
CREATE INDEX IF NOT EXISTS idx_bookings_table_date_status
ON bookings(table_id, booking_date, status);

-- ============================================
-- TRANSCRIPTS TABLE INDEXES
-- ============================================

-- For loading recent transcripts
CREATE INDEX IF NOT EXISTS idx_transcripts_account_created_desc
ON transcripts(account_id, created_at DESC);

-- ============================================
-- RESTAURANT ACCOUNTS TABLE INDEXES
-- ============================================

-- For email lookups during authentication
CREATE INDEX IF NOT EXISTS idx_accounts_email
ON restaurant_accounts(owner_email);

-- For subscription status queries
CREATE INDEX IF NOT EXISTS idx_accounts_subscription
ON restaurant_accounts(subscription_status, is_active);

-- ============================================
-- MENU ITEMS TABLE INDEXES
-- ============================================

-- For active items queries
CREATE INDEX IF NOT EXISTS idx_menu_items_category_available
ON menu_items(category_id, is_available);

-- ============================================
-- CUSTOMERS TABLE INDEXES
-- ============================================

-- For phone lookups
CREATE INDEX IF NOT EXISTS idx_customers_phone_created
ON customers(phone, created_at DESC);

-- ============================================
-- ADMIN NOTIFICATIONS TABLE INDEXES
-- ============================================

-- For unread notifications
CREATE INDEX IF NOT EXISTS idx_notifications_unread_created
ON admin_notifications(is_read, created_at DESC)
WHERE is_read = false;

-- ============================================
-- VERIFY INDEXES
-- ============================================

-- Run this to check indexes were created:
-- SELECT indexname, indexdef FROM pg_indexes WHERE tablename IN ('orders', 'bookings', 'transcripts', 'restaurant_accounts', 'menu_items', 'customers', 'admin_notifications');
