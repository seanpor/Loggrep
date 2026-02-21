# AI Agents Documentation

This document describes the AI development history and agent interactions for the Loggrep project.

## Project Overview

**Loggrep** is a timestamp-aware log filtering tool designed to help developers analyze logs from specific points in time. It combines the power of `grep` with intelligent timestamp parsing, making it perfect for debugging application startup issues, deployment logs, and live log streaming.

## Development History

### Agent Interactions and Contributions

#### 2025-10-18: Live Mode Timestamp Filtering Clarification

**Agent**: GitHub Copilot CLI (Claude-based)  
**Context**: User clarification that `adb logcat` does have timestamps and the filtering should work correctly

**Investigation Results:**
- Android logcat timestamps (`10-18 14:27:09.035`) are correctly detected and parsed
- The timestamp parsing converts `10-18 14:27:09.035` to `2025-10-18 14:27:09.035000` properly
- Live mode filtering is working as intended - it captures startup time and filters out older logs

**Root Cause Clarification:**
- The original issue was not a bug but expected behavior
- When running `date ; adb logcat | ./loggrep walkie`, historical logs are correctly filtered out
- Only logs generated AFTER loggrep startup will be displayed
- This is the intended design for live log monitoring

**Code Changes Made:**
- Removed unnecessary grace period logic that was masking the correct behavior
- Restored precise startup time filtering without artificial time adjustments
- Maintained the no-timestamp fallback logic for streams without any timestamps

**Expected Usage:**
1. Run `date ; adb logcat | ./loggrep walkie`  
2. Perform actions on the Android device that generate new logs containing "walkie"
3. New logs will appear in real-time, filtered by the pattern

**Testing Confirmed:**
- Historical timestamps (older than startup): correctly filtered out
- Future timestamps (newer than startup): correctly displayed
- Timestamp parsing accuracy: Android logcat format works perfectly
- All existing tests continue to pass

#### 2025-10-18: UTF-8 Encoding Fix and Live Mode Default

**Agent**: GitHub Copilot CLI (Claude-based)  
**Context**: User experiencing UTF-8 decode errors when using `adb logcat | loggrep walkie --live`

**Problem Identified:**
- `adb logcat` outputs binary data mixed with text that causes UTF-8 decode errors
- The error message was: `'utf-8' codec can't decode byte 0xc0 in position 758: invalid start byte`
- User had to manually specify `--live` flag for every stdin usage

**Solutions Implemented:**

1. **UTF-8 Encoding Error Fix:**
   - Modified `search_stdin()` method in `/src/loggrep/core.py`
   - Replaced direct `sys.stdin` usage with `io.TextIOWrapper` using `errors='replace'`
   - This matches the error handling strategy used for file reading
   - Binary data now appears as replacement characters (�) instead of causing crashes

2. **Default Live Mode for Stdin:**
   - Made `--live` the default behavior for stdin input
   - Added `--no-live` flag to disable live mode when needed
   - Updated help text and examples to reflect the new defaults
   - Maintained backward compatibility while improving user experience

**Code Changes:**
- `/src/loggrep/core.py`: Enhanced `search_stdin()` with proper encoding error handling
- `/src/loggrep/cli.py`: Modified argument parsing and logic for default live mode
- `/tests/test_loggrep.py`: Added comprehensive test for UTF-8 error handling

**Testing:**
- Added new test class `TestEncodingHandling` with binary data simulation
- All 67 existing tests continue to pass
- New test verifies that binary data doesn't cause crashes and is handled gracefully

**Documentation Updates:**
- Updated README.md examples to reflect new default behavior
- Created this AGENTS.md file to document AI development history

## Agent Guidelines

### For Future AI Agents Working on This Project

1. **Test-Driven Development:**
   - Always run existing tests before making changes (`python3 -m pytest tests/`)
   - Add tests for new features or bug fixes
   - Ensure backward compatibility

2. **Code Quality Standards:**
   - Maintain the existing code style and patterns
   - Use type hints consistently
   - Keep changes minimal and surgical
   - Follow the DRY principle

3. **Error Handling:**
   - The project emphasizes graceful error handling with helpful user messages
   - Use emoji prefixes for error messages (🔤, 🚫, 💡, etc.) to maintain consistency
   - Provide actionable tips for users when errors occur

4. **Performance Considerations:**
   - The tool is designed for real-time log streaming
   - Memory efficiency is important for large log files
   - Optimize for interactive use cases

5. **Cross-Platform Compatibility:**
   - Ensure changes work on Linux, macOS, and Windows
   - Test with multiple Python versions (3.7-3.14)
   - Use the Docker testing infrastructure when available

## Key Technical Decisions

### Encoding Strategy
- **Decision**: Use `errors='replace'` for stdin processing
- **Rationale**: Tools like `adb logcat` output binary data mixed with text
- **Impact**: Improves reliability for mobile development workflows

### Default Live Mode
- **Decision**: Make live mode default for stdin, add `--no-live` flag
- **Rationale**: Most stdin usage is for live streaming (adb logcat, tail -f, etc.)
- **Impact**: Reduces repetitive typing while maintaining flexibility

### Timestamp Parsing
- **Strategy**: Automatic format detection with caching for performance
- **Supported Formats**: Unix syslog, ISO 8601, Android logcat, custom formats
- **Performance**: ~1M lines/second processing rate

## Contributing Guidelines for AI Agents

1. **Understand the User Workflow:**
   - Primary use case: developers debugging applications
   - Common scenarios: Android development, server log analysis, deployment debugging
   - Focus on reducing friction in common workflows

2. **Maintain Professional Quality:**
   - Comprehensive error handling with helpful messages
   - Performance optimization for real-world log files
   - Cross-platform compatibility

3. **Documentation Standards:**
   - Update README.md for user-facing changes
   - Update this AGENTS.md file for development decisions
   - Include practical examples in documentation

4. **Testing Requirements:**
   - Add tests for new functionality
   - Ensure all existing tests pass
   - Use both unit tests and integration tests
   - Test edge cases (large files, binary data, malformed input)

## Future Development Areas

Based on the current codebase and user needs, future agents might consider:

1. **Enhanced Android Support:**
   - Better logcat format detection
   - Package name filtering improvements
   - Crash log analysis features

2. **Performance Optimizations:**
   - Streaming mode for very large files
   - Parallel processing for multiple files
   - Advanced timestamp caching

3. **Output Formatting:**
   - JSON output mode
   - Custom timestamp formats
   - Statistical summaries

4. **Integration Features:**
   - Git integration for deployment correlation
   - Cloud log service adapters
   - Plugin architecture for custom formats

---

*This document should be updated by AI agents when making significant changes to the project.*