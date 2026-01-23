-- Analytics RPC functions migration
-- Run this in Supabase SQL Editor
-- These functions move heavy aggregations to the database level for better performance

-- ============================================
-- DAILY ORDER STATS (for trends)
-- ============================================
-- Returns daily order count and revenue for a given account and date range

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


-- ============================================
-- HOURLY ORDER DISTRIBUTION (for peak hours)
-- ============================================

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


-- ============================================
-- ORDER ANALYTICS SUMMARY
-- ============================================
-- Single query for all summary stats

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


-- ============================================
-- PLATFORM REVENUE BREAKDOWN (for admin)
-- ============================================
-- Aggregates revenue by restaurant account

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
        ra.business_name,
        COUNT(o.id)::BIGINT as order_count,
        COALESCE(SUM(o.total), 0)::BIGINT as revenue_cents,
        COALESCE(ra.platform_commission_rate, 10.0) as commission_rate,
        (COALESCE(SUM(o.total), 0) * COALESCE(ra.platform_commission_rate, 10.0) / 100)::BIGINT as commission_cents
    FROM restaurant_accounts ra
    LEFT JOIN restaurants r ON r.account_id = ra.id
    LEFT JOIN orders o ON o.restaurant_id = r.id
        AND o.order_date BETWEEN p_start_date AND p_end_date
    GROUP BY ra.id, ra.business_name, ra.platform_commission_rate
    HAVING COUNT(o.id) > 0
    ORDER BY revenue_cents DESC;
END;
$$ LANGUAGE plpgsql;


-- ============================================
-- PLATFORM STATS (for admin dashboard)
-- ============================================

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


-- ============================================
-- TODAY'S ORDERS (optimized for dashboard)
-- ============================================

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
        o.customer_name,
        o.customer_phone,
        o.status,
        o.total,
        o.order_type,
        o.created_at
    FROM orders o
    WHERE o.account_id = p_account_id
      AND DATE(o.created_at) = CURRENT_DATE
    ORDER BY o.created_at DESC;
END;
$$ LANGUAGE plpgsql;


-- ============================================
-- ACTIVE ORDERS (pending, confirmed, preparing, ready)
-- ============================================

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
        o.customer_name,
        o.customer_phone,
        o.status,
        o.total,
        o.order_type,
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
-- VERIFY FUNCTIONS
-- ============================================
-- Run this to check functions were created:
-- SELECT routine_name FROM information_schema.routines WHERE routine_type = 'FUNCTION' AND routine_schema = 'public';
