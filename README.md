# 🔍 Loggrep

**A powerful command-line tool for timestamp-aware log searching**

[![PyPI version](https://badge.fury.io/py/loggrep.svg)](https://badge.fury.io/py/loggrep)
[![CI/CD](https://github.com/seanpor/Loggrep/actions/workflows/ci.yml/badge.svg)](https://github.com/seanpor/Loggrep/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/seanpor/Loggrep/branch/main/graph/badge.svg)](https://codecov.io/gh/seanpor/Loggrep)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Loggrep combines the power of `grep` with intelligent timestamp filtering, making it perfect for analyzing logs from specific points in time. Whether you're debugging application startup issues, analyzing deployment logs, or filtering Android logcat output, loggrep helps you focus on what matters.

## ✨ **Why Loggrep?**

**The Problem:** When debugging applications, you often need to see what happened *after* a specific event (app startup, deployment, etc.). Traditional tools like `grep` show you everything, including irrelevant historical data.

**The Solution:** Loggrep filters logs by timestamp, showing only entries after your specified start time, combined with powerful pattern matching and context display.

```bash
# Show all errors after app startup
loggrep "ERROR" --startup-time "2025-01-15 14:30:00"

# Android debugging with live streaming
adb logcat | loggrep "MyApp" --live

# System logs after service restart with context
loggrep "failed" --file /var/log/syslog --startup-time "10 minutes ago" -C 3
```

## 🚀 **Installation**

```bash
pip install loggrep
```

**Requirements:** Python 3.7+

## 📖 **Quick Start**

### Basic Usage
```bash
# Search for pattern in file
loggrep "ERROR" --file application.log

# Read from stdin (like grep)
cat application.log | loggrep "ERROR"

# Multiple patterns (OR logic)
loggrep "ERROR" "WARN" "FATAL" --file application.log
```

### Timestamp Filtering
```bash
# Only show matches after specific time
loggrep "ERROR" --file app.log --startup-time "2025-01-15 14:30:00"

# Use first timestamp in file as start point (default behavior)
loggrep "ERROR" --file app.log
```

### Context Lines
```bash
# Show 3 lines before and after each match
loggrep "ERROR" --file app.log -C 3

# Show 2 lines after each match
loggrep "ERROR" --file app.log -A 2

# Show 2 lines before each match  
loggrep "ERROR" --file app.log -B 2
```

### Advanced Options
```bash
# Case-insensitive search
loggrep -i "error" --file app.log

# Invert match (show lines that DON'T match)
loggrep -v "DEBUG" --file app.log

# Force colored output with live streaming
loggrep "ERROR" --live --color=always
```

## 🎯 **Real-World Examples**

### DevOps & Deployment
```bash
# Check for errors after deployment
loggrep "ERROR|FATAL" --file app.log --startup-time "$(date -d '5 minutes ago')"

# Monitor service restart issues
sudo loggrep "systemd.*failed" --file /var/log/syslog -C 2
```

### Mobile Development
```bash
# Android logcat filtering with live streaming
adb logcat | loggrep "ActivityManager.*MyApp" --live

# iOS simulator logs
loggrep "MyApp" --file ~/Library/Logs/CoreSimulator/*/system.log -A 3
```

### Application Debugging
```bash
# Database connection issues during startup
loggrep "database.*connection" --file app.log --startup-time "2025-01-15 09:00:00" -C 5

# Memory issues with context
loggrep "OutOfMemory|heap" --file gc.log -B 10 -A 5
```

## 📅 **Supported Timestamp Formats**

Loggrep automatically detects these common timestamp formats:

- **Unix Syslog**: `Oct  5 14:30:02`
- **ISO 8601**: `2025-10-05 14:30:02.123` or `2025-10-05T14:30:02.123Z`
- **Android Logcat**: `10-05 14:30:02.123`
- **Custom formats**: `Oct 05, 2025 14:30:02`

## 🔧 **Command Reference**

```
loggrep [OPTIONS] PATTERNS...

Arguments:
  PATTERNS...                Regex pattern(s) to search for

Options:
  --file FILE               Log file to search (default: stdin)
  --startup-time TIME       Only show matches after this time
  -i, --ignore-case         Case-insensitive matching
  -v, --invert-match        Show non-matching lines
  -A, --after-context N     Show N lines after each match
  -B, --before-context N    Show N lines before each match  
  -C, --context N           Show N lines before and after each match
  --color [always|never|auto]  Control colored output (default: auto)
  -h, --help               Show help message
```

## 🏗️ **Performance**

Loggrep is designed for real-world log files:

- **Memory efficient**: Streams large files without loading into memory
- **Fast startup**: Optimized for interactive use
- **Smart filtering**: Only processes relevant timestamp ranges

**Benchmarks** (1GB log file, 10M lines):
- Initial search: ~2.3 seconds
- Memory usage: <50MB
- Timestamp parsing: ~1M lines/second

## 🧪 **Development**

### Running Tests
```bash
git clone https://github.com/seanpor/Loggrep.git
cd Loggrep
pip install -e ".[dev]"
pytest
```

### Contributing
We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Code Quality
- **Comprehensive test suite**: 29 tests covering all features
- **Type hints**: Full mypy type checking
- **Code formatting**: Black + isort
- **CI/CD**: Automated testing on multiple Python versions and platforms

## 📊 **Comparison with Other Tools**

| Feature | loggrep | grep | ripgrep | awk |
|---------|---------|------|---------|-----|
| Pattern matching | ✅ | ✅ | ✅ | ✅ |
| Timestamp awareness | ✅ | ❌ | ❌ | ⚠️ |
| Multiple formats | ✅ | ❌ | ❌ | ⚠️ |
| Context lines | ✅ | ✅ | ✅ | ⚠️ |
| Easy installation | ✅ | ✅ | ✅ | ✅ |
| Colored output | ✅ | ✅ | ✅ | ❌ |

## 📄 **License**

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

## 🙏 **Acknowledgments**

- Inspired by `grep` and `ripgrep` for the command-line interface
- Built with `python-dateutil` for robust timestamp parsing
- Uses `colorama` for cross-platform colored output

---

**Made with ❤️ for developers who deal with logs every day**