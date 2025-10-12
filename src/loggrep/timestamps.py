"""
Timestamp detection and parsing functionality for loggrep.

Supports multiple common log timestamp formats including Unix syslog,
ISO 8601, Android logcat, web server logs, and custom formats.
"""

import re
from typing import Optional, List, Dict
from datetime import datetime
from dateutil import parser as dateutil_parser


# Common timestamp patterns for better performance and debugging
TIMESTAMP_PATTERNS = [
    {
        "name": "unix_syslog",
        "pattern": r"^\s*([A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})",
        "description": "Unix syslog format (Oct  5 14:30:02)"
    },
    {
        "name": "iso8601_basic",
        "pattern": r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
        "description": "ISO 8601 basic (2025-10-05 14:30:02.123)"
    },
    {
        "name": "iso8601_extended",
        "pattern": r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)",
        "description": "ISO 8601 extended (2025-10-05T14:30:02.123Z)"
    },
    {
        "name": "android_logcat",
        "pattern": r"(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
        "description": "Android logcat (10-05 14:30:02.123)"
    },
    {
        "name": "us_date_time",
        "pattern": r"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
        "description": "US date format (10/05/2025 14:30:02.123)"
    },
    {
        "name": "rfc3339",
        "pattern": r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)",
        "description": "RFC 3339 (2025-10-05T14:30:02.123+00:00)"
    },
    {
        "name": "apache_common",
        "pattern": r"(\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2})",
        "description": "Apache Common Log (05/Oct/2025:14:30:02)"
    },
    {
        "name": "nginx_default",
        "pattern": r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})",
        "description": "Nginx default (2025/10/05 14:30:02)"
    },
    {
        "name": "custom_readable",
        "pattern": r"([A-Za-z]{3}\s+\d{1,2},?\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}(?:\.\d+)?)",
        "description": "Custom readable (Oct 05, 2025 14:30:02.123)"
    },
    {
        "name": "eu_date_time",
        "pattern": r"(\d{1,2}\.\d{1,2}\.\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
        "description": "European date format (05.10.2025 14:30:02.123)"
    }
]


def detect_timestamp_format(line: str) -> Optional[str]:
    """Detect and extract timestamp from a log line using optimized patterns.

    Args:
        line: A line from a log file

    Returns:
        The timestamp string if found, None otherwise

    Supported formats:
        - Unix syslog: Oct  5 14:30:02
        - ISO 8601: 2025-10-05 14:30:02.123 or 2025-10-05T14:30:02.123Z
        - Android logcat: 10-05 14:30:02.123
        - Apache logs: 05/Oct/2025:14:30:02
        - Nginx logs: 2025/10/05 14:30:02
        - US format: 10/05/2025 14:30:02.123
        - EU format: 05.10.2025 14:30:02.123
        - Custom: Oct 05, 2025 14:30:02
    """
    # Try each pattern in order of likelihood for performance
    for pattern_info in TIMESTAMP_PATTERNS:
        match = re.search(pattern_info["pattern"], line)
        if match:
            return match.group(1)
    return None


def parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse a timestamp string into a datetime object using robust parsing.

    Args:
        ts_str: Timestamp string to parse

    Returns:
        datetime object if parsing succeeds, None otherwise
        
    Note:
        Uses dateutil.parser for flexible parsing of various formats.
        Handles timezone information when present.
    """
    if not ts_str or not ts_str.strip():
        return None
        
    try:
        # dateutil.parser is very flexible and handles most formats
        return dateutil_parser.parse(ts_str)
    except (ValueError, TypeError, OverflowError):
        # Fallback: try some manual parsing for edge cases
        try:
            # Handle some common problematic formats manually
            ts_str = ts_str.strip()
            
            # Handle Apache log format specifically
            if "/" in ts_str and ":" in ts_str:
                # Try Apache format: 05/Oct/2025:14:30:02
                if re.match(r"\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}", ts_str):
                    return datetime.strptime(ts_str, "%d/%b/%Y:%H:%M:%S")
            
            return None
        except (ValueError, TypeError):
            return None


def get_supported_formats() -> List[Dict[str, str]]:
    """Get list of supported timestamp formats for documentation.
    
    Returns:
        List of dictionaries with format information
    """
    return [{"name": p["name"], "description": p["description"]} for p in TIMESTAMP_PATTERNS]
