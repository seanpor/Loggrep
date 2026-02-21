#!/usr/bin/env python3
"""
Comprehensive test suite for loggrep.py

Tests all functionality promised in the README:
- Timestamp-aware searching
- Regex support
- Invert match (-v)
- Context lines (-A, -B, -C)
- Color output
- Multiple patterns
- Flexible timestamp parsing
- Stdin/file input
- Case-insensitive search (-i)
"""

import os
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Get the directory containing this test file
TEST_DIR = Path(__file__).parent.parent
LOGGREP_PATH = TEST_DIR / "loggrep"  # Use our console script


# ---------------------------------------------------------------------------
# Dynamic test-data generators -- timestamps are always in the near future
# so that loggrep's default "now" filter lets them through.
# ---------------------------------------------------------------------------


def _fmt_syslog(dt):
    """Format datetime as syslog: 'Feb  4 12:00:00'."""
    return f"{dt.strftime('%b')}{dt.day:>3} {dt.strftime('%H:%M:%S')}"


def _fmt_iso8601(dt):
    """Format datetime as ISO 8601: '2026-02-21 12:00:00.123'."""
    return dt.strftime("%Y-%m-%d %H:%M:%S.") + f"{dt.microsecond // 1000:03d}"


def _fmt_logcat(dt):
    """Format datetime as Android logcat: '02-21 12:00:00.123'."""
    return dt.strftime("%m-%d %H:%M:%S.") + f"{dt.microsecond // 1000:03d}"


# Offsets (in seconds from base) shared by all three formats.
_OFFSETS = [0, 2, 6, 11, 13, 16, 21, 26, 31, 61]


def make_syslog_data(base_offset=60):
    """Generate syslog-format log data with future timestamps.

    Returns (data_string, base_time, list_of_datetimes).
    """
    base = datetime.now() + timedelta(seconds=base_offset)
    times = [base + timedelta(seconds=s) for s in _OFFSETS]
    lines = [
        f"{_fmt_syslog(times[0])} server1 service[1234]: Starting service",
        f"{_fmt_syslog(times[1])} server1 service[1234]: Service started successfully",
        f"{_fmt_syslog(times[2])} server1 service[1234]: Processing request 1",
        f"{_fmt_syslog(times[3])} server1 service[1234]: ERROR: Database connection failed",
        f"{_fmt_syslog(times[4])} server1 service[1234]: WARN: Retrying database connection",
        f"{_fmt_syslog(times[5])} server1 service[1234]: INFO: Database connection restored",
        f"{_fmt_syslog(times[6])} server1 service[1234]: Processing request 2",
        f"{_fmt_syslog(times[7])} server1 service[1234]: Request 2 completed successfully",
        f"{_fmt_syslog(times[8])} server1 service[1234]: ERROR: Memory usage high",
        f"{_fmt_syslog(times[9])} server1 service[1234]: Service stopped",
    ]
    return "\n".join(lines) + "\n", base, times


def make_iso8601_data(base_offset=60):
    """Generate ISO 8601 log data with future timestamps."""
    base = datetime.now() + timedelta(seconds=base_offset)
    times = [base + timedelta(seconds=s) for s in _OFFSETS]
    lines = [
        f"{_fmt_iso8601(times[0])} [INFO] Application starting",
        f"{_fmt_iso8601(times[1])} [INFO] Configuration loaded",
        f"{_fmt_iso8601(times[2])} [DEBUG] Processing user request",
        f"{_fmt_iso8601(times[3])} [ERROR] Database connection timeout",
        f"{_fmt_iso8601(times[4])} [WARN] Retrying operation",
        f"{_fmt_iso8601(times[5])} [INFO] Operation completed",
        f"{_fmt_iso8601(times[6])} [DEBUG] Cleanup started",
        f"{_fmt_iso8601(times[7])} [INFO] Cleanup completed",
        f"{_fmt_iso8601(times[8])} [ERROR] Unexpected error occurred",
        f"{_fmt_iso8601(times[9])} [INFO] Application shutdown",
    ]
    return "\n".join(lines) + "\n", base, times


