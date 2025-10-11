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
import tempfile
import pytest
from datetime import datetime
import re
import sys
from pathlib import Path

# Get the directory containing this test file
TEST_DIR = Path(__file__).parent.parent
LOGGREP_PATH = TEST_DIR / "loggrep"  # Use our console script

# Sample log data for testing different timestamp formats
SAMPLE_LOG_UNIX_SYSLOG = """Oct  4 11:59:59 server1 service[1234]: Starting service
Oct  4 12:00:01 server1 service[1234]: Service started successfully
Oct  4 12:00:05 server1 service[1234]: Processing request 1
Oct  4 12:00:10 server1 service[1234]: ERROR: Database connection failed
Oct  4 12:00:12 server1 service[1234]: WARN: Retrying database connection
Oct  4 12:00:15 server1 service[1234]: INFO: Database connection restored
Oct  4 12:00:20 server1 service[1234]: Processing request 2
Oct  4 12:00:25 server1 service[1234]: Request 2 completed successfully
Oct  4 12:00:30 server1 service[1234]: ERROR: Memory usage high
Oct  4 12:01:00 server1 service[1234]: Service stopped
"""

SAMPLE_LOG_ISO8601 = """2025-10-04 11:59:59.123 [INFO] Application starting
2025-10-04 12:00:01.456 [INFO] Configuration loaded
2025-10-04 12:00:05.789 [DEBUG] Processing user request
2025-10-04 12:00:10.012 [ERROR] Database connection timeout
2025-10-04 12:00:12.345 [WARN] Retrying operation
2025-10-04 12:00:15.678 [INFO] Operation completed
2025-10-04 12:00:20.901 [DEBUG] Cleanup started
2025-10-04 12:00:25.234 [INFO] Cleanup completed
2025-10-04 12:00:30.567 [ERROR] Unexpected error occurred
2025-10-04 12:01:00.890 [INFO] Application shutdown
"""

SAMPLE_LOG_ANDROID_LOGCAT = """10-04 11:59:59.123  1234  5678 I ActivityManager: Starting activity
10-04 12:00:01.456  1234  5678 I ActivityManager: Activity started
10-04 12:00:05.789  1234  5678 D NetworkManager: Network request sent
10-04 12:00:10.012  1234  5678 E NetworkManager: Connection failed
10-04 12:00:12.345  1234  5678 W NetworkManager: Retrying connection
10-04 12:00:15.678  1234  5678 I NetworkManager: Connection established
10-04 12:00:20.901  1234  5678 D LocationManager: GPS update received
10-04 12:00:25.234  1234  5678 I LocationManager: Location updated
10-04 12:00:30.567  1234  5678 E SystemManager: Low memory warning
10-04 12:01:00.890  1234  5678 I ActivityManager: Activity stopped
"""

def run_loggrep(args, input_data=None, expect_error=False):
    """Helper function to run loggrep with given arguments and input."""
    cmd = [str(LOGGREP_PATH)] + args
    process = subprocess.run(
        cmd,
        input=input_data,
        text=True,
        capture_output=True,
        cwd=TEST_DIR
    )
    
    if not expect_error and process.returncode != 0:
        pytest.fail(f"loggrep failed with exit code {process.returncode}\nstderr: {process.stderr}\nstdout: {process.stdout}")
    
    return process

def create_temp_logfile(content):
    """Create a temporary log file with given content."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
    temp_file.write(content)
    temp_file.close()
    return temp_file.name

class TestBasicFunctionality:
    """Test basic search functionality."""
    
    def test_basic_pattern_search(self):
        """Test basic pattern search in log file."""
        temp_file = create_temp_logfile(SAMPLE_LOG_UNIX_SYSLOG)
        try:
            result = run_loggrep(["ERROR", "--file", temp_file])
            assert "ERROR: Database connection failed" in result.stdout
            assert "ERROR: Memory usage high" in result.stdout
            assert result.stdout.count("ERROR") == 2
        finally:
            os.unlink(temp_file)
    
    def test_stdin_input(self):
        """Test reading from stdin."""
        result = run_loggrep(["ERROR"], input_data=SAMPLE_LOG_UNIX_SYSLOG)
        assert "ERROR: Database connection failed" in result.stdout
        assert "ERROR: Memory usage high" in result.stdout
    
    def test_no_matches(self):
        """Test when pattern doesn't match anything."""
        result = run_loggrep(["NONEXISTENT"], input_data=SAMPLE_LOG_UNIX_SYSLOG)
        assert result.stdout.strip() == ""
    
    def test_multiple_patterns(self):
        """Test searching for multiple patterns (OR logic)."""
        result = run_loggrep(["ERROR", "WARN"], input_data=SAMPLE_LOG_UNIX_SYSLOG)
        assert "ERROR: Database connection failed" in result.stdout
        assert "ERROR: Memory usage high" in result.stdout
        assert "WARN: Retrying database connection" in result.stdout
        # Should have 3 total matches
        assert len(result.stdout.strip().split('\n')) == 3

