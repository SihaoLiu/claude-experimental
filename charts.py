"""Chart and visualization functions for Claude Code usage analysis."""

from datetime import timedelta
from formatting import format_y_axis_value, format_total_value


def print_stacked_bar_chart(time_series, height=75, days_back=7, chart_type='all', show_x_axis=True):
    """Print a text-based stacked bar chart of token usage breakdown over time.

    Args:
        time_series: Time series data with token breakdown
        height: Height of the chart
        days_back: Number of days to show
        chart_type: 'all' (all 4 types), 'io' (input+output), or 'cache' (cache_creation+cache_read)
        show_x_axis: Whether to show X-axis labels
    """
    if not time_series:
        print("No time series data available.")
        return

    # Sort by time
    all_sorted_times = sorted(time_series.keys())

    if not all_sorted_times:
        print("No data available.")
        return

    # Calculate start time based on days_back parameter
    last_time = all_sorted_times[-1]
    start_time = last_time - timedelta(days=days_back)

    # Round start_time down to nearest hour
    start_time_rounded = start_time.replace(minute=0, second=0, microsecond=0)

    # Create a complete continuous time series (every hour)
    # This ensures uniform spacing even when there's no data
    sorted_times = []
    current_time = start_time_rounded
    while current_time <= last_time:
        sorted_times.append(current_time)
        current_time += timedelta(hours=1)

    if len(sorted_times) < 2:
        print("Not enough data points for chart.")
        return

    # Limit chart width to 500 columns
    if len(sorted_times) > 500:
        # Adjust interval to fit in 500 columns
        hours_per_interval = len(sorted_times) / 500
        print(f"Note: Adjusting interval to ~{hours_per_interval:.1f} hours to fit in 500 columns.")

        # Resample to fit in 500 columns
        step = max(1, len(sorted_times) // 500)
        sorted_times = sorted_times[::step]

    # Calculate breakdown per time interval
    breakdown_data = []
    totals = []
    for time in sorted_times:
        if time in time_series:
            input_val = time_series[time].get('input', 0)
            output_val = time_series[time].get('output', 0)
            cache_creation_val = time_series[time].get('cache_creation', 0)
            cache_read_val = time_series[time].get('cache_read', 0)
        else:
            input_val = output_val = cache_creation_val = cache_read_val = 0

        breakdown_data.append({
            'input': input_val,
            'output': output_val,
            'cache_creation': cache_creation_val,
            'cache_read': cache_read_val
        })

        # Calculate total based on chart_type
        if chart_type == 'io':
            total = input_val + output_val
        elif chart_type == 'cache':
            total = cache_creation_val + cache_read_val
        else:  # 'all'
            total = input_val + output_val + cache_creation_val + cache_read_val

        totals.append(total)

    # First pass: calculate Y-axis range from all data
    max_value_raw = max(totals) if totals else 1
    min_value_raw = min(totals) if totals else 0

    # Round min/max to nearest multiple of 5K or 5M or 5B
    def round_to_5_multiple(value, round_up=True):
        """Round value to nearest multiple of 5B/5M/5K."""
        if value >= 5_000_000_000:
            # Round to nearest 5B
            unit = 5_000_000_000
        elif value >= 5_000_000:
            # Round to nearest 5M
            unit = 5_000_000
        elif value >= 5_000:
            # Round to nearest 5K
            unit = 5_000
        else:
            # Round to nearest 5
            unit = 5

        if round_up:
            return ((int(value) + unit - 1) // unit) * unit
        else:
            return (int(value) // unit) * unit

    min_value = round_to_5_multiple(min_value_raw, round_up=False)
    max_value = round_to_5_multiple(max_value_raw, round_up=True)

    # Ensure max > min
    if max_value == min_value:
        max_value = min_value + 5_000

    num_data_points = len(totals)
    chart_height = height

    # Print chart title based on type
    if chart_type == 'io':
        print("\nInput + Output Tokens Over Time (1-hour intervals, Local Time)")
        print(f"Y-axis: Input and Output token consumption")
    elif chart_type == 'cache':
        print("\nCache Tokens Over Time (1-hour intervals, Local Time)")
        print(f"Y-axis: Cache Output and Cache Input token consumption")
    else:
        print("\nToken Usage Breakdown Over Time (1-hour intervals, Local Time)")
        print(f"Y-axis: Token consumption (all token types)")

    if show_x_axis:
        print(f"X-axis: Time (each day has 24 data points, ticks at 6-hour intervals)\n")
    else:
        print()

    # Scale breakdown values to chart height
    # For each data point, calculate the scaled heights of each segment
    scaled_breakdown = []
    for breakdown in breakdown_data:
        if max_value == min_value:
            scaled_breakdown.append({
                'input': 0,
                'output': 0,
                'cache_creation': 0,
                'cache_read': 0
            })
        else:
            # Scale each component individually
            scaled_breakdown.append({
                'input': int((breakdown['input'] - 0) / (max_value - min_value) * (chart_height - 1)),
                'output': int((breakdown['output'] - 0) / (max_value - min_value) * (chart_height - 1)),
                'cache_creation': int((breakdown['cache_creation'] - 0) / (max_value - min_value) * (chart_height - 1)),
                'cache_read': int((breakdown['cache_read'] - 0) / (max_value - min_value) * (chart_height - 1))
            })

    # Build chart:
    # First day: data points (no separator, Y-axis serves as the boundary)
    # Subsequent days: separator + data points
    chart_columns = []  # List of (type, value)
    data_to_col = {}  # Map data point index to column index

    col_idx = 0
    for i in range(num_data_points):
        time = sorted_times[i]

        # Add separator before 00:00 (except for the very first day)
        if time.hour == 0 and time.minute == 0 and i > 0:
            chart_columns.append(('separator', None))
            col_idx += 1

        # Add data point
        chart_columns.append(('data', i))
        data_to_col[i] = col_idx
        col_idx += 1

    chart_width = len(chart_columns)
    print("=" * (chart_width + 10))

    # Calculate daily totals for display at top of chart
    daily_totals = []
    current_day_start = None
    current_day_total = 0
    current_day_start_col = 0

    for col_idx, (col_type, col_data) in enumerate(chart_columns):
        if col_type == 'separator':
            # End of previous day
            if current_day_start is not None:
                mid_col = (current_day_start_col + col_idx) // 2
                daily_totals.append((mid_col, current_day_total, current_day_start))
            current_day_start = None
            current_day_total = 0
            current_day_start_col = col_idx + 1
        else:
            data_idx = col_data
            if current_day_start is None:
                current_day_start = sorted_times[data_idx]
                current_day_start_col = col_idx
            current_day_total += totals[data_idx]

    # Add last day if exists
    if current_day_start is not None:
        mid_col = (current_day_start_col + len(chart_columns)) // 2
        daily_totals.append((mid_col, current_day_total, current_day_start))

    # Print daily totals at top of chart (weekday + total tokens)
    weekday_line = " " * 7  # Align with Y-axis
    date_line = " " * 7  # Align with Y-axis
    prev_end = 0

    weekday_abbr = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    for day_idx, (mid_col, total, day_start) in enumerate(daily_totals):
        total_str = format_total_value(total)
        weekday = weekday_abbr[day_start.weekday()]
        weekday_total = f"{weekday} : {total_str}"

        # Format date as " MM / DD"
        date_str = day_start.strftime(' %m / %d')

        # Find positions of : and /
        colon_idx = weekday_total.index(':')
        slash_idx = date_str.index('/')

        # Add padding to align : and / at the same relative position
        if colon_idx > slash_idx:
            # Add spaces before date_str
            date_str = ' ' * (colon_idx - slash_idx) + date_str
            slash_idx = colon_idx
        elif slash_idx > colon_idx:
            # Add spaces before weekday_total
            weekday_total = ' ' * (slash_idx - colon_idx) + weekday_total
            colon_idx = slash_idx

        # Make both strings the same length
        max_len = max(len(weekday_total), len(date_str))
        weekday_total = weekday_total.ljust(max_len)
        date_str = date_str.ljust(max_len)

        # Position them so : and / are at mid_col
        start_pos = mid_col - colon_idx

        # Add padding and content to both lines
        padding = start_pos - prev_end
        if padding > 0:
            weekday_line += " " * padding
            date_line += " " * padding

        weekday_line += weekday_total
        date_line += date_str
        prev_end = start_pos + max_len

    print(weekday_line)
    print(date_line)

    # Draw chart from top to bottom (stacked bar chart style)
    for row in range(chart_height - 1, -1, -1):
        # Y-axis label
        y_val = min_value + (max_value - min_value) * row / (chart_height - 1)
        y_label = f"{format_y_axis_value(y_val)} |"

        # Chart line
        line = ""
        for col_type, col_data in chart_columns:
            if col_type == 'separator':
                line += "|"
            else:
                data_idx = col_data
                breakdown = scaled_breakdown[data_idx]

                # Calculate cumulative heights for stacking (bottom to top)
                # Stack order: input (bottom) -> output -> cache_creation -> cache_read (top)
                input_height = breakdown['input']
                output_height = breakdown['output']
                cache_creation_height = breakdown['cache_creation']
                cache_read_height = breakdown['cache_read']

                cumulative_input = input_height
                cumulative_output = cumulative_input + output_height
                cumulative_cache_creation = cumulative_output + cache_creation_height
                cumulative_cache_read = cumulative_cache_creation + cache_read_height

                # Determine which character to draw based on current row and chart_type
                # ANSI 256-color codes: Cyan for input, Green for output, Orange for cache_output, Pink for cache_input
                if chart_type == 'io':
                    # Only show input and output
                    if row < cumulative_input:
                        line += "\033[38;5;51m\u2588\033[0m"  # Input tokens (Bright Cyan)
                    elif row < cumulative_output:
                        line += "\033[38;5;46m\u2593\033[0m"  # Output tokens (Bright Green)
                    else:
                        line += " "  # Empty space
                elif chart_type == 'cache':
                    # Only show cache_creation and cache_read, but calculate from 0
                    cache_only_cumulative_creation = cache_creation_height
                    cache_only_cumulative_read = cache_only_cumulative_creation + cache_read_height
                    if row < cache_only_cumulative_creation:
                        line += "\033[38;5;214m\u2592\033[0m"  # Cache output tokens (Bright Orange)
                    elif row < cache_only_cumulative_read:
                        line += "\u2588"  # Cache input tokens (default color)
                    else:
                        line += " "  # Empty space
                else:
                    # Show all 4 types
                    if row < cumulative_input:
                        line += "\033[38;5;51m\u2588\033[0m"  # Input tokens (Bright Cyan)
                    elif row < cumulative_output:
                        line += "\033[38;5;46m\u2593\033[0m"  # Output tokens (Bright Green)
                    elif row < cumulative_cache_creation:
                        line += "\033[38;5;214m\u2592\033[0m"  # Cache output tokens (Bright Orange)
                    elif row < cumulative_cache_read:
                        line += "\u2588\u2591"  # Cache input tokens (default color)
                    else:
                        line += " "  # Empty space

        print(y_label + line)

    # X-axis with day separators
    # Position: 6 spaces to align + with Y-axis |
    x_axis_line = ""
    for col_type, _ in chart_columns:
        if col_type == 'separator':
            x_axis_line += "\u2534"
        else:
            x_axis_line += "\u2500"
    print("      \u2514" + x_axis_line)  # 6 spaces + corner aligns with Y-axis position

    # X-axis labels (show only if show_x_axis is True)
    if show_x_axis:
        # X-axis labels (show only 6:00, 12:00, and 18:00) - rotated 90 degrees counter-clockwise
        print()

        # Create label for 6:00, 12:00, and 18:00
        labels = []
        positions = []

        for i, time in enumerate(sorted_times):
            # Only show labels for 6:00, 12:00, and 18:00
            if time.hour in [6, 12, 18]:
                # Position is the column index for this data point
                if i in data_to_col:
                    labels.append(time.strftime('%H'))
                    positions.append(data_to_col[i])

        # Find maximum label length
        max_label_len = max(len(label) for label in labels) if labels else 0

        # Print each character position vertically
        # Position: 6 spaces to align first character with Y-axis | position
        # Then add one more space so labels start at column 0 of chart content
        for char_idx in range(max_label_len):
            line = "       "  # 7 spaces: aligns with Y-axis format (5 chars + space + |)

            for col_idx, (col_type, col_data) in enumerate(chart_columns):
                if col_type == 'separator':
                    char_to_print = "|"
                else:
                    # Check if this column has a label
                    char_to_print = " "
                    for label_idx, pos in enumerate(positions):
                        if col_idx == pos and char_idx < len(labels[label_idx]):
                            char_to_print = labels[label_idx][char_idx]
                            break

                line += char_to_print

            print(line)

    # Show summary info only for the last chart (when show_x_axis is True)
    if show_x_axis:
        print("\n" + "=" * (chart_width + 10))
        print(f"Total time span: {sorted_times[0].strftime('%Y-%m-%d %H:%M')} to {sorted_times[-1].strftime('%Y-%m-%d %H:%M')} | Data points: {len(sorted_times)}")
        print(f"Legend: \033[38;5;51m\u2588\033[0m Input  \033[38;5;46m\u2593\033[0m Output  \u2588 Cache Input  \033[38;5;214m\u2592\033[0m Cache Output")


def print_model_chart(time_series, width=100, height=15):
    """Print a text-based chart showing each model's usage over time."""
    if not time_series:
        print("No time series data available.")
        return

    sorted_times = sorted(time_series.keys())

    if len(sorted_times) < 2:
        print("Not enough data points for chart.")
        return

    # Get all models and their colors
    all_models = set()
    for models in time_series.values():
        all_models.update(models.keys())

    all_models = sorted(all_models)
    model_symbols = {'claude-sonnet-4-5-20250929': '\u2588',
                     'claude-haiku-4-5-20251001': '\u2593',
                     'claude-opus-4-1-20250805': '\u2592'}

    print("\n\nToken Usage by Model Over Time")
    print("=" * width)

    for model in all_models:
        if model not in model_symbols:
            model_symbols[model] = '\u2591'

        # Get values for this model
        values = []
        for time in sorted_times:
            val = time_series[time].get(model, 0) / 1000  # KTok
            values.append(val)

        if all(v == 0 for v in values):
            continue

        max_value = max(values)

        # Print model name
        print(f"\n{model}:")
        print(f"Max: {max_value:.1f} KTok")

        # Simple bar chart
        chart_width = width - 25
        for i, val in enumerate(values):
            if i % 4 == 0:  # Show every 4th data point to avoid clutter
                bar_length = int((val / max_value * chart_width)) if max_value > 0 else 0
                time_str = sorted_times[i].strftime('%m/%d %H:%M')
                bar = model_symbols[model] * bar_length
                print(f"  {time_str} |{bar} {val:.1f}")