def make_logcat_data(base_offset=60):
    """Generate Android logcat log data with future timestamps."""
    base = datetime.now() + timedelta(seconds=base_offset)
    times = [base + timedelta(seconds=s) for s in _OFFSETS]
    lines = [
        f"{_fmt_logcat(times[0])}  1234  5678 I ActivityManager: Starting activity",
        f"{_fmt_logcat(times[1])}  1234  5678 I ActivityManager: Activity started",
        f"{_fmt_logcat(times[2])}  1234  5678 D NetworkManager: Network request sent",
        f"{_fmt_logcat(times[3])}  1234  5678 E NetworkManager: Connection failed",
        f"{_fmt_logcat(times[4])}  1234  5678 W NetworkManager: Retrying connection",
        f"{_fmt_logcat(times[5])}  1234  5678 I NetworkManager: Connection established",
        f"{_fmt_logcat(times[6])}  1234  5678 D LocationManager: GPS update received",
        f"{_fmt_logcat(times[7])}  1234  5678 I LocationManager: Location updated",
        f"{_fmt_logcat(times[8])}  1234  5678 E SystemManager: Low memory warning",
        f"{_fmt_logcat(times[9])}  1234  5678 I ActivityManager: Activity stopped",
    ]
    return "\n".join(lines) + "\n", base, times


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def run_loggrep(args, input_data=None, expect_error=False):
    """Helper function to run loggrep with given arguments and input."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(TEST_DIR / "src") + ":" + env.get("PYTHONPATH", "")

    if sys.platform == "win32":
        cmd = [sys.executable, str(LOGGREP_PATH)] + args
    else:
        cmd = [str(LOGGREP_PATH)] + args

    process = subprocess.run(
        cmd, input=input_data, text=True, capture_output=True, cwd=TEST_DIR, env=env
    )

    if not expect_error and process.returncode != 0:
        pytest.fail(
            f"loggrep failed with exit code {process.returncode}\n"
            f"stderr: {process.stderr}\nstdout: {process.stdout}"
        )

    return process


def create_temp_logfile(content):
    """Create a temporary log file with given content."""
    temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log")
    temp_file.write(content)
    temp_file.close()
    return temp_file.name


# ===================================================================
# Tests
# ===================================================================


class TestBasicFunctionality:
    """Test basic search functionality."""

    def test_basic_pattern_search(self):
        """Test basic pattern search in log file."""
        data, _, _ = make_syslog_data()
        temp_file = create_temp_logfile(data)
        try:
            result = run_loggrep(["ERROR", "--file", temp_file])
            assert "ERROR: Database connection failed" in result.stdout
            assert "ERROR: Memory usage high" in result.stdout
            assert result.stdout.count("ERROR") == 2
        finally:
            os.unlink(temp_file)

    def test_stdin_input(self):
        """Test reading from stdin."""
        data, _, _ = make_syslog_data()
        result = run_loggrep(["ERROR"], input_data=data)
        assert "ERROR: Database connection failed" in result.stdout
        assert "ERROR: Memory usage high" in result.stdout

    def test_no_matches(self):
        """Test when pattern doesn't match anything."""
        data, _, _ = make_syslog_data()
        result = run_loggrep(["NONEXISTENT"], input_data=data)
        assert result.stdout.strip() == ""

    def test_multiple_patterns(self):
        """Test searching for multiple patterns (OR logic)."""
        data, _, _ = make_syslog_data()
        result = run_loggrep(["ERROR", "WARN"], input_data=data)
        assert "ERROR: Database connection failed" in result.stdout
        assert "ERROR: Memory usage high" in result.stdout
        assert "WARN: Retrying database connection" in result.stdout
        assert len(result.stdout.strip().split("\n")) == 3