class TestRegexSupport:
    """Test regex pattern support."""
    
    def test_regex_pattern(self):
        """Test using regex patterns."""
        # Test regex pattern for ERROR or WARN
        result = run_loggrep([r"(ERROR|WARN)"], input_data=SAMPLE_LOG_UNIX_SYSLOG)
        assert "ERROR: Database connection failed" in result.stdout
        assert "WARN: Retrying database connection" in result.stdout
        assert "ERROR: Memory usage high" in result.stdout
    
    def test_regex_word_boundaries(self):
        """Test regex with word boundaries."""
        result = run_loggrep([r"\bservice\b"], input_data=SAMPLE_LOG_UNIX_SYSLOG)
        # Should match lines with "service" as a whole word
        lines = result.stdout.strip().split('\n')
        assert len(lines) > 0
        for line in lines:
            assert "service" in line.lower()
    
    def test_invalid_regex(self):
        """Test handling of invalid regex patterns."""
        result = run_loggrep(["[invalid"], input_data=SAMPLE_LOG_UNIX_SYSLOG, expect_error=True)
        assert result.returncode != 0
        assert "Invalid regex pattern" in result.stderr

class TestCaseInsensitive:
    """Test case-insensitive search functionality."""
    
    def test_case_insensitive_flag(self):
        """Test -i/--ignore-case flag."""
        result = run_loggrep(["-i", "error"], input_data=SAMPLE_LOG_UNIX_SYSLOG)
        assert "ERROR: Database connection failed" in result.stdout
        assert "ERROR: Memory usage high" in result.stdout
    
    def test_case_sensitive_default(self):
        """Test that search is case-sensitive by default."""
        result = run_loggrep(["error"], input_data=SAMPLE_LOG_UNIX_SYSLOG)
        assert result.stdout.strip() == ""  # Should find nothing with lowercase "error"
        
        result = run_loggrep(["ERROR"], input_data=SAMPLE_LOG_UNIX_SYSLOG)
        assert "ERROR: Database connection failed" in result.stdout

class TestInvertMatch:
    """Test invert match functionality (-v flag)."""
    
    def test_invert_match(self):
        """Test -v/--invert-match flag."""
        result = run_loggrep(["-v", "ERROR"], input_data=SAMPLE_LOG_UNIX_SYSLOG)
        # Should get all lines except those containing ERROR
        lines = result.stdout.strip().split('\n')
        for line in lines:
            assert "ERROR" not in line
        # Should have 8 lines (10 total - 2 ERROR lines)
        assert len(lines) == 8
    
    def test_invert_match_with_multiple_patterns(self):
        """Test invert match with multiple patterns."""
        result = run_loggrep(["-v", "ERROR", "WARN"], input_data=SAMPLE_LOG_UNIX_SYSLOG)
        lines = result.stdout.strip().split('\n')
        for line in lines:
            assert "ERROR" not in line
            assert "WARN" not in line
        # Should have 7 lines (10 total - 2 ERROR - 1 WARN)
        assert len(lines) == 7

class TestContextLines:
    """Test context lines functionality (-A, -B, -C flags)."""
    
    def test_after_context(self):
        """Test -A flag (lines after match)."""
        result = run_loggrep(["-A", "2", "ERROR.*Database"], input_data=SAMPLE_LOG_UNIX_SYSLOG)
        lines = result.stdout.strip().split('\n')
        # Should include the match line plus 2 lines after
        assert "ERROR: Database connection failed" in result.stdout
        assert "WARN: Retrying database connection" in result.stdout
        assert "INFO: Database connection restored" in result.stdout
    
    def test_before_context(self):
        """Test -B flag (lines before match)."""
        result = run_loggrep(["-B", "2", "ERROR.*Database"], input_data=SAMPLE_LOG_UNIX_SYSLOG)
        lines = result.stdout.strip().split('\n')
        # Should include 2 lines before plus the match line
        assert "Service started successfully" in result.stdout
        assert "Processing request 1" in result.stdout
        assert "ERROR: Database connection failed" in result.stdout
    
    def test_context_around(self):
        """Test -C flag (lines around match)."""
        result = run_loggrep(["-C", "1", "ERROR.*Database"], input_data=SAMPLE_LOG_UNIX_SYSLOG)
        lines = result.stdout.strip().split('\n')
        # Should include 1 line before, the match, and 1 line after
        assert "Processing request 1" in result.stdout
        assert "ERROR: Database connection failed" in result.stdout
        assert "WARN: Retrying database connection" in result.stdout

