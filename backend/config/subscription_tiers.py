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
        "commission_rate": 15.0,  # 15% commission during trial
    },
    "starter": {
        "name": "Starter",
        "monthly_price": 49,
        "commission_rate": 0.0,  # $49/mo flat fee, no commission
    },
    "growth": {
        "name": "Growth",
        "monthly_price": 149,
        "commission_rate": 3.0,  # $149/mo + 3% commission
    },
    "scale": {
        "name": "Scale",
        "monthly_price": 299,
        "commission_rate": 3.0,  # $299/mo + 3% commission
    },
}


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
    return 15.0  # Default to 15% if unknown tier


def get_tier_monthly_price(tier: str) -> int:
    """Get the monthly price for a subscription tier."""
    tier_config = SUBSCRIPTION_TIERS.get(tier.lower())
    if tier_config:
        return tier_config["monthly_price"]
    return 0
