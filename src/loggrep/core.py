"""
Core search functionality for loggrep.

Contains the main LogSearcher class that handles pattern matching,
timestamp filtering, and context line management.
"""

import re
import sys
from collections import deque
from datetime import datetime
from typing import Iterator, List, Optional, TextIO

from .timestamps import detect_timestamp_format, parse_timestamp

try:
    from colorama import Fore, Style, init

    init()
    COLOR_AVAILABLE = True
except ImportError:
    COLOR_AVAILABLE = False


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
        """Initialize the LogSearcher.

        Args:
            patterns: List of regex patterns to search for
            ignore_case: Whether to ignore case in pattern matching
            invert_match: Whether to invert the match (show non-matching lines)
            before_context: Number of lines to show before matches
            after_context: Number of lines to show after matches
            context: Number of lines to show around matches (overrides before/after)
            use_color: Whether to use colored output
            startup_time: Only show matches after this timestamp
        """
        self.invert_match = invert_match
        self.before_context = max(before_context, context)
        self.after_context = max(after_context, context)
        self.use_color = use_color and COLOR_AVAILABLE
        self.startup_time = parse_timestamp(startup_time) if startup_time else None

        # Compile regex pattern(s)
        flags = re.IGNORECASE if ignore_case else 0
        try:
            self.pattern = re.compile("|".join(patterns), flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

    def highlight_match(self, line: str, match: re.Match) -> str:
        """Highlight the matched part of the line with color.

        Args:
            line: The line containing the match
            match: The regex match object

        Returns:
            Line with highlighted match, or original line if no color
        """
        if not self.use_color or not COLOR_AVAILABLE:
            return line
        return line.replace(
            match.group(), f"{Fore.RED}{match.group()}{Style.RESET_ALL}"
        )

    def search_stream(
        self, input_stream: TextIO, use_current_time_default: bool = False
    ) -> Iterator[str]:
        """Search through a stream of log lines.

        Args:
            input_stream: Input stream to search through
            use_current_time_default: If True and no startup_time specified, use current time

        Yields:
            Lines that match the search criteria with context
        """
        # Handle context lines
        before_buffer: deque = deque(
            maxlen=self.before_context if self.before_context > 0 else None
        )
        after_count = 0
        first_timestamp = None
        startup_time = self.startup_time

        # If no startup time specified and we're reading from stdin (streaming), use current time
        # But only if the input appears to be live/streaming (i.e., we detect it's potentially real-time)
        if not startup_time and use_current_time_default:
            # For stdin, we'll be more conservative and only use current time if explicitly needed
            # The caller can control this behavior
            startup_time = datetime.now()

        # Read all lines to enable proper context handling
        try:
            lines = list(input_stream)
        except MemoryError:
            # For very large files, fall back to streaming mode (TODO: implement smart streaming)
            lines = input_stream  # type: ignore

        in_range = not startup_time  # If no startup time, process all lines

        for i, line in enumerate(lines):
            ts_str = detect_timestamp_format(line)
            ts = None

            # Parse timestamp if found
            if ts_str:
                ts = parse_timestamp(ts_str)
                if ts and not first_timestamp:
                    first_timestamp = ts
                # Use first timestamp as startup time if none specified and not using current time
                if (
                    not startup_time
                    and not use_current_time_default
                    and first_timestamp
                ):
                    startup_time = first_timestamp
                    in_range = True
                # Check if we're past startup time
                if startup_time and ts and ts >= startup_time:
                    in_range = True
                elif startup_time and ts and ts < startup_time:
                    in_range = False

            # Process line if we're in the time range or no timestamp filtering
            if in_range or not startup_time:
                match = self.pattern.search(line)
                is_match = (match and not self.invert_match) or (
                    not match and self.invert_match
                )

                # Handle after-context from previous matches
                if after_count > 0:
                    yield line
                    after_count -= 1

                if is_match:
                    # Yield before-context lines
                    if self.before_context:
                        context_lines = self.before_context
                        for before_line in list(before_buffer)[-context_lines:]:
                            yield before_line

                    # Yield the match line (with highlighting if applicable)
                    if match:
                        yield self.highlight_match(line, match)
                    else:
                        yield line

                    # Set up after-context
                    if self.after_context:
                        after_count = self.after_context

                # Always buffer lines for potential before-context
                if self.before_context:
                    before_buffer.append(line)

    def search_file(self, file_path: str) -> Iterator[str]:
        """Search through a log file.

        Args:
            file_path: Path to the log file

        Yields:
            Lines that match the search criteria with context
        """
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            yield from self.search_stream(f, use_current_time_default=False)

    def search_stdin(self) -> Iterator[str]:
        """Search through stdin.

        Yields:
            Lines that match the search criteria with context
        """
        yield from self.search_stream(sys.stdin, use_current_time_default=False)