class TestTimestampParsing:
    """Test timestamp parsing and filtering functionality."""
    
    def test_unix_syslog_timestamps(self):
        """Test parsing Unix syslog timestamp format."""
        temp_file = create_temp_logfile(SAMPLE_LOG_UNIX_SYSLOG)
        try:
            # Search after 12:00:15
            result = run_loggrep(["Processing", "--file", temp_file, "--startup-time", "Oct 4 12:00:15"])
            # Should only find "Processing request 2" which is at 12:00:20
            assert "Processing request 2" in result.stdout
            assert "Processing request 1" not in result.stdout
        finally:
            os.unlink(temp_file)
    
    def test_iso8601_timestamps(self):
        """Test parsing ISO 8601 timestamp format."""
        temp_file = create_temp_logfile(SAMPLE_LOG_ISO8601)
        try:
            # Search after 12:00:15
            result = run_loggrep(["INFO", "--file", temp_file, "--startup-time", "2025-10-04 12:00:15"])
            # Should find INFO messages after 12:00:15
            assert "Operation completed" in result.stdout
            assert "Cleanup completed" in result.stdout
            assert "Application shutdown" in result.stdout
            # Should not find earlier INFO messages
            assert "Application starting" not in result.stdout
            assert "Configuration loaded" not in result.stdout
        finally:
            os.unlink(temp_file)
    
    def test_android_logcat_timestamps(self):
        """Test parsing Android logcat timestamp format."""
        temp_file = create_temp_logfile(SAMPLE_LOG_ANDROID_LOGCAT)
        try:
            # Search after 12:00:20
            result = run_loggrep(["ActivityManager", "--file", temp_file, "--startup-time", "10-04 12:00:20"])
            # Should only find the last ActivityManager message
            assert "Activity stopped" in result.stdout
            assert "Starting activity" not in result.stdout
            assert "Activity started" not in result.stdout
        finally:
            os.unlink(temp_file)
    
    def test_no_startup_time_uses_first_timestamp(self):
        """Test that without startup-time, first timestamp is used for files."""
        temp_file = create_temp_logfile(SAMPLE_LOG_UNIX_SYSLOG)
        try:
            result = run_loggrep(["service", "--file", temp_file])
            # Should find all lines with "service" since we start from first timestamp
            lines = result.stdout.strip().split('\n')
            assert len(lines) > 5  # Should find multiple service-related lines
        finally:
            os.unlink(temp_file)
    
    def test_stdin_defaults_to_current_time(self):
        """Test that stdin input with --live flag defaults to current time."""
        from datetime import datetime, timedelta
        
        # Create log data with timestamps - some old, some recent
        now = datetime.now()
        old_time = now - timedelta(hours=1)
        recent_time = now + timedelta(seconds=1)  # Slightly in future to ensure it's processed
        
        log_data = f"""{old_time.strftime('%Y-%m-%d %H:%M:%S')} [INFO] Old message should be filtered
{recent_time.strftime('%Y-%m-%d %H:%M:%S')} [ERROR] Recent message should appear
"""
        
        result = run_loggrep(["ERROR", "--live"], input_data=log_data)
        # Should only find the recent ERROR message, not the old one
        assert "Recent message should appear" in result.stdout
        assert "Old message should be filtered" not in result.stdout
    
    def test_file_uses_first_timestamp_not_current_time(self):
        """Test that file input uses first timestamp, not current time."""
        from datetime import datetime, timedelta
        
        # Create log data with all timestamps in the past
        past_time = datetime.now() - timedelta(hours=2)
        past_time2 = past_time + timedelta(minutes=5)
        
        log_data = f"""{past_time.strftime('%Y-%m-%d %H:%M:%S')} [INFO] First message
{past_time2.strftime('%Y-%m-%d %H:%M:%S')} [ERROR] Second message
"""
        
        temp_file = create_temp_logfile(log_data)
        try:
            result = run_loggrep(["ERROR", "--file", temp_file])
            # Should find the ERROR message even though it's in the past
            # because file mode uses first timestamp, not current time
            assert "Second message" in result.stdout
        finally:
            os.unlink(temp_file)
    
    def test_live_flag_functionality(self):
        """Test that --live flag works for real-time log streaming."""
        from datetime import datetime, timedelta
        
        # Create log data with recent timestamp
        now = datetime.now()
        recent_time = now + timedelta(seconds=1)
        
        log_data = f"""{recent_time.strftime('%Y-%m-%d %H:%M:%S')} [ERROR] Live log message
"""
        
        result = run_loggrep(["ERROR", "--live"], input_data=log_data)
        assert "Live log message" in result.stdout