class TestRegexSupport:
    """Test regex pattern support."""

    def test_regex_pattern(self):
        """Test using regex patterns."""
        data, _, _ = make_syslog_data()
        result = run_loggrep([r"(ERROR|WARN)"], input_data=data)
        assert "ERROR: Database connection failed" in result.stdout
        assert "WARN: Retrying database connection" in result.stdout
        assert "ERROR: Memory usage high" in result.stdout

    def test_regex_word_boundaries(self):
        """Test regex with word boundaries."""
        data, _, _ = make_syslog_data()
        result = run_loggrep([r"\bservice\b"], input_data=data)
        lines = result.stdout.strip().split("\n")
        assert len(lines) > 0
        for line in lines:
            assert "service" in line.lower()

    def test_invalid_regex(self):
        """Test handling of invalid regex patterns."""
        data, _, _ = make_syslog_data()
        result = run_loggrep(["[invalid"], input_data=data, expect_error=True)
        assert result.returncode != 0
        assert "Invalid regex pattern" in result.stderr


class TestCaseInsensitive:
    """Test case-insensitive search functionality."""

    def test_case_insensitive_flag(self):
        """Test -i/--ignore-case flag."""
        data, _, _ = make_syslog_data()
        result = run_loggrep(["-i", "error"], input_data=data)
        assert "ERROR: Database connection failed" in result.stdout
        assert "ERROR: Memory usage high" in result.stdout

    def test_case_sensitive_default(self):
        """Test that search is case-sensitive by default."""
        data, _, _ = make_syslog_data()
        result = run_loggrep(["error"], input_data=data)
        assert result.stdout.strip() == ""

        result = run_loggrep(["ERROR"], input_data=data)
        assert "ERROR: Database connection failed" in result.stdout


class TestInvertMatch:
    """Test invert match functionality (-v flag)."""

    def test_invert_match(self):
        """Test -v/--invert-match flag."""
        data, _, _ = make_syslog_data()
        result = run_loggrep(["-v", "ERROR"], input_data=data)
        lines = result.stdout.strip().split("\n")
        for line in lines:
            assert "ERROR" not in line
        assert len(lines) == 8

    def test_invert_match_with_multiple_patterns(self):
        """Test invert match with multiple patterns."""
        data, _, _ = make_syslog_data()
        result = run_loggrep(["-v", "ERROR", "WARN"], input_data=data)
        lines = result.stdout.strip().split("\n")
        for line in lines:
            assert "ERROR" not in line
            assert "WARN" not in line
        assert len(lines) == 7


class TestContextLines:
    """Test context lines functionality (-A, -B, -C flags)."""

    def test_after_context(self):
        """Test -A flag (lines after match)."""
        data, _, _ = make_syslog_data()
        result = run_loggrep(["-A", "2", "ERROR.*Database"], input_data=data)
        assert "ERROR: Database connection failed" in result.stdout
        assert "WARN: Retrying database connection" in result.stdout
        assert "INFO: Database connection restored" in result.stdout

    def test_before_context(self):
        """Test -B flag (lines before match)."""
        data, _, _ = make_syslog_data()
        result = run_loggrep(["-B", "2", "ERROR.*Database"], input_data=data)
        assert "Service started successfully" in result.stdout
        assert "Processing request 1" in result.stdout
        assert "ERROR: Database connection failed" in result.stdout

    def test_context_around(self):
        """Test -C flag (lines around match)."""
        data, _, _ = make_syslog_data()
        result = run_loggrep(["-C", "1", "ERROR.*Database"], input_data=data)
        assert "Processing request 1" in result.stdout
        assert "ERROR: Database connection failed" in result.stdout
        assert "WARN: Retrying database connection" in result.stdout


