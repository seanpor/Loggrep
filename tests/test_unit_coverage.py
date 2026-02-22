#!/usr/bin/env python3
"""
Unit tests with direct imports for coverage tracking.

These complement the integration tests in test_loggrep.py which run via subprocess
and therefore don't contribute to pytest-cov coverage.
"""

import io
import os
import sys
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

sys.path.insert(0, "src")

from loggrep.cli import _file_error, create_parser, determine_color_usage, main
from loggrep.core import LogSearcher
from loggrep.timestamps import detect_timestamp_format, parse_timestamp

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_stream(lines):
    """Create a StringIO stream from a list of strings."""
    return io.StringIO("".join(lines))


def _future_iso(seconds=60):
    """Return an ISO-8601 timestamp string N seconds in the future."""
    dt = datetime.now() + timedelta(seconds=seconds)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _past_iso(seconds=600):
    """Return an ISO-8601 timestamp string N seconds in the past."""
    dt = datetime.now() - timedelta(seconds=seconds)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ===================================================================
# LogSearcher — __init__
# ===================================================================


class TestLogSearcherInit:
    def test_single_pattern(self):
        ls = LogSearcher(patterns=["hello"])
        assert ls.pattern.pattern == "hello"

    def test_multiple_patterns(self):
        ls = LogSearcher(patterns=["a", "b"])
        assert "(a)" in ls.pattern.pattern
        assert "(b)" in ls.pattern.pattern

    def test_ignore_case(self):
        ls = LogSearcher(patterns=["hello"], ignore_case=True)
        assert ls.pattern.search("HELLO")

    def test_context_override(self):
        ls = LogSearcher(patterns=["x"], before_context=1, after_context=1, context=5)
        assert ls.before_context == 5
        assert ls.after_context == 5

    def test_invalid_regex(self):
        with pytest.raises(ValueError, match="Invalid regex"):
            LogSearcher(patterns=["[invalid"])

    def test_startup_time_parsing(self):
        ls = LogSearcher(patterns=["x"], startup_time="2025-06-15 12:00:00")
        assert ls.startup_time == datetime(2025, 6, 15, 12, 0, 0)

    def test_no_startup_time(self):
        ls = LogSearcher(patterns=["x"])
        assert ls.startup_time is None


# ===================================================================
# LogSearcher — search_stream
# ===================================================================


class TestSearchStream:
    def test_basic_match(self):
        stream = _make_stream(["hello world\n", "goodbye\n"])
        ls = LogSearcher(patterns=["hello"])
        assert list(ls.search_stream(stream)) == ["hello world\n"]

    def test_no_match(self):
        stream = _make_stream(["foo\n", "bar\n"])
        ls = LogSearcher(patterns=["baz"])
        assert list(ls.search_stream(stream)) == []

    def test_invert_match(self):
        stream = _make_stream(["ERROR line\n", "INFO line\n", "DEBUG line\n"])
        ls = LogSearcher(patterns=["ERROR"], invert_match=True)
        result = list(ls.search_stream(stream))
        assert "INFO line\n" in result
        assert "DEBUG line\n" in result
        assert "ERROR line\n" not in result

    def test_after_context(self):
        lines = ["line1\n", "MATCH\n", "line3\n", "line4\n"]
        ls = LogSearcher(patterns=["MATCH"], after_context=1)
        result = list(ls.search_stream(_make_stream(lines)))
        assert "MATCH\n" in result
        assert "line3\n" in result

    def test_before_context(self):
        lines = ["line1\n", "line2\n", "MATCH\n", "line4\n"]
        ls = LogSearcher(patterns=["MATCH"], before_context=1)
        result = list(ls.search_stream(_make_stream(lines)))
        assert "line2\n" in result
        assert "MATCH\n" in result

    def test_context_both(self):
        lines = ["a\n", "b\n", "MATCH\n", "d\n", "e\n"]
        ls = LogSearcher(patterns=["MATCH"], context=1)
        result = list(ls.search_stream(_make_stream(lines)))
        assert "b\n" in result
        assert "MATCH\n" in result
        assert "d\n" in result

    def test_timestamp_filtering_skips_old(self):
        now = datetime.now()
        past = (now - timedelta(seconds=600)).strftime("%Y-%m-%d %H:%M:%S")
        future = (now + timedelta(seconds=600)).strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            f"{past} old error\n",
            f"{future} new error\n",
        ]
        ls = LogSearcher(patterns=["error"])
        ls.startup_time = now
        result = list(ls.search_stream(_make_stream(lines)))
        assert len(result) == 1
        assert "new error" in result[0]

    def test_no_timestamp_fallback(self):
        """After NO_TIMESTAMP_THRESHOLD lines with no timestamps, filtering disables."""
        lines = ["line1\n", "line2\n", "line3\n", "target line\n"]
        ls = LogSearcher(patterns=["target"])
        ls.startup_time = datetime.now()
        result = list(ls.search_stream(_make_stream(lines)))
        assert len(result) == 1
        assert "target" in result[0]

    def test_no_filtering_without_startup_time(self):
        lines = ["a\n", "b\n", "c\n"]
        ls = LogSearcher(patterns=["b"])
        result = list(ls.search_stream(_make_stream(lines)))
        assert result == ["b\n"]


