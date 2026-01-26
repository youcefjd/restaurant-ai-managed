-- Migration: Add max_advance_order_days to restaurant_accounts
-- This allows restaurants to configure how far in advance customers can place orders.
-- 0 = same-day only, 1 = up to tomorrow, 7 = up to a week, etc.

ALTER TABLE restaurant_accounts
ADD COLUMN IF NOT EXISTS max_advance_order_days INTEGER DEFAULT 0;

COMMENT ON COLUMN restaurant_accounts.max_advance_order_days IS 'Maximum days in advance a customer can place an order (0 = same-day only)';
