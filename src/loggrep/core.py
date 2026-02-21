"""
Core search functionality for loggrep.

Contains the main LogSearcher class that handles pattern matching,
timestamp filtering, and context line management.
"""

import io
import re
import sys
from collections import deque
from typing import Iterator, List, Optional, TextIO

from .timestamps import detect_timestamp_format, parse_timestamp

try:
    from colorama import Fore, Style, init

    init()
    COLOR_AVAILABLE = True
except ImportError:
    COLOR_AVAILABLE = False

NO_TIMESTAMP_THRESHOLD = 3


class LogSearcher:
    """Main class for searching logs with timestamp awareness and pattern matching."""

    def __init__(
        self,
        patterns: List[str],
        ignore_case: bool = False,
        invert_match: bool = False,
        before_context: int = 0,
        after_context: int = 0,
        context: int = 0,
        use_color: bool = False,
        startup_time: Optional[str] = None,
    ):
        self.invert_match = invert_match
        self.before_context = max(before_context, context)
        self.after_context = max(after_context, context)
        self.use_color = use_color and COLOR_AVAILABLE
        self.startup_time = parse_timestamp(startup_time) if startup_time else None

        flags = re.IGNORECASE if ignore_case else 0
        try:
            if len(patterns) == 1:
                self.pattern = re.compile(patterns[0], flags)
            else:
                self.pattern = re.compile("|".join(f"({p})" for p in patterns), flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

    def highlight_match(self, line: str, match: re.Match) -> str:
        """Highlight the matched part of the line with color."""
        if not self.use_color or not COLOR_AVAILABLE:
            return line
        return line.replace(
            match.group(), f"{Fore.RED}{match.group()}{Style.RESET_ALL}"
        )

    def search_stream(self, input_stream: TextIO) -> Iterator[str]:
        """Search through a stream of log lines.

        Yields lines that match the search criteria, respecting
        timestamp filtering and context line settings.
        """
        before_buffer: deque = deque(
            maxlen=self.before_context if self.before_context > 0 else None
        )
        after_count = 0
        startup_time = self.startup_time
        in_range = not startup_time
        no_timestamp_lines = 0
        has_seen_timestamp = False

        for line in input_stream:
            # Timestamp filtering
            if startup_time:
                ts_str = detect_timestamp_format(line)
                if ts_str:
                    has_seen_timestamp = True
                    ts = parse_timestamp(ts_str)
                    if ts:
                        in_range = ts >= startup_time
                else:
                    no_timestamp_lines += 1
                    if (
                        no_timestamp_lines >= NO_TIMESTAMP_THRESHOLD
                        and not has_seen_timestamp
                    ):
                        # No timestamps found — disable filtering
                        in_range = True
                        startup_time = None

            if not in_range:
                continue

            match = self.pattern.search(line)
            is_match = bool(match) != self.invert_match

            # Yield after-context from previous matches
            if after_count > 0:
                yield line
                after_count -= 1

            if is_match:
                # Yield before-context lines
                if self.before_context:
                    for before_line in before_buffer:
                        yield before_line

                # Yield the match line (with highlighting if applicable)
                if match:
                    yield self.highlight_match(line, match)
                else:
                    yield line

                if self.after_context:
                    after_count = self.after_context

            # Buffer lines for potential before-context
            if self.before_context:
                before_buffer.append(line)

    def search_file(self, file_path: str) -> Iterator[str]:
        """Search through a log file."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            yield from self.search_stream(f)

    def search_stdin(self) -> Iterator[str]:
        """Search through stdin with error-tolerant encoding."""
        stdin_stream = io.TextIOWrapper(
            sys.stdin.buffer, encoding="utf-8", errors="replace"
        )
        yield from self.search_stream(stdin_stream)
