# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-10-11

### Added
- **Docker-based multi-version testing**: Support for Python 3.7, 3.8, 3.9, 3.10, 3.11, 3.12
- **Comprehensive development workflow**: Makefile with all necessary commands
- **Live streaming functionality**: Proper `--live` flag for real-time log monitoring
- **Enhanced test suite**: 33 tests including proper live functionality tests
- **Development scripts**: `test_docker.sh` and `dev.sh` for streamlined workflows
- **CI/CD integration**: GitHub Actions workflow with Docker testing
- **Docker Compose**: Multi-service setup for parallel version testing
- **Documentation**: Complete Docker testing guide (`DOCKER_TESTING.md`)

### Fixed
- **Live test functionality**: Replaced static tests with proper live streaming simulation
- **Context lines implementation**: Completely rewritten for proper behavior
- **Lines without timestamps**: All lines are now processed correctly
- **Build system**: Optimized package configuration for reliable installation
- **Coverage reporting**: Fixed permission issues and multi-version support

### Changed
- **Test count**: Increased from 29 to 33 tests with better coverage
- **Testing strategy**: Docker-based approach for consistency across environments
- **Development workflow**: Unified commands through Makefile and scripts
- **Documentation structure**: Enhanced with comprehensive guides and examples

### Technical Improvements
- **Multi-stage Dockerfiles**: Optimized builds with layer caching
- **Build optimization**: `.dockerignore` for faster Docker builds
- **Error handling**: Better error messages and troubleshooting guides
- **Code quality**: Enhanced linting, formatting, and type checking integration

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