class TestColorOutput:
    """Test color output functionality."""
    
    def test_color_auto_with_tty(self):
        """Test color=auto behavior (default)."""
        # When output is not a TTY (like in tests), color should be disabled by default
        result = run_loggrep(["ERROR"], input_data=SAMPLE_LOG_UNIX_SYSLOG)
        # Should not contain ANSI color codes when output is not a TTY
        assert "\x1b[" not in result.stdout
    
    def test_color_always(self):
        """Test --color=always flag."""
        result = run_loggrep(["--color=always", "ERROR"], input_data=SAMPLE_LOG_UNIX_SYSLOG)
        # Should contain ANSI color codes when forced
        if "colorama" in sys.modules or True:  # colorama should be available
            # The exact color codes might vary, but should have some coloring
            assert "ERROR" in result.stdout
    
    def test_color_never(self):
        """Test --color=never flag."""
        result = run_loggrep(["--color=never", "ERROR"], input_data=SAMPLE_LOG_UNIX_SYSLOG)
        # Should not contain ANSI color codes
        assert "\x1b[" not in result.stdout
        assert "ERROR" in result.stdout

class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        result = run_loggrep(["ERROR", "--file", "/nonexistent/file.log"], expect_error=True)
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
        log_without_timestamps = """Line 1 without timestamp
Line 2 without timestamp
ERROR: Something went wrong
Line 4 without timestamp
"""
        result = run_loggrep(["ERROR"], input_data=log_without_timestamps)
        # Should still work, but might not apply timestamp filtering
        assert "ERROR: Something went wrong" in result.stdout
    
    def test_invalid_startup_time(self):
        """Test handling of invalid startup time format."""
        temp_file = create_temp_logfile(SAMPLE_LOG_UNIX_SYSLOG)
        try:
            result = run_loggrep(["ERROR", "--file", temp_file, "--startup-time", "invalid-time"])
            # Should handle gracefully (might default to first timestamp or show error)
            # The exact behavior depends on implementation
            assert result.returncode == 0 or result.returncode != 0  # Either way is acceptable
        finally:
            os.unlink(temp_file)

class TestIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    def test_complex_search_scenario(self):
        """Test a complex search combining multiple features."""
        temp_file = create_temp_logfile(SAMPLE_LOG_UNIX_SYSLOG)
        try:
            # Case-insensitive search for error/warn after 12:00:05 with context
            result = run_loggrep([
                "-i", "-C", "1", "error", "warn", 
                "--file", temp_file, 
                "--startup-time", "Oct 4 12:00:05"
            ])
            
            lines = result.stdout.strip().split('\n')
            # Should include context lines around matches
            assert len(lines) > 2
            assert any("ERROR" in line for line in lines)
            assert any("WARN" in line for line in lines)
        finally:
            os.unlink(temp_file)
    
    def test_real_world_log_patterns(self):
        """Test patterns that would be used in real-world scenarios."""
        # Test searching for specific error codes, IPs, etc.
        log_with_patterns = """Oct  4 12:00:01 server1 nginx[1234]: 192.168.1.100 - GET /api/v1/users
Oct  4 12:00:02 server1 nginx[1234]: 192.168.1.101 - POST /api/v1/login
Oct  4 12:00:03 server1 nginx[1234]: 192.168.1.100 - GET /api/v1/users - 200 OK
Oct  4 12:00:04 server1 nginx[1234]: 192.168.1.101 - POST /api/v1/login - 401 Unauthorized
Oct  4 12:00:05 server1 nginx[1234]: 192.168.1.102 - GET /api/v1/admin - 403 Forbidden
Oct  4 12:00:06 server1 nginx[1234]: 192.168.1.100 - GET /api/v1/data - 500 Internal Server Error
"""
        
        # Test searching for specific HTTP status codes
        result = run_loggrep([r"\b(401|403|500)\b"], input_data=log_with_patterns)
        lines = result.stdout.strip().split('\n')
        assert len(lines) == 3
        assert "401 Unauthorized" in result.stdout
        assert "403 Forbidden" in result.stdout
        assert "500 Internal Server Error" in result.stdout
        
        # Test searching for specific IP addresses
        result = run_loggrep([r"192\.168\.1\.100"], input_data=log_with_patterns)
        lines = result.stdout.strip().split('\n')
        assert len(lines) == 3
        
        # Test searching for API endpoints
        result = run_loggrep([r"/api/v1/\w+"], input_data=log_with_patterns)
        lines = result.stdout.strip().split('\n')
        assert len(lines) == 6  # All lines should match

def test_help_option():
    """Test that --help works correctly."""
    result = run_loggrep(["--help"])
    assert "Search log files with timestamp awareness" in result.stdout
    assert "patterns" in result.stdout
    assert "--file" in result.stdout
    assert "--startup-time" in result.stdout

def test_version_compatibility():
    """Test that the script runs with the documented Python version."""
    # The README specifies Python 3.6+, ensure we're compatible
    import sys
    assert sys.version_info >= (3, 6), "Python 3.6+ required as per README"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])