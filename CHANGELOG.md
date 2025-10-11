# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-15

### Added
- Initial release of loggrep as a proper Python package
- Timestamp-aware log searching with multiple format support
- Pattern matching with regex support
- Context lines display (-A, -B, -C flags)
- Case-insensitive search (-i flag)
- Invert match functionality (-v flag)
- Colored output support
- Multiple pattern support (OR logic)
- Support for Unix syslog, ISO 8601, and Android logcat timestamp formats
- Comprehensive test suite with 29 tests
- Professional packaging with PyPI support
- Command-line interface with rich help and examples

### Technical Details
- Modular architecture with separate core, CLI, and timestamp modules
- Type hints throughout codebase
- Proper error handling and user-friendly error messages
- Memory-efficient processing for large files
- Cross-platform compatibility (Linux, macOS, Windows)

### Supported Timestamp Formats
- Unix syslog: `Oct  5 14:30:02`
- ISO 8601: `2025-10-05 14:30:02.123`
- Android logcat: `10-05 14:30:02.123`
- Custom formats: `Oct 05, 2025 14:30:02`