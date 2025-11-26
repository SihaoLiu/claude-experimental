#!/usr/bin/env python3
"""Main entry point for Claude Code usage analysis."""

import os
import sys
import argparse
import time
import select
from datetime import datetime

from data import get_claude_dir, read_jsonl_files, filter_usage_data_by_days
from stats import calculate_model_breakdown, calculate_token_breakdown_time_series
from formatting import print_model_breakdown
from charts import print_stacked_bar_chart
from subscription import get_subscription_usage, print_subscription_usage_table


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Analyze Claude Code usage statistics')
    parser.add_argument('--days', type=int, default=7,
                        help='Number of days to look back (default: 7)')
    parser.add_argument('--monitor', type=int, nargs='?', const=3600, metavar='INTERVAL',
                        help='Monitor mode: refresh output every INTERVAL seconds (default: 3600 seconds / 1 hour)')
    args = parser.parse_args()

    claude_dir = get_claude_dir()
    projects_dir = claude_dir / 'projects'

    if not projects_dir.exists():
        print(f"Error: Projects directory not found at {projects_dir}")
        sys.exit(1)

    def print_stats():
        """Print all statistics (for both one-time and monitor mode)."""
        # Clear screen in monitor mode
        if args.monitor:
            os.system('clear' if os.name != 'nt' else 'cls')

        print("Calculating Claude Code usage...")
        print(f"Showing data from last {args.days} days")
        if args.monitor:
            print(f"Monitor mode: Refreshing every {args.monitor} seconds (Press Ctrl+C to exit)")
            print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Read data
        usage_data = read_jsonl_files(projects_dir)

        if not usage_data:
            print("No usage data found.")
            return False

        # Filter data based on days parameter
        filtered_usage_data = filter_usage_data_by_days(usage_data, args.days)

        if not filtered_usage_data:
            print(f"No usage data found in the last {args.days} days.")
            return False

        # Calculate and print statistics using filtered data
        model_stats = calculate_model_breakdown(filtered_usage_data)
        print_model_breakdown(model_stats, days_in_data=args.days)

        # Calculate and print token breakdown time series (stacked bar charts)
        # Use 1-hour intervals for finer granularity
        breakdown_time_series = calculate_token_breakdown_time_series(filtered_usage_data, interval_hours=1)

        # Print two separate charts: I/O tokens and Cache tokens
        # Each with reduced height (29) to make room for subscription usage table
        print_stacked_bar_chart(breakdown_time_series, height=29, days_back=args.days,
                                chart_type='io', show_x_axis=False)
        print_stacked_bar_chart(breakdown_time_series, height=29, days_back=args.days,
                                chart_type='cache', show_x_axis=True)

        # Print subscription usage information
        print()
        subscription_data = get_subscription_usage()
        print_subscription_usage_table(subscription_data)

        print()
        return True

    # Monitor mode: interactive continuous refresh
    if args.monitor:
        print("\n" + "=" * 80)
        print("Interactive Monitor Mode")
        print("=" * 80)
        print("Commands:")
        print("  /refresh - Refresh statistics immediately")
        print("  /exit    - Exit monitor mode")
        print("  Ctrl+C   - Exit monitor mode")
        print(f"\nAuto-refresh interval: {args.monitor} seconds")
        print("=" * 80 + "\n")

        # Initial display
        print_stats()

        next_refresh_time = time.time() + args.monitor

        def show_prompt():
            """Display the command prompt."""
            print("\n" + "-" * 80)
            print("> ", end='', flush=True)

        # Show initial prompt
        show_prompt()

        try:
            while True:
                now = time.time()

                # Check if it's time for auto-refresh
                if now >= next_refresh_time:
                    # Clear the current line (prompt)
                    print("\r" + " " * 82 + "\r", end='')
                    print("-" * 80)
                    print("\n" + "=" * 80)
                    print("AUTO-REFRESH")
                    print("=" * 80 + "\n")
                    print_stats()
                    next_refresh_time = time.time() + args.monitor
                    show_prompt()

                # Wait for input with timeout using select
                time_until_refresh = next_refresh_time - time.time()
                timeout = min(1.0, max(0.1, time_until_refresh))

                ready, _, _ = select.select([sys.stdin], [], [], timeout)

                if ready:
                    command = sys.stdin.readline().strip()

                    if command == "/refresh":
                        print("-" * 80)
                        print("\n" + "=" * 80)
                        print("MANUAL REFRESH")
                        print("=" * 80 + "\n")
                        print_stats()
                        # Reset auto-refresh timer
                        next_refresh_time = time.time() + args.monitor
                        show_prompt()
                    elif command == "/exit":
                        print("-" * 80)
                        print("\nExiting monitor mode...")
                        break
                    elif command == "":
                        # Empty command, just show prompt again
                        show_prompt()
                    elif command:
                        print(f"Unknown command: '{command}'. Available: /refresh, /exit")
                        show_prompt()

        except KeyboardInterrupt:
            print("\n" + "-" * 80)
            print("\nMonitoring stopped.")

        sys.exit(0)
    else:
        # One-time execution
        if not print_stats():
            sys.exit(0)


if __name__ == '__main__':
    main()
