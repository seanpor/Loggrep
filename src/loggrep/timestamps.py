"""
Timestamp detection and parsing functionality for loggrep.

Supports multiple common log timestamp formats including Unix syslog,
ISO 8601, Android logcat, and custom formats.
"""

import re
from typing import Optional

from dateutil import parser


def detect_timestamp_format(line: str) -> Optional[str]:
    """Detect and extract timestamp from a log line.

    Args:
        line: A line from a log file

    Returns:
        The timestamp string if found, None otherwise

    Supported formats:
        - Unix syslog: Oct  5 00:00:02
        - ISO 8601: 2025-10-05 00:00:02.123
        - Android logcat: 10-05 00:00:02.123
        - Custom formats: Oct 05, 2025 00:00:02
    """
    # Supports Unix syslog, Android logcat, and other common formats
    timestamp_re = (
        r"^\s*([A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}|"  # Oct  5 00:00:02
        r"[A-Za-z]{3}\s+\d{1,2},?\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}(?:\.\d+)?|"  # Oct 05, 2025 00:00:02.123
        r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?|"  # 2025-10-05 00:00:02.123
        r"\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?|"  # 10/05/2025 00:00:02.123
        r"\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?|"  # 05 Oct 2025 00:00:02.123
        r"\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)"  # 10-05 00:00:02.123
    )
    match = re.search(timestamp_re, line)
    if match:
        return match.group(1)
    return None


def parse_timestamp(ts_str: str):
    """Parse a timestamp string into a datetime object.

    Args:
        ts_str: Timestamp string to parse

    Returns:
        datetime object if parsing succeeds, None otherwise
    """
    try:
        return parser.parse(ts_str)
    except ValueError:
        return None
