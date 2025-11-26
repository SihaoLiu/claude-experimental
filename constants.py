"""Pricing and configuration constants for Claude Code usage analysis."""

# Pricing constants (per million tokens) - model-specific
MODEL_PRICING = {
    'claude-sonnet-4-5-20250929': {
        'input': 1.50,
        'output': 7.50,
        'cache_input': 0.15,
        'cache_output': 1.875,
    },
    'claude-haiku-4-5-20251001': {
        'input': 0.50,
        'output': 2.50,
        'cache_input': 0.05,
        'cache_output': 0.625,
    },
    'claude-opus-4-5-20251101': {
        'input': 2.50,
        'output': 12.50,
        'cache_input': 0.25,
        'cache_output': 3.125,
    },
}

# Default pricing (fallback for unknown models, using Sonnet pricing)
DEFAULT_PRICING = {
    'input': 1.50,
    'output': 7.50,
    'cache_input': 0.15,
    'cache_output': 1.875,
}

# Subscription pricing
SUBSCRIPTION_PRICE = 200  # $200 / month

# Session and weekly duration constants (in minutes)
SESSION_DURATION_MINUTES = 300  # 5 hours
WEEKLY_DURATION_MINUTES = 10080  # 7 days = 168 hours
