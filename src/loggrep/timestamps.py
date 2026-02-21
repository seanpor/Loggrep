"""
Timestamp detection and parsing for loggrep.

Supports multiple common log timestamp formats including Unix syslog,
ISO 8601, Android logcat, web server logs, and custom formats.
"""

import re
from datetime import datetime
from functools import lru_cache
from typing import Any, List, Optional

from dateutil import parser as dateutil_parser

# Timestamp patterns ordered by frequency for better average-case performance.
# Each entry has a compiled regex and an optional fast-path parser.
TIMESTAMP_PATTERNS: List[Any] = [
    {
        "name": "iso8601_basic",
        "pattern": r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
        "fast_parse": lambda s: (
            datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S") if len(s) >= 19 else None
        ),
    },
    {
        "name": "unix_syslog",
        "pattern": r"^\s*([A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})",
        "fast_parse": None,
    },
    {
        "name": "iso8601_extended",
        "pattern": r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)",
        "fast_parse": lambda s: (
            datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
            if len(s) >= 19 and "T" in s
            else None
        ),
    },
    {
        "name": "android_logcat",
        "pattern": r"(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
        "fast_parse": None,
    },
    {
        "name": "nginx_default",
        "pattern": r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})",
        "fast_parse": lambda s: (
            datetime.strptime(s, "%Y/%m/%d %H:%M:%S") if len(s) == 19 else None
        ),
    },
    {
        "name": "us_date_time",
        "pattern": r"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
        "fast_parse": lambda s: (
            datetime.strptime(s[:19], "%m/%d/%Y %H:%M:%S") if len(s) >= 19 else None
        ),
    },
    {
        "name": "apache_common",
        "pattern": r"(\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2})",
        "fast_parse": lambda s: (
            datetime.strptime(s, "%d/%b/%Y:%H:%M:%S") if len(s) == 20 else None
        ),
    },
    {
        "name": "custom_readable",
        "pattern": r"([A-Za-z]{3}\s+\d{1,2},?\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}(?:\.\d+)?)",
        "fast_parse": None,
    },
    {
        "name": "eu_date_time",
        "pattern": r"(\d{1,2}\.\d{1,2}\.\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
        "fast_parse": lambda s: (
            datetime.strptime(s[:19], "%d.%m.%Y %H:%M:%S") if len(s) >= 19 else None
        ),
    },
]

# Compile patterns once at module load
_COMPILED_PATTERNS = [(re.compile(p["pattern"]), p) for p in TIMESTAMP_PATTERNS]


def detect_timestamp_format(line: str) -> Optional[str]:
    """Detect and extract a timestamp from a log line.

    Tries each compiled pattern in order of likelihood and returns
    the first match.

    Returns:
        The timestamp string if found, None otherwise.
    """
    for compiled_regex, _pattern_info in _COMPILED_PATTERNS:
        match = compiled_regex.search(line)
        if match:
            return match.group(1)
    return None


@lru_cache(maxsize=512)
def parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse a timestamp string into a datetime object.

    Uses fast-path strptime for common formats, falling back
    to dateutil for complex ones (syslog, logcat, etc.).

    Returns:
        datetime object if parsing succeeds, None otherwise.
    """
    if not ts_str or not ts_str.strip():
        return None

    ts_str = ts_str.strip()

    # Try fast-path parsing first
    for pattern_info in TIMESTAMP_PATTERNS:
        fast_parse = pattern_info.get("fast_parse")
        if fast_parse:
            try:
                result = fast_parse(ts_str)
                if result:
                    return result
            except (ValueError, TypeError):
                continue

    # Fallback to dateutil for complex formats
    try:
        parsed_dt = dateutil_parser.parse(ts_str)
        if parsed_dt.tzinfo is not None:
            return parsed_dt.replace(tzinfo=None)
        return parsed_dt
    except (ValueError, TypeError, OverflowError):
        return None