# ===================================================================
# LogSearcher — highlight_match
# ===================================================================


class TestHighlightMatch:
    def test_no_color(self):
        ls = LogSearcher(patterns=["test"], use_color=False)
        m = ls.pattern.search("test line")
        assert ls.highlight_match("test line", m) == "test line"

    def test_with_color(self):
        ls = LogSearcher(patterns=["test"], use_color=True)
        if ls.use_color:  # Only runs if colorama is installed
            m = ls.pattern.search("test line")
            result = ls.highlight_match("test line", m)
            assert "test" in result
            assert result != "test line"  # Should be different due to color codes


# ===================================================================
# LogSearcher — search_file
# ===================================================================


class TestSearchFile:
    def test_search_file_basic(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("ERROR something\nINFO ok\nERROR again\n")
            f.flush()
            try:
                ls = LogSearcher(patterns=["ERROR"])
                ls.startup_time = None  # Disable time filtering
                result = list(ls.search_file(f.name))
                assert len(result) == 2
                assert all("ERROR" in r for r in result)
            finally:
                os.unlink(f.name)

    def test_search_file_with_encoding_errors(self):
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".log", delete=False) as f:
            f.write(b"good line\n\xc0\xc1 bad bytes\nanother good\n")
            f.flush()
            try:
                ls = LogSearcher(patterns=["good"])
                ls.startup_time = None
                result = list(ls.search_file(f.name))
                assert len(result) == 2
            finally:
                os.unlink(f.name)


# ===================================================================
# CLI — determine_color_usage
# ===================================================================


