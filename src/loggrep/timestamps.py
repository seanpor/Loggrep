"""
Timestamp detection and parsing functionality for loggrep.

Supports multiple common log timestamp formats including Unix syslog,
ISO 8601, Android logcat, web server logs, and custom formats.

PERFORMANCE OPTIMIZATIONS:
- Cached compiled regex patterns for faster detection
- Fast-path parsing for common formats before using dateutil
- Pattern ordering by frequency for better average-case performance
"""

import re
from datetime import datetime
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional

from dateutil import parser as dateutil_parser

# Pre-compiled regex patterns for better performance
COMPILED_PATTERNS: Optional[List[Any]] = None


def _get_compiled_patterns() -> List[Any]:
    """Get compiled regex patterns, creating them once for better performance."""
    global COMPILED_PATTERNS
    if COMPILED_PATTERNS is None:
        COMPILED_PATTERNS = [
            (re.compile(pattern["pattern"]), pattern) for pattern in TIMESTAMP_PATTERNS  # type: ignore
        ]
    return COMPILED_PATTERNS


# Common timestamp patterns ordered by frequency for better performance
TIMESTAMP_PATTERNS = [
    {
        "name": "iso8601_basic",
        "pattern": r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
        "description": "ISO 8601 basic (2025-10-05 14:30:02.123)",
        "fast_parse": lambda s: (
            datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S") if len(s) >= 19 else None
        ),
    },
    {
        "name": "unix_syslog",
        "pattern": r"^\s*([A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})",
        "description": "Unix syslog format (Oct  5 14:30:02)",
        "fast_parse": None,  # Complex format, use dateutil
    },
    {
        "name": "iso8601_extended",
        "pattern": r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)",
        "description": "ISO 8601 extended (2025-10-05T14:30:02.123Z)",
        "fast_parse": lambda s: (
            datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
            if len(s) >= 19 and "T" in s
            else None
        ),
    },
    {
        "name": "android_logcat",
        "pattern": r"(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
        "description": "Android logcat (10-05 14:30:02.123)",
        "fast_parse": None,  # Need year, use dateutil
    },
    {
        "name": "nginx_default",
        "pattern": r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})",
        "description": "Nginx default (2025/10/05 14:30:02)",
        "fast_parse": lambda s: (
            datetime.strptime(s, "%Y/%m/%d %H:%M:%S") if len(s) == 19 else None
        ),
    },
    {
        "name": "us_date_time",
        "pattern": r"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
        "description": "US date format (10/05/2025 14:30:02.123)",
        "fast_parse": lambda s: (
            datetime.strptime(s[:19], "%m/%d/%Y %H:%M:%S") if len(s) >= 19 else None
        ),
    },
    {
        "name": "apache_common",
        "pattern": r"(\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2})",
        "description": "Apache Common Log (05/Oct/2025:14:30:02)",
        "fast_parse": lambda s: (
            datetime.strptime(s, "%d/%b/%Y:%H:%M:%S") if len(s) == 20 else None
        ),
    },
    {
        "name": "rfc3339",
        "pattern": r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)",
        "description": "RFC 3339 (2025-10-05T14:30:02.123+00:00)",
        "fast_parse": None,  # Complex timezone handling
    },
    {
        "name": "custom_readable",
        "pattern": r"([A-Za-z]{3}\s+\d{1,2},?\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}(?:\.\d+)?)",
        "description": "Custom readable (Oct 05, 2025 14:30:02.123)",
        "fast_parse": None,  # Variable format, use dateutil
    },
    {
        "name": "eu_date_time",
        "pattern": r"(\d{1,2}\.\d{1,2}\.\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
        "description": "European date format (05.10.2025 14:30:02.123)",
        "fast_parse": lambda s: (
            datetime.strptime(s[:19], "%d.%m.%Y %H:%M:%S") if len(s) >= 19 else None
        ),
    },
]


@lru_cache(maxsize=1024)
def detect_timestamp_format_cached(line: str) -> Optional[str]:
    """Cached version of timestamp detection for better performance.

    Uses LRU cache to avoid re-parsing similar log lines.
    """
    return detect_timestamp_format(line)


def detect_timestamp_format(line: str) -> Optional[str]:
    """Detect and extract timestamp from a log line using optimized patterns.

    Args:
        line: A line from a log file

    Returns:
        The timestamp string if found, None otherwise

    Performance optimizations:
        - Pre-compiled regex patterns
        - Patterns ordered by frequency
        - Early termination on first match
    """
    # Use pre-compiled patterns for better performance
    compiled_patterns = _get_compiled_patterns()

    # Try each pattern in order of likelihood for performance
    for compiled_regex, pattern_info in compiled_patterns:
        match = compiled_regex.search(line)
        if match:
            return match.group(1)  # type: ignore
    return None


@lru_cache(maxsize=512)
def parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse a timestamp string into a datetime object with performance optimizations.

    Args:
        ts_str: Timestamp string to parse

    Returns:
        datetime object if parsing succeeds, None otherwise

    Performance optimizations:
        - LRU cache for repeated timestamps
        - Fast-path parsing for common formats
        - Fallback to dateutil for complex formats
        - Timezone normalization
    """
    if not ts_str or not ts_str.strip():
        return None

    ts_str = ts_str.strip()

    # Try fast-path parsing for common formats first
    for pattern_info in TIMESTAMP_PATTERNS:
        fast_parse = pattern_info.get("fast_parse")  # type: ignore
        if fast_parse:
            try:
                result = fast_parse(ts_str)
                if result:
                    return result  # type: ignore
            except (ValueError, TypeError):
                continue

    # Fallback to dateutil for complex formats
    try:
        parsed_dt = dateutil_parser.parse(ts_str)

        # Convert timezone-aware to naive datetime for consistent comparison
        if parsed_dt.tzinfo is not None:
            return parsed_dt.replace(tzinfo=None)

        return parsed_dt

    except (ValueError, TypeError, OverflowError):
        return None


def get_supported_formats() -> List[Dict[str, str]]:
    """Get list of supported timestamp formats for documentation.

    Returns:
        List of dictionaries with format information
    """
    return [
        {"name": p["name"], "description": p["description"]} for p in TIMESTAMP_PATTERNS  # type: ignore
    ]
