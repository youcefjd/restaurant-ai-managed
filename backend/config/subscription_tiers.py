"""
Subscription tier configuration.

Defines tier names, pricing, and default commission rates.
Admins can override commission per-restaurant from the admin console.
"""

# Subscription tiers with monthly pricing
SUBSCRIPTION_TIERS = {
    "free": {
        "name": "Free Trial",
        "monthly_price": 0,
        "commission_rate": 0.0,  # No commission
        "per_order_fee_cents": 0,  # No per-order fee during trial
    },
    "starter": {
        "name": "Starter",
        "monthly_price": 49,
        "commission_rate": 0.0,  # No commission
        "per_order_fee_cents": 50,  # $0.50 per order
    },
    "growth": {
        "name": "Growth",
        "monthly_price": 149,
        "commission_rate": 0.0,  # No commission
        "per_order_fee_cents": 50,  # $0.50 per order
    },
    "scale": {
        "name": "Scale",
        "monthly_price": 299,
        "commission_rate": 0.0,  # No commission
        "per_order_fee_cents": 50,  # $0.50 per order
    },
}

# Default per-order fee for all paid tiers
DEFAULT_PER_ORDER_FEE_CENTS = 50  # $0.50


def get_default_commission_for_tier(tier: str) -> float:
    """
    Get the default commission rate for a subscription tier.

    Args:
        tier: Subscription tier name (free, starter, growth, scale)

    Returns:
        Default commission rate percentage (0-100)
    """
    tier_config = SUBSCRIPTION_TIERS.get(tier.lower())
    if tier_config:
        return tier_config["commission_rate"]
    return 0.0  # Default to 0% - no commission


def get_tier_monthly_price(tier: str) -> int:
    """Get the monthly price for a subscription tier."""
    tier_config = SUBSCRIPTION_TIERS.get(tier.lower())
    if tier_config:
        return tier_config["monthly_price"]
    return 0


def get_per_order_fee_for_tier(tier: str) -> int:
    """Get the per-order fee in cents for a subscription tier."""
    tier_config = SUBSCRIPTION_TIERS.get(tier.lower())
    if tier_config:
        return tier_config["per_order_fee_cents"]
    return DEFAULT_PER_ORDER_FEE_CENTS
