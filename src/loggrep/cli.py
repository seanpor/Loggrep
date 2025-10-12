#!/usr/bin/env python3
"""
Command-line interface for loggrep.

A powerful command-line tool for searching log files with timestamp awareness,
regex support, invert match, context lines, and color output.
"""

import argparse
import sys
from typing import Optional, List


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

    # Positional arguments
    parser.add_argument(
        "patterns",
        nargs="+",
        help="Regex pattern(s) to search for. Multiple patterns are OR'd together.",
    )

    # Input options
    parser.add_argument(
        "--file", help="Log file to search (default: stdin)", default=None
    )
    parser.add_argument(
        "--startup-time",
        help="Only show matches after this time. Supports various formats: '2025-10-04 12:00:00', 'Oct 4 12:00:00', '10 minutes ago'. For stdin, consider using --live for real-time filtering.",
        default=None,
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help="For stdin input, use current time as startup time. Perfect for live log streaming (e.g., 'adb logcat | loggrep pattern --live').",
    )

    # Search options
    parser.add_argument(
        "-i",
        "--ignore-case",
        action="store_true",
        help="Ignore case distinctions in both patterns and input text (like grep -i).",
    )
    parser.add_argument(
        "-v",
        "--invert-match",
        action="store_true",
        help="Show lines that do NOT match any of the patterns (like grep -v). Useful for filtering out noise.",
    )

    # Context options
    parser.add_argument(
        "-A",
        "--after-context",
        type=int,
        default=0,
        metavar="NUM",
        help="Show NUM lines after each match (like grep -A). Useful for seeing consequences of errors.",
    )
    parser.add_argument(
        "-B",
        "--before-context",
        type=int,
        default=0,
        metavar="NUM",
        help="Show NUM lines before each match (like grep -B). Useful for seeing what led to errors.",
    )
    parser.add_argument(
        "-C",
        "--context",
        type=int,
        default=0,
        metavar="NUM",
        help="Show NUM lines before and after each match (like grep -C). Equivalent to -A NUM -B NUM.",
    )

    # Output options
    parser.add_argument(
        "--color",
        choices=["always", "never", "auto"],
        default="auto",
        help="Control colored output (default: auto)",
    )

    # Version
    parser.add_argument("--version", action="version", version=f"loggrep {__version__}")

    return parser


def determine_color_usage(color_arg: str) -> bool:
    """Determine whether to use colored output based on arguments and environment."""
    if color_arg == "always":
        return True
    elif color_arg == "never":
        return False
    else:  # auto
        try:
            from colorama import init

            init()
            return sys.stdout.isatty()
        except ImportError:
            return False


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the loggrep command-line tool."""
    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        # Determine color usage
        use_color = determine_color_usage(args.color)

        # Create searcher
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

        # Search and output results
        try:
            if args.file:
                results = searcher.search_file(args.file)
            else:
                # For stdin, use live mode if specified
                if args.live and not args.startup_time:
                    from datetime import datetime

                    searcher.startup_time = datetime.now()
                results = searcher.search_stdin()

            for line in results:
                print(line, end="")

        except FileNotFoundError:
            print(f"🚫 loggrep: '{args.file}': No such file or directory", file=sys.stderr)
            print("💡 Tip: Check the file path and ensure the file exists", file=sys.stderr)
            return 2
        except PermissionError:
            print(f"🔒 loggrep: '{args.file}': Permission denied", file=sys.stderr)
            print("💡 Tip: Try running with sudo or check file permissions", file=sys.stderr)
            return 2
        except IsADirectoryError:
            print(f"📁 loggrep: '{args.file}': Is a directory", file=sys.stderr)
            print("💡 Tip: Specify a file, not a directory. Use 'find' to search directories", file=sys.stderr)
            return 2
        except BrokenPipeError:
            # Handle broken pipe gracefully (e.g., when piping to head)
            return 0
        except UnicodeDecodeError as e:
            print(f"🔤 loggrep: Unable to decode file '{args.file}': {e}", file=sys.stderr)
            print("💡 Tip: File may be binary or use an unsupported encoding", file=sys.stderr)
            return 2

    except ValueError as e:
        error_msg = str(e)
        if "startup-time" in error_msg.lower():
            print(f"⏰ loggrep: Invalid timestamp format: {e}", file=sys.stderr)
            print("💡 Tip: Try formats like '2025-10-05 14:30:00' or 'Oct 5 14:30:00'", file=sys.stderr)
        elif "pattern" in error_msg.lower() or "regex" in error_msg.lower():
            print(f"🔍 loggrep: Invalid regex pattern: {e}", file=sys.stderr)
            print("💡 Tip: Check your regex syntax or use simple text patterns", file=sys.stderr)
        else:
            print(f"❌ loggrep: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"💥 loggrep: Unexpected error: {e}", file=sys.stderr)
        print("🐛 Please report this issue at: https://github.com/seanpor/Loggrep/issues", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