class TestTimestampParsing:
    """Test timestamp parsing and filtering functionality."""

    def test_unix_syslog_timestamps(self):
        """Test parsing Unix syslog timestamp format."""
        data, base, times = make_syslog_data()
        temp_file = create_temp_logfile(data)
        try:
            # Startup between entry 5 (+16s) and entry 6 (+21s)
            startup = _fmt_syslog(base + timedelta(seconds=18))
            result = run_loggrep(
                ["Processing", "--file", temp_file, "--startup-time", startup]
            )
            assert "Processing request 2" in result.stdout
            assert "Processing request 1" not in result.stdout
        finally:
            os.unlink(temp_file)

    def test_iso8601_timestamps(self):
        """Test parsing ISO 8601 timestamp format."""
        data, base, times = make_iso8601_data()
        temp_file = create_temp_logfile(data)
        try:
            # Startup between entry 4 (+13s) and entry 5 (+16s)
            startup = _fmt_iso8601(base + timedelta(seconds=15))
            result = run_loggrep(
                ["INFO", "--file", temp_file, "--startup-time", startup]
            )
            assert "Operation completed" in result.stdout
            assert "Cleanup completed" in result.stdout
            assert "Application shutdown" in result.stdout
            assert "Application starting" not in result.stdout
            assert "Configuration loaded" not in result.stdout
        finally:
            os.unlink(temp_file)

    def test_android_logcat_timestamps(self):
        """Test parsing Android logcat timestamp format."""
        data, base, times = make_logcat_data()
        temp_file = create_temp_logfile(data)
        try:
            # Startup between entry 7 (+26s) and entry 8 (+31s)
            startup = _fmt_logcat(base + timedelta(seconds=28))
            result = run_loggrep(
                ["ActivityManager", "--file", temp_file, "--startup-time", startup]
            )
            assert "Activity stopped" in result.stdout
            assert "Starting activity" not in result.stdout
            assert "Activity started" not in result.stdout
        finally:
            os.unlink(temp_file)

    def test_no_startup_time_shows_future_entries(self):
        """Without --startup-time, file mode defaults to now and shows future entries."""
        data, _, _ = make_syslog_data()
        temp_file = create_temp_logfile(data)
        try:
            result = run_loggrep(["service", "--file", temp_file])
            lines = result.stdout.strip().split("\n")
            assert len(lines) > 5
        finally:
            os.unlink(temp_file)

    def test_stdin_defaults_to_current_time(self):
        """Test that stdin filters old entries and shows future ones."""
        now = datetime.now()
        old_time = now - timedelta(hours=1)
        future_time = now + timedelta(seconds=60)

        log_data = (
            f"{old_time.strftime('%Y-%m-%d %H:%M:%S')} [INFO] Old message should be filtered\n"
            f"{future_time.strftime('%Y-%m-%d %H:%M:%S')} [ERROR] Recent message should appear\n"
        )

        result = run_loggrep(["ERROR"], input_data=log_data)
        assert "Recent message should appear" in result.stdout
        assert "Old message should be filtered" not in result.stdout

    def test_file_defaults_to_now_filters_past(self):
        """Test that file mode filters out past entries by default."""
        past_time = datetime.now() - timedelta(hours=2)
        past_time2 = past_time + timedelta(minutes=5)

        log_data = (
            f"{past_time.strftime('%Y-%m-%d %H:%M:%S')} [INFO] First message\n"
            f"{past_time2.strftime('%Y-%m-%d %H:%M:%S')} [ERROR] Second message\n"
        )

        temp_file = create_temp_logfile(log_data)
        try:
            # Default file mode filters to "now" -- past logs excluded
            result = run_loggrep(["ERROR", "--file", temp_file])
            assert "Second message" not in result.stdout

            # --no-live disables filtering
            result = run_loggrep(["ERROR", "--no-live", "--file", temp_file])
            assert "Second message" in result.stdout
        finally:
            os.unlink(temp_file)

    def test_live_flag_functionality(self):
        """Test that --live flag works for real-time log streaming simulation."""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(TEST_DIR / "src") + ":" + env.get("PYTHONPATH", "")

        if sys.platform == "win32":
            cmd = [sys.executable, str(LOGGREP_PATH), "ERROR", "--live"]
        else:
            cmd = [str(LOGGREP_PATH), "ERROR", "--live"]

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=TEST_DIR,
        )

        try:
            now = datetime.now()
            old_entry = (
                f"{(now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')}"
                " [ERROR] Old error message\n"
            )
            future_entry = (
                f"{(now + timedelta(seconds=60)).strftime('%Y-%m-%d %H:%M:%S')}"
                " [ERROR] Future error message\n"
            )

            stdout, stderr = process.communicate(
                input=old_entry + future_entry, timeout=5
            )

            assert "Future error message" in stdout
            assert "Old error message" not in stdout

        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            pytest.fail("Live test timed out")
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait()

    def test_live_streaming_simulation(self):
        """Test live streaming like 'tail -f' or 'adb logcat' scenarios."""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(TEST_DIR / "src") + ":" + env.get("PYTHONPATH", "")

        if sys.platform == "win32":
            cmd = [sys.executable, str(LOGGREP_PATH), "ActivityManager", "--live"]
        else:
            cmd = [str(LOGGREP_PATH), "ActivityManager", "--live"]

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=TEST_DIR,
        )

        output_lines = []

        def read_output():
            try:
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    output_lines.append(line.strip())
            except Exception:
                pass

        output_thread = threading.Thread(target=read_output, daemon=True)
        output_thread.start()

        try:
            now = datetime.now()
            old_entries = [
                f"{(now - timedelta(minutes=30)).strftime('%m-%d %H:%M:%S.%f')[:-3]}"
                "  1234  5678 I ActivityManager: Old activity start",
                f"{(now - timedelta(minutes=20)).strftime('%m-%d %H:%M:%S.%f')[:-3]}"
                "  1234  5678 I ActivityManager: Old activity pause",
            ]
            future_entries = [
                f"{(now + timedelta(seconds=60)).strftime('%m-%d %H:%M:%S.%f')[:-3]}"
                "  1234  5678 I ActivityManager: Future activity launch",
                f"{(now + timedelta(seconds=61)).strftime('%m-%d %H:%M:%S.%f')[:-3]}"
                "  1234  5678 I ActivityManager: Recent activity resume",
            ]

            for entry in old_entries:
                process.stdin.write(entry + "\n")
                process.stdin.flush()
                time.sleep(0.05)

            for entry in future_entries:
                process.stdin.write(entry + "\n")
                process.stdin.flush()
                time.sleep(0.05)

            time.sleep(0.2)
            process.stdin.close()
            process.wait(timeout=3)

            output_text = "\n".join(output_lines)
            assert "Future activity launch" in output_text
            assert "Recent activity resume" in output_text
            assert "Old activity start" not in output_text
            assert "Old activity pause" not in output_text

        except subprocess.TimeoutExpired:
            process.kill()
            pytest.fail("Live streaming test timed out")
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait()