class TestDetermineColorUsage:
    def test_always(self):
        assert determine_color_usage("always") is True

    def test_never(self):
        assert determine_color_usage("never") is False

    def test_auto_non_tty(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            assert determine_color_usage("auto") is False

    def test_auto_no_colorama(self):
        """When colorama is not installed, auto returns False (cli.py:142-143)."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "colorama":
                raise ImportError("no colorama")
            return original_import(name, *args, **kwargs)

        with patch.object(builtins, "__import__", side_effect=mock_import):
            assert determine_color_usage("auto") is False


# ===================================================================
# CLI — _file_error
# ===================================================================


class TestFileError:
    def test_returns_2(self, capsys):
        result = _file_error("🚫", "/tmp/x", "Not found", "Check path")
        assert result == 2
        captured = capsys.readouterr()
        assert "/tmp/x" in captured.err
        assert "Not found" in captured.err
        assert "Check path" in captured.err


# ===================================================================
# CLI — main() startup time priority
# ===================================================================


class TestMainStartupTime:
    def test_no_live_disables_filtering(self):
        """--no-live sets startup_time to None."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            past = _past_iso(3600)
            f.write(f"{past} ERROR old line\n")
            f.flush()
            try:
                result = main(["ERROR", "--file", f.name, "--no-live"])
                assert result == 0
            finally:
                os.unlink(f.name)

    def test_startup_time_override(self):
        """startup_time_override is used when no --startup-time is given."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            future = _future_iso(600)
            f.write(f"{future} ERROR future line\n")
            f.flush()
            try:
                override = datetime.now() - timedelta(seconds=10)
                result = main(
                    ["ERROR", "--file", f.name],
                    startup_time_override=override,
                )
                assert result == 0
            finally:
                os.unlink(f.name)

    def test_explicit_startup_time_takes_priority(self):
        """--startup-time overrides everything else."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("2025-06-15 12:00:00 ERROR test\n")
            f.flush()
            try:
                result = main(
                    [
                        "ERROR",
                        "--file",
                        f.name,
                        "--startup-time",
                        "2025-06-15 11:00:00",
                    ]
                )
                assert result == 0
            finally:
                os.unlink(f.name)

    def test_default_uses_now(self, capsys):
        """Without --no-live or override, default is datetime.now()."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            past = _past_iso(3600)
            f.write(f"{past} ERROR should be hidden\n")
            f.flush()
            try:
                result = main(["ERROR", "--file", f.name])
                assert result == 0
                captured = capsys.readouterr()
                assert "should be hidden" not in captured.out
            finally:
                os.unlink(f.name)


# ===================================================================
# CLI — main() error handling
# ===================================================================


class TestMainErrors:
    def test_file_not_found(self, capsys):
        result = main(["x", "--file", "/tmp/nonexistent_loggrep_test.log"])
        assert result == 2
        assert "No such file" in capsys.readouterr().err

    def test_directory_error(self, capsys):
        result = main(["x", "--file", "/tmp"])
        assert result == 2
        assert "Is a directory" in capsys.readouterr().err

    def test_invalid_regex(self, capsys):
        result = main(["[invalid", "--no-live"])
        assert result == 1
        assert "regex" in capsys.readouterr().err.lower()

    def test_permission_denied(self, capsys):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("test\n")
            f.flush()
            os.chmod(f.name, 0o000)
            try:
                result = main(["test", "--file", f.name])
                assert result == 2
                assert "Permission denied" in capsys.readouterr().err
            finally:
                os.chmod(f.name, 0o644)
                os.unlink(f.name)

    def test_broken_pipe(self):
        """BrokenPipeError returns 0 (cli.py:214-215)."""
        with patch("loggrep.cli.LogSearcher") as MockSearcher:
            instance = MockSearcher.return_value
            instance.search_file.return_value = iter(["line\n"])
            with patch("builtins.print", side_effect=BrokenPipeError):
                result = main(["test", "--file", "dummy.log", "--no-live"])
                assert result == 0

    def test_unicode_decode_error(self, capsys):
        """UnicodeDecodeError returns 2 with helpful message (cli.py:216-217)."""
        with patch("loggrep.cli.LogSearcher") as MockSearcher:
            instance = MockSearcher.return_value
            instance.search_file.side_effect = UnicodeDecodeError(
                "utf-8", b"\xff", 0, 1, "invalid"
            )
            result = main(["test", "--file", "dummy.log", "--no-live"])
            assert result == 2
            assert "Unable to decode" in capsys.readouterr().err

    def test_non_regex_value_error(self, capsys):
        """Non-regex ValueError prints generic error (cli.py:233)."""
        with patch("loggrep.cli.LogSearcher") as MockSearcher:
            MockSearcher.side_effect = ValueError("something went wrong")
            result = main(["test", "--file", "dummy.log", "--no-live"])
            assert result == 1
            assert "something went wrong" in capsys.readouterr().err

    def test_keyboard_interrupt(self, capsys):
        """KeyboardInterrupt returns 130 (cli.py:235-237)."""
        with patch("loggrep.cli.LogSearcher") as MockSearcher:
            MockSearcher.side_effect = KeyboardInterrupt()
            result = main(["test", "--file", "dummy.log", "--no-live"])
            assert result == 130
            assert "Interrupted" in capsys.readouterr().err

    def test_unexpected_exception(self, capsys):
        """Unexpected exceptions return 1 with bug report link (cli.py:238-244)."""
        with patch("loggrep.cli.LogSearcher") as MockSearcher:
            MockSearcher.side_effect = RuntimeError("boom")
            result = main(["test", "--file", "dummy.log", "--no-live"])
            assert result == 1
            err = capsys.readouterr().err
            assert "Unexpected error" in err
            assert "github.com" in err


# ===================================================================
# Timestamps — detect_timestamp_format
# ===================================================================


class TestDetectTimestampFormat:
    def test_iso8601(self):
        assert detect_timestamp_format("2025-06-15 12:00:00 msg") is not None

    def test_syslog(self):
        assert detect_timestamp_format("Oct  5 14:30:02 host msg") is not None

    def test_logcat(self):
        assert detect_timestamp_format("10-05 14:30:02.123 msg") is not None

    def test_iso8601_extended(self):
        assert detect_timestamp_format("2025-06-15T12:00:00Z msg") is not None

    def test_no_timestamp(self):
        assert detect_timestamp_format("plain text no time here") is None

    def test_nginx(self):
        assert detect_timestamp_format("2025/06/15 12:00:00 msg") is not None

    def test_apache(self):
        assert detect_timestamp_format("15/Jun/2025:12:00:00 msg") is not None

    def test_eu_date(self):
        assert detect_timestamp_format("15.06.2025 12:00:00 msg") is not None


# ===================================================================
# Timestamps — parse_timestamp
# ===================================================================


class TestParseTimestamp:
    def test_iso8601(self):
        result = parse_timestamp("2025-06-15 12:00:00")
        assert result == datetime(2025, 6, 15, 12, 0, 0)

    def test_syslog(self):
        result = parse_timestamp("Oct 12 14:30:45")
        assert result is not None
        assert result.month == 10
        assert result.day == 12

    def test_logcat(self):
        result = parse_timestamp("10-12 14:30:45.123")
        assert result is not None
        assert result.month == 10

    def test_empty_string(self):
        assert parse_timestamp("") is None

    def test_whitespace_only(self):
        assert parse_timestamp("   ") is None

    def test_nonsense(self):
        assert parse_timestamp("not a timestamp at all") is None

    def test_iso8601_with_t(self):
        result = parse_timestamp("2025-06-15T12:00:00")
        assert result == datetime(2025, 6, 15, 12, 0, 0)

    def test_timezone_stripped(self):
        result = parse_timestamp("2025-06-15T12:00:00+05:00")
        assert result is not None
        assert result.tzinfo is None  # Should be naive

    def test_timezone_aware_via_dateutil(self):
        """Timezone-aware datetimes are made naive (timestamps.py:129)."""
        # RFC 2822 format — not caught by any fast_parse, dateutil returns tz-aware
        result = parse_timestamp("Fri, 15 Jun 2025 12:00:00 +0500")
        assert result is not None
        assert result.tzinfo is None
        assert result == datetime(2025, 6, 15, 12, 0, 0)


# ===================================================================
# Core — search_stdin (core.py:135-138)
# ===================================================================


class TestSearchStdin:
    def test_search_stdin_basic(self):
        """search_stdin reads from sys.stdin.buffer (core.py:135-138)."""
        searcher = LogSearcher(["hello"])
        searcher.startup_time = None
        data = b"hello world\ngoodbye world\nhello again\n"
        mock_stdin = type("MockStdin", (), {"buffer": io.BytesIO(data)})()
        with patch("sys.stdin", mock_stdin):
            results = list(searcher.search_stdin())
        assert len(results) == 2
        assert "hello world" in results[0]
        assert "hello again" in results[1]


# ===================================================================
# Core — colorama ImportError (core.py:21-22)
# ===================================================================


class TestColoramaFallback:
    def test_color_available_false_without_colorama(self):
        """When colorama is not installed, COLOR_AVAILABLE is False."""
        import builtins
        import importlib

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "colorama":
                raise ImportError("no colorama")
            return original_import(name, *args, **kwargs)

        with patch.object(builtins, "__import__", side_effect=mock_import):
            # Remove cached module so re-import triggers the except branch
            saved = sys.modules.pop("loggrep.core", None)
            try:
                import loggrep.core

                importlib.reload(loggrep.core)
                assert loggrep.core.COLOR_AVAILABLE is False
            finally:
                # Restore the module
                if saved is not None:
                    sys.modules["loggrep.core"] = saved


# ===================================================================
# CLI — main() stdin path (cli.py:188)
# ===================================================================


class TestMainStdin:
    def test_stdin_path(self, capsys):
        """main() calls search_stdin when no --file is given (cli.py:188)."""
        with patch("loggrep.cli.LogSearcher") as MockSearcher:
            instance = MockSearcher.return_value
            instance.search_stdin.return_value = iter(["matched line\n"])
            result = main(["test", "--no-live"])
            assert result == 0
            instance.search_stdin.assert_called_once()
            assert "matched line" in capsys.readouterr().out


# ===================================================================
# CLI — create_parser
# ===================================================================


class TestCreateParser:
    def test_basic(self):
        parser = create_parser()
        args = parser.parse_args(["test_pattern"])
        assert args.patterns == ["test_pattern"]

    def test_all_options(self):
        parser = create_parser()
        args = parser.parse_args(
            [
                "-i",
                "-v",
                "-A",
                "3",
                "-B",
                "2",
                "-C",
                "1",
                "--color",
                "always",
                "--no-live",
                "--startup-time",
                "2025-01-01 00:00:00",
                "--file",
                "test.log",
                "pattern1",
                "pattern2",
            ]
        )
        assert args.ignore_case is True
        assert args.invert_match is True
        assert args.after_context == 3
        assert args.before_context == 2
        assert args.context == 1
        assert args.color == "always"
        assert args.no_live is True
        assert args.file == "test.log"
        assert args.patterns == ["pattern1", "pattern2"]

    def test_help_exits(self):
        with pytest.raises(SystemExit):
            create_parser().parse_args(["--help"])

    def test_version_exits(self):
        with pytest.raises(SystemExit):
            create_parser().parse_args(["--version"])
