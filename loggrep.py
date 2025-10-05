#!/usr/bin/env python3
"""
loggrep.py - A powerful log file grep tool with support for timestamps, regex, invert match, context lines, and color output.

This tool is designed to search log files (e.g., Unix syslog, Android logcat) for a pattern, but only after a specified startup time.
It supports reading from stdin or a file, and provides features similar to grep, including invert match, context lines, and color highlighting.

Usage:
    loggrep.py <pattern> [--file LOG_FILE] [--startup-time STARTUP_TIME] [OPTIONS]

Arguments:
    pattern (str): Regex pattern(s) to search for. Multiple patterns are OR'd together.
    --file (str, optional): Path to the log file. If not provided, reads from stdin.
    --startup-time (str, optional): Startup time (e.g., "2025-10-04 12:00:00").
        If not provided, the first timestamp in the log is used.

Options:
    -i, --ignore-case: Ignore case in regex matching.
    -v, --invert-match: Invert match (show non-matching lines).
    -A NUM: Show NUM lines after match.
    -B NUM: Show NUM lines before match.
    -C NUM: Show NUM lines around match.
    --color: Highlight matches in color (default: auto, use --color=never to disable).

Examples:
    # Search for "ERROR" in a log file after a specific time:
    loggrep.py "ERROR" --file /var/log/syslog --startup-time "2025-10-04 12:00:00"

    # Search for "ERROR" or "WARN" in stdin, case-insensitive, with context:
    cat /var/log/syslog | loggrep.py -i "ERROR" "WARN" -C 2

    # Invert match (like grep -v):
    loggrep.py -v "OK" --file /var/log/syslog

Features:
    - Flexible timestamp parsing: Supports Unix syslog, Android logcat, and other common formats.
    - Efficient: Only processes lines after the startup time.
    - Color output: Highlights matches for better readability.
    - Context lines: Show lines before/after matches.
    - Multiple patterns: Search for multiple patterns at once.
    - User-friendly: Clear CLI interface and error messages.

Dependencies:
    - python-dateutil: For flexible timestamp parsing.
      Install with: pip install python-dateutil
    - colorama: For color output.
      Install with: pip install colorama
"""

import argparse
import re
import sys
from dateutil import parser
from typing import Optional, TextIO, List
from collections import deque
try:
    from colorama import Fore, Style, init
    init()
    COLOR_AVAILABLE = True
except ImportError:
    COLOR_AVAILABLE = False

def detect_timestamp_format(line: str) -> Optional[str]:
    """Detect and extract timestamp from a log line."""
    # Supports Unix syslog, Android logcat, and other common formats
    timestamp_re = (
        r'^\s*([A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}|'  # Oct  5 00:00:02
        r'[A-Za-z]{3}\s+\d{1,2},?\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}(?:\.\d+)?|'  # Oct 05, 2025 00:00:02.123
        r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?|'  # 2025-10-05 00:00:02.123
        r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?|'  # 10/05/2025 00:00:02.123
        r'\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?|'  # 05 Oct 2025 00:00:02.123
        r'\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)'  # 10-05 00:00:02.123
    )
    match = re.search(timestamp_re, line)
    if match:
        return match.group(1)
    return None

def parse_timestamp(ts_str: str):
    """Parse a timestamp string into a datetime object."""
    try:
        return parser.parse(ts_str)
    except ValueError:
        return None

def highlight_match(line: str, match: re.Match, use_color: bool) -> str:
    """Highlight the matched part of the line."""
    if not use_color or not COLOR_AVAILABLE:
        return line
    return line.replace(match.group(), f"{Fore.RED}{match.group()}{Style.RESET_ALL}")

def main():
    arg_parser = argparse.ArgumentParser(description="Grep log file after a specific startup time.")
    arg_parser.add_argument("patterns", nargs="+", help="Regex pattern(s) to search for")
    arg_parser.add_argument("--file", help="Log file to search (default: stdin)", default=None)
    arg_parser.add_argument("--startup-time", help="Startup time (e.g., '2025-10-04 12:00:00').", default=None)
    arg_parser.add_argument("-i", "--ignore-case", action="store_true", help="Ignore case")
    arg_parser.add_argument("-v", "--invert-match", action="store_true", help="Invert match")
    arg_parser.add_argument("-A", type=int, default=0, help="Show N lines after match")
    arg_parser.add_argument("-B", type=int, default=0, help="Show N lines before match")
    arg_parser.add_argument("-C", type=int, default=0, help="Show N lines around match")
    arg_parser.add_argument("--color", choices=["always", "never", "auto"], default="auto", help="Color output")
    args = arg_parser.parse_args()

    # Compile regex pattern(s)
    flags = re.IGNORECASE if args.ignore_case else 0
    try:
        pattern = re.compile("|".join(args.patterns), flags)
    except re.error as e:
        print(f"Error: Invalid regex pattern: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine if color should be used
    use_color = args.color == "always" or (args.color == "auto" and COLOR_AVAILABLE and sys.stdout.isatty())

    # Handle context lines
    before_lines = deque(maxlen=args.B)
    after_lines = deque(maxlen=args.A)
    context = args.A + args.B

    startup_time = parse_timestamp(args.startup_time) if args.startup_time else None
    input_stream = open(args.file, "r") if args.file else sys.stdin
    first_timestamp = None

    try:
        for line in input_stream:
            ts_str = detect_timestamp_format(line)
            if ts_str:
                ts = parse_timestamp(ts_str)
                if ts and not first_timestamp:
                    first_timestamp = ts
                if not startup_time:
                    startup_time = first_timestamp
                if ts and ts >= startup_time:
                    match = pattern.search(line)
                    if (match and not args.invert_match) or (not match and args.invert_match):
                        if args.C:
                            for bline in before_lines:
                                print(bline, end="")
                            print(highlight_match(line, match, use_color) if match else line, end="")
                            after_lines.clear()
                        elif args.B:
                            for bline in before_lines:
                                print(bline, end="")
                            print(highlight_match(line, match, use_color) if match else line, end="")
                            before_lines.clear()
                        else:
                            print(highlight_match(line, match, use_color) if match else line, end="")
                    elif args.A and match and not args.invert_match:
                        after_lines.append(line)
                    elif args.B and ((match and not args.invert_match) or (not match and args.invert_match)):
                        before_lines.clear()
                    else:
                        if args.B:
                            before_lines.append(line)
                        if args.A and after_lines:
                            print(after_lines.popleft(), end="")
            elif args.A and after_lines:
                print(after_lines.popleft(), end="")
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if args.file:
            input_stream.close()

if __name__ == "__main__":
    main()