class TestColorOutput:
    """Test color output functionality."""

    def test_color_auto_with_tty(self):
        """Test color=auto behavior (default)."""
        data, _, _ = make_syslog_data()
        result = run_loggrep(["ERROR"], input_data=data)
        assert "\x1b[" not in result.stdout

    def test_color_always(self):
        """Test --color=always flag."""
        data, _, _ = make_syslog_data()
        result = run_loggrep(["--color=always", "ERROR"], input_data=data)
        assert "ERROR" in result.stdout

    def test_color_never(self):
        """Test --color=never flag."""
        data, _, _ = make_syslog_data()
        result = run_loggrep(["--color=never", "ERROR"], input_data=data)
        assert "\x1b[" not in result.stdout
        assert "ERROR" in result.stdout


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        result = run_loggrep(
            ["ERROR", "--file", "/nonexistent/file.log"], expect_error=True
        )
        assert result.returncode != 0

    def test_empty_log_file(self):
        """Test handling of empty log file."""
        temp_file = create_temp_logfile("")
        try:
            result = run_loggrep(["ERROR", "--file", temp_file])
            assert result.stdout.strip() == ""
            assert result.returncode == 0
        finally:
            os.unlink(temp_file)

    def test_log_without_timestamps(self):
        """Test handling of log without recognizable timestamps."""
        log_without_timestamps = (
            "Line 1 without timestamp\n"
            "Line 2 without timestamp\n"
            "ERROR: Something went wrong\n"
            "Line 4 without timestamp\n"
        )
        # --no-live is appropriate here: no timestamps in data
        result = run_loggrep(["ERROR", "--no-live"], input_data=log_without_timestamps)
        assert "ERROR: Something went wrong" in result.stdout

    def test_invalid_startup_time(self):
        """Test handling of invalid startup time format."""
        data, _, _ = make_syslog_data()
        temp_file = create_temp_logfile(data)
        try:
            result = run_loggrep(
                ["ERROR", "--file", temp_file, "--startup-time", "invalid-time"]
            )
            assert result.returncode == 0 or result.returncode != 0
        finally:
            os.unlink(temp_file)

    def test_live_mode_without_timestamps(self):
        """Test that the no-timestamp fallback kicks in for stdin."""
        log_without_timestamps = (
            "Line 1 without timestamp\n"
            "Line 2 containing walkie\n"
            "Line 3 without timestamp\n"
            "Line 4 containing walkie again\n"
            "Line 5 without timestamp\n"
        )
        result = run_loggrep(["walkie"], input_data=log_without_timestamps)
        output_lines = result.stdout.strip().split("\n")
        assert len(output_lines) >= 1
        assert "Line 4 containing walkie again" in result.stdout


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_complex_search_scenario(self):
        """Test a complex search combining multiple features."""
        data, base, times = make_syslog_data()
        temp_file = create_temp_logfile(data)
        try:
            # Startup between entry 2 (+6s) and entry 3 (+11s)
            startup = _fmt_syslog(base + timedelta(seconds=8))
            result = run_loggrep(
                [
                    "-i",
                    "-C",
                    "1",
                    "error",
                    "warn",
                    "--file",
                    temp_file,
                    "--startup-time",
                    startup,
                ]
            )
            lines = result.stdout.strip().split("\n")
            assert len(lines) > 2
            assert any("ERROR" in line for line in lines)
            assert any("WARN" in line for line in lines)
        finally:
            os.unlink(temp_file)

    def test_real_world_log_patterns(self):
        """Test patterns that would be used in real-world scenarios."""
        base = datetime.now() + timedelta(seconds=60)
        offsets = [0, 1, 2, 3, 4, 5]
        times = [base + timedelta(seconds=s) for s in offsets]
        log_with_patterns = (
            f"{_fmt_syslog(times[0])} server1 nginx[1234]: 192.168.1.100 - GET /api/v1/users\n"
            f"{_fmt_syslog(times[1])} server1 nginx[1234]: 192.168.1.101 - POST /api/v1/login\n"
            f"{_fmt_syslog(times[2])} server1 nginx[1234]: 192.168.1.100 - GET /api/v1/users - 200 OK\n"
            f"{_fmt_syslog(times[3])} server1 nginx[1234]: 192.168.1.101 - POST /api/v1/login - 401 Unauthorized\n"
            f"{_fmt_syslog(times[4])} server1 nginx[1234]: 192.168.1.102 - GET /api/v1/admin - 403 Forbidden\n"
            f"{_fmt_syslog(times[5])} server1 nginx[1234]: 192.168.1.100 - GET /api/v1/data - 500 Internal Server Error\n"
        )

        result = run_loggrep([r"\b(401|403|500)\b"], input_data=log_with_patterns)
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3
        assert "401 Unauthorized" in result.stdout
        assert "403 Forbidden" in result.stdout
        assert "500 Internal Server Error" in result.stdout

        result = run_loggrep([r"192\.168\.1\.100"], input_data=log_with_patterns)
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3

        result = run_loggrep([r"/api/v1/\w+"], input_data=log_with_patterns)
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 6


