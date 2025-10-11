"""
Loggrep - A powerful command-line tool for timestamp-aware log searching.

Loggrep combines the power of grep with intelligent timestamp filtering,
making it perfect for analyzing logs from specific points in time.
"""

__version__ = "1.0.0"
__author__ = "Sean"
__email__ = "seanpor at acm.org"
__license__ = "Apache-2.0"

from .core import LogSearcher
from .timestamps import detect_timestamp_format, parse_timestamp

__all__ = [
    "LogSearcher",
    "detect_timestamp_format",
    "parse_timestamp",
    "__version__",
]
