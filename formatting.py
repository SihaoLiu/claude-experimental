"""Formatting utilities for Claude Code usage analysis."""

from constants import MODEL_PRICING, DEFAULT_PRICING, SUBSCRIPTION_PRICE


def format_number(num):
    """Format number with thousand separators."""
    return f"{num:,}"


def format_y_axis_value(value):
    """Format Y-axis value to always be 5 characters with K/M units."""
    if value >= 1_000_000:
        # Millions
        val_m = value / 1_000_000
        if val_m >= 100:
            return f"{int(val_m):3d} M"
        elif val_m >= 10:
            return f" {int(val_m):2d} M"
        else:
            return f"{val_m:3.1f} M"
    elif value >= 1000:
        # Thousands
        val_k = value / 1000
        if val_k >= 100:
            return f"{int(val_k):3d} K"
        elif val_k >= 10:
            return f" {int(val_k):2d} K"
        else:
            return f"{val_k:3.1f} K"
    else:
        # Less than 1000, show as integer
        return f"{int(value):5d}"


def format_total_value(value):
    """Format total value with B/M/K units."""
    if value >= 1_000_000_000:
        # Billions
        val_b = value / 1_000_000_000
        if val_b >= 100:
            return f"{int(val_b)}B"
        elif val_b >= 10:
            return f"{val_b:.1f}B"
        else:
            return f"{val_b:.2f}B"
    elif value >= 1_000_000:
        # Millions
        val_m = value / 1_000_000
        if val_m >= 100:
            return f"{int(val_m)}M"
        elif val_m >= 10:
            return f"{val_m:.1f}M"
        else:
            return f"{val_m:.2f}M"
    elif value >= 1_000:
        # Thousands
        val_k = value / 1_000
        if val_k >= 100:
            return f"{int(val_k)}K"
        elif val_k >= 10:
            return f"{val_k:.1f}K"
        else:
            return f"{val_k:.2f}K"
    else:
        # Less than 1000
        return f"{int(value)}"


def print_overall_stats(stats):
    """Print overall statistics."""
    print("Overall Usage Statistics")
    print("=" * 50)
    print()
    print(f"Total messages:        {format_number(stats['total_messages'])}")
    print()
    print(f"Input tokens:          {format_number(stats['input_tokens'])}")
    print(f"Output tokens:         {format_number(stats['output_tokens'])}")
    print(f"Cache output tokens:   {format_number(stats['cache_creation_tokens'])}")
    print(f"Cache input tokens:    {format_number(stats['cache_read_tokens'])}")
    print()
    print(f"Total tokens:          {format_number(stats['total_tokens'])}")


def print_model_breakdown(model_stats, days_in_data=7):
    """Print model breakdown table.

    Args:
        model_stats: Model statistics to display
        days_in_data: Number of days the data covers (for cost projections)
    """
    print("Usage / Cost by Model")
    print("=" * 154)

    # Print header
    header = f"| {'Model':<35} {'Messages':>10} | {'Input':>15} {'Output':>15} {'Total':>15} | {'Cache Output':>15} {'Cache Input':>15} {'Cache Total':>19} |"
    print(header)
    print("|" + "-" * 152 + "|")

    # Print rows and calculate sums
    sum_messages = 0
    sum_input = 0
    sum_output = 0
    sum_total = 0
    sum_cache_creation = 0
    sum_cache_read = 0
    sum_total_with_cache = 0

    for stats in model_stats:
        row = (f"| {stats['model']:<35} "
               f"{stats['count']:>10} | "
               f"{format_number(stats['input']):>15} "
               f"{format_number(stats['output']):>15} "
               f"{format_number(stats['total']):>15} | "
               f"{format_number(stats['cache_creation']):>15} "
               f"{format_number(stats['cache_read']):>15} "
               f"{format_number(stats['total_with_cache']):>19} |")
        print(row)

        # Accumulate sums
        sum_messages += stats['count']
        sum_input += stats['input']
        sum_output += stats['output']
        sum_total += stats['total']
        sum_cache_creation += stats['cache_creation']
        sum_cache_read += stats['cache_read']
        sum_total_with_cache += stats['total_with_cache']

    # Print separator and sum row
    print("|" + "-" * 152 + "|")
    sum_row = (f"| {'TOTAL':<35} "
               f"{sum_messages:>10} | "
               f"{format_number(sum_input):>15} "
               f"{format_number(sum_output):>15} "
               f"{format_number(sum_total):>15} | "
               f"{format_number(sum_cache_creation):>15} "
               f"{format_number(sum_cache_read):>15} "
               f"{format_number(sum_total_with_cache):>19} |")
    print(sum_row)

    # Calculate and print API cost row (using model-specific pricing)
    input_cost = 0
    output_cost = 0
    cache_output_cost = 0
    cache_input_cost = 0

    for stats in model_stats:
        model = stats['model']
        pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)

        input_cost += stats['input'] * pricing['input'] / 1_000_000
        output_cost += stats['output'] * pricing['output'] / 1_000_000
        cache_output_cost += stats['cache_creation'] * pricing['cache_output'] / 1_000_000
        cache_input_cost += stats['cache_read'] * pricing['cache_input'] / 1_000_000

    io_total_cost = input_cost + output_cost
    cache_total_cost = cache_output_cost + cache_input_cost
    total_cost = io_total_cost + cache_total_cost

    cost_row = (f"| {'Cost(API)':<35} "
                f"{'':>10} | "
                f"${input_cost:>14.2f} "
                f"${output_cost:>14.2f} "
                f"${io_total_cost:>14.2f} | "
                f"${cache_output_cost:>14.2f} "
                f"${cache_input_cost:>14.2f} "
                f"${total_cost:>18.2f} |")
    print(cost_row)
    print("=" * 154)

    # Calculate daily, weekly, monthly costs based on average from the data period
    daily_cost = total_cost / days_in_data if days_in_data > 0 else 0
    weekly_cost = daily_cost * 7
    monthly_cost = daily_cost * 30
    savings = monthly_cost - SUBSCRIPTION_PRICE

    # Calculate cost per million tokens with subscription
    # Project total tokens to monthly usage
    monthly_tokens = (sum_total_with_cache / days_in_data) * 30 if days_in_data > 0 else 0
    cost_per_mtok = SUBSCRIPTION_PRICE / (monthly_tokens / 1_000_000) if monthly_tokens > 0 else 0

    print(f"Daily: ${daily_cost:.2f}, Weekly: ${weekly_cost:.2f}, Monthly(30d): ${monthly_cost:.2f}, Monthly Saving ${savings:.2f}, ${cost_per_mtok:.2f} / MTok")