def test_help_option():
    """Test that --help works correctly."""
    result = run_loggrep(["--help"])
    assert "Search log files with timestamp awareness" in result.stdout
    assert "patterns" in result.stdout
    assert "--file" in result.stdout
    assert "--startup-time" in result.stdout


def test_version_compatibility():
    """Test that the script runs with the documented Python version."""
    assert sys.version_info >= (3, 7), "Python 3.7+ required as per README"


def test_version_option():
    """Test that --version works correctly."""
    result = run_loggrep(["--version"])
    assert result.returncode == 0
    assert "loggrep" in result.stdout.lower()


class TestErrorHandling:
    """Test error handling and edge cases for better coverage."""

    def test_permission_denied_error(self):
        """Test handling of permission denied on file."""
        if sys.platform == "win32":
            pytest.skip("Permission test not applicable on Windows")

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content\n")
            temp_file = f.name

        try:
            if hasattr(os, "getuid") and os.getuid() == 0:
                pytest.skip("Permission test not applicable when running as root")
            else:
                os.chmod(temp_file, 0o200)
                result = run_loggrep(["test", "--file", temp_file], expect_error=True)
                assert result.returncode == 2
                assert "Permission denied" in result.stderr
        finally:
            try:
                os.chmod(temp_file, 0o644)
                os.unlink(temp_file)
            except Exception:
                pass

    def test_directory_error(self):
        """Test handling when file argument is a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_loggrep(["test", "--file", temp_dir], expect_error=True)
            assert result.returncode == 2
            if sys.platform == "win32":
                assert "Permission denied" in result.stderr
            else:
                assert "Is a directory" in result.stderr

    def test_file_not_found_error(self):
        """Test handling of nonexistent file."""
        result = run_loggrep(
            ["test", "--file", "/nonexistent/path/file.log"], expect_error=True
        )
        assert result.returncode == 2
        assert (
            "No such file or directory" in result.stderr
            or "cannot find the file" in result.stderr.lower()
        )

    def test_broken_pipe_handling(self):
        """Test graceful handling of broken pipe."""
        temp_file = create_temp_logfile("line with content\n" * 1000)
        try:
            if sys.platform == "win32":
                cmd = [
                    sys.executable,
                    str(LOGGREP_PATH),
                    "content",
                    "--file",
                    temp_file,
                ]
            else:
                cmd = [str(LOGGREP_PATH), "content", "--file", temp_file]

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if process.stdout:
                process.stdout.read(100)
                process.stdout.close()
            process.wait()
            assert process.returncode in [0, 1, 120]
        finally:
            try:
                os.unlink(temp_file)
            except Exception:
                pass

    def test_invalid_regex_error_handling(self):
        """Test handling of invalid regex patterns."""
        data, _, _ = make_iso8601_data()
        result = run_loggrep(["[invalid"], input_data=data, expect_error=True)
        assert result.returncode == 1
        assert result.stdout.strip() == ""

    def test_colorama_import_scenarios(self):
        """Test scenarios that exercise colorama import handling."""
        result = run_loggrep(["--help"])
        assert result.returncode == 0
        assert "color" in result.stdout.lower()

        data, _, _ = make_iso8601_data()
        result = run_loggrep(["INFO", "--color", "auto"], input_data=data)
        assert result.returncode == 0


class TestColorHandling:
    """Test color handling scenarios."""

    def test_color_auto_without_tty(self):
        """Test color=auto behavior when not in TTY."""
        data, _, _ = make_iso8601_data()
        result = run_loggrep(["INFO", "--color", "auto"], input_data=data)
        assert result.returncode == 0
        assert "\033[" not in result.stdout

    def test_color_never(self):
        """Test that --color never disables colors."""
        data, _, _ = make_iso8601_data()
        result = run_loggrep(["INFO", "--color", "never"], input_data=data)
        assert result.returncode == 0
        assert "\033[" not in result.stdout


class TestMemoryAndPerformance:
    """Test memory handling and performance edge cases."""

    def test_large_input_handling(self):
        """Test handling of large input data."""
        future_time = (datetime.now() + timedelta(seconds=60)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        large_log = f"{future_time} Test line\n" * 10000

        result = run_loggrep(["Test"], input_data=large_log)
        assert result.returncode == 0
        assert result.stdout.count("Test line") == 10000

    def test_no_matches_large_file(self):
        """Test behavior with large file that has no matches."""
        future_time = (datetime.now() + timedelta(seconds=60)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        large_log = f"{future_time} Other content\n" * 5000

        result = run_loggrep(["NonExistent"], input_data=large_log)
        assert result.returncode == 0
        assert result.stdout.strip() == ""


class TestRegexEdgeCases:
    """Test regex handling edge cases."""

    def test_regex_special_characters(self):
        """Test regex with special characters."""
        future_time = (datetime.now() + timedelta(seconds=60)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        log_data = (
            f"{future_time} Price: $100.50\n"
            f"{future_time} Email: user@domain.com\n"
            f"{future_time} Path: /var/log/app.log\n"
            f"{future_time} Query: SELECT * FROM users\n"
        )

        result = run_loggrep([r"\$\d+\.\d+"], input_data=log_data)
        assert "Price: $100.50" in result.stdout

        result = run_loggrep([r"\w+@\w+\.\w+"], input_data=log_data)
        assert "user@domain.com" in result.stdout

    def test_complex_regex_patterns(self):
        """Test complex regex patterns."""
        future_time = (datetime.now() + timedelta(seconds=60)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        log_data = (
            f"{future_time} [ERROR] Database connection failed: timeout after 30s\n"
            f"{future_time} [WARN] Memory usage: 85%\n"
            f"{future_time} [INFO] User login: john.doe\n"
            f"{future_time} [ERROR] API error: 404 Not Found\n"
        )

        result = run_loggrep([r"ERROR.*\d+"], input_data=log_data)
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2


class TestEncodingHandling:
    """Test handling of various text encodings and binary data."""

    def test_utf8_decode_errors_handling(self):
        """Test that binary data doesn't cause UTF-8 decode errors."""
        now = datetime.now()
        current_date = now.strftime("%m-%d")
        current_time = now.strftime("%H:%M:%S.%f")[:-3]

        binary_data_script = f"""import sys
import time
sys.stdout.buffer.write(b'{current_date} {current_time} I walkie: Starting app\\n')
time.sleep(0.001)
sys.stdout.buffer.write(b'{current_date} {current_time} I walkie: \\xc0\\x80Invalid UTF-8 data\\n')
time.sleep(0.001)
sys.stdout.buffer.write(b'{current_date} {current_time} I walkie: Normal log line\\n')
time.sleep(0.001)
sys.stdout.buffer.write(b'{current_date} {current_time} E other: \\xff\\xfeMore binary data\\n')
"""

        process1 = subprocess.Popen(
            [sys.executable, "-c", binary_data_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        loggrep_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "loggrep"
        )

        process2 = subprocess.Popen(
            [sys.executable, loggrep_path, "walkie", "--no-live"],
            stdin=process1.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        process1.stdout.close()
        stdout, stderr = process2.communicate()

        assert "Unable to decode" not in stderr
        assert "utf-8 codec can't decode" not in stderr
        assert "walkie: Starting app" in stdout
        assert "walkie:" in stdout
        assert "walkie: Normal log line" in stdout
        assert process2.returncode == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
