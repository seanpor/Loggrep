#!/usr/bin/env python3
"""
Command-line interface for loggrep.

A powerful command-line tool for searching log files with timestamp awareness,
regex support, invert match, context lines, and color output.
"""

import argparse
import sys
from datetime import datetime
from typing import Any, List, Optional

from . import __version__
from .core import LogSearcher


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="loggrep",
        description="Search log files with timestamp awareness - like grep but for logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic pattern search
  loggrep "ERROR" --file application.log

  # Search from stdin (like grep)
  cat application.log | loggrep "ERROR"

  # Only show matches after specific time
  loggrep "ERROR" --file app.log --startup-time "2025-01-15 14:30:00"

  # Multiple patterns with context
  loggrep "ERROR" "WARN" --file app.log -C 3

  # Case-insensitive search with invert match
  loggrep -i -v "debug" --file app.log

  # Android logcat filtering with live flag
  adb logcat | loggrep "ActivityManager.*MyApp" --live

Supported timestamp formats:
  - Unix syslog: Oct  5 14:30:02
  - ISO 8601: 2025-10-05 14:30:02.123
  - Android logcat: 10-05 14:30:02.123
  - Custom: Oct 05, 2025 14:30:02

For more information, visit: https://github.com/seanpor/Loggrep
        """,
    )

    parser.add_argument(
        "patterns",
        nargs="+",
        help="Regex pattern(s) to search for. Multiple patterns are OR'd together.",
    )

    parser.add_argument(
        "--file", help="Log file to search (default: stdin)", default=None
    )
    parser.add_argument(
        "--startup-time",
        help=(
            "Only show matches after this time. Supports various formats: "
            "'2025-10-04 12:00:00', 'Oct 4 12:00:00', '10 minutes ago'."
        ),
        default=None,
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use current time as startup time for filtering.",
    )
    parser.add_argument(
        "--no-live",
        action="store_true",
        help="Disable timestamp filtering. Show all matching lines.",
    )

    parser.add_argument(
        "-i",
        "--ignore-case",
        action="store_true",
        help="Ignore case distinctions (like grep -i).",
    )
    parser.add_argument(
        "-v",
        "--invert-match",
        action="store_true",
        help="Show lines that do NOT match (like grep -v).",
    )

    parser.add_argument(
        "-A",
        "--after-context",
        type=int,
        default=0,
        metavar="NUM",
        help="Show NUM lines after each match (like grep -A).",
    )
    parser.add_argument(
        "-B",
        "--before-context",
        type=int,
        default=0,
        metavar="NUM",
        help="Show NUM lines before each match (like grep -B).",
    )
    parser.add_argument(
        "-C",
        "--context",
        type=int,
        default=0,
        metavar="NUM",
        help="Show NUM lines before and after each match (like grep -C).",
    )

    parser.add_argument(
        "--color",
        choices=["always", "never", "auto"],
        default="auto",
        help="Control colored output (default: auto)",
    )
    parser.add_argument("--version", action="version", version=f"loggrep {__version__}")

    return parser


def determine_color_usage(color_arg: str) -> bool:
    """Determine whether to use colored output."""
    if color_arg == "always":
        return True
    if color_arg == "never":
        return False
    try:
        from colorama import init

        init()
        return sys.stdout.isatty()
    except ImportError:
        return False


def _file_error(icon: str, path: str, message: str, tip: str) -> int:
    """Print a file-related error with a tip and return exit code 2."""
    print(f"{icon} loggrep: '{path}': {message}", file=sys.stderr)
    print(f"💡 Tip: {tip}", file=sys.stderr)
    return 2


def main(
    argv: Optional[List[str]] = None,
    startup_time_override: Optional[Any] = None,
) -> int:
    """Main entry point for the loggrep command-line tool."""
    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        use_color = determine_color_usage(args.color)

        searcher = LogSearcher(
            patterns=args.patterns,
            ignore_case=args.ignore_case,
            invert_match=args.invert_match,
            before_context=args.before_context,
            after_context=args.after_context,
            context=args.context,
            use_color=use_color,
            startup_time=args.startup_time,
        )

        # Startup time priority: --startup-time > --no-live > override > default
        if args.no_live:
            searcher.startup_time = None
        elif not args.startup_time:
            if startup_time_override:
                searcher.startup_time = startup_time_override
            else:
                searcher.startup_time = datetime.now()

        try:
            if args.file:
                results = searcher.search_file(args.file)
            else:
                results = searcher.search_stdin()

            for line in results:
                print(line, end="")

        except FileNotFoundError:
            return _file_error(
                "🚫",
                args.file,
                "No such file or directory",
                "Check the file path and ensure the file exists",
            )
        except PermissionError:
            return _file_error(
                "🔒",
                args.file,
                "Permission denied",
                "Try running with sudo or check file permissions",
            )
        except IsADirectoryError:
            return _file_error(
                "📁",
                args.file,
                "Is a directory",
                "Specify a file, not a directory. Use 'find' to search directories",
            )
        except BrokenPipeError:
            return 0
        except UnicodeDecodeError as e:
            return _file_error(
                "🔤",
                args.file,
                f"Unable to decode: {e}",
                "File may be binary or use an unsupported encoding",
            )

    except ValueError as e:
        error_msg = str(e)
        if "pattern" in error_msg.lower() or "regex" in error_msg.lower():
            print(f"🔍 loggrep: Invalid regex pattern: {e}", file=sys.stderr)
            print(
                "💡 Tip: Check your regex syntax or use simple text patterns",
                file=sys.stderr,
            )
        else:
            print(f"❌ loggrep: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"💥 loggrep: Unexpected error: {e}", file=sys.stderr)
        print(
            "🐛 Please report this issue at: https://github.com/seanpor/Loggrep/issues",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
