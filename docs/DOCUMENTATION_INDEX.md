# 📚 Loggrep Documentation Index

Welcome to the comprehensive documentation for loggrep! This index helps you find the right documentation for your needs.

## 🚀 Quick Start

| Document | Purpose | For Who |
|----------|---------|---------|
| [../README.md](../README.md) | Main project overview and usage | Everyone |
| [../Makefile](../Makefile) | Development commands | Developers |

## 📖 User Documentation

### Basic Usage
- **[../README.md](../README.md)** - Complete user guide with examples
  - Installation instructions
  - Command-line usage
  - Timestamp format support
  - Real-world examples

### Advanced Features
- **Live log monitoring** - Real-time log streaming with `--live` flag
- **Multi-pattern search** - OR logic for multiple patterns
- **Context display** - Show surrounding lines with `-A`, `-B`, `-C`
- **Flexible timestamp parsing** - Support for multiple log formats

## 🔧 Developer Documentation

### Development Setup
- **[DOCKER_TESTING.md](DOCKER_TESTING.md)** - Complete Docker testing guide
  - Multi-version Python testing
  - Development containers
  - CI/CD integration
  - Troubleshooting guide

### Testing
- **[TESTS.md](TESTS.md)** - Comprehensive test documentation
  - Test suite overview
  - Running tests locally and with Docker
  - Test categories and coverage
- **[TEST_SUMMARY.md](TEST_SUMMARY.md)** - Executive summary of test results

### Development Workflow
```bash
# Quick development commands
make help                    # Show all available commands
./scripts/dev.sh help       # Development workflow options
./scripts/test_docker.sh help  # Docker testing options
```

## 🐳 Docker & Multi-Version Testing

### Primary Resources
- **[DOCKER_TESTING.md](DOCKER_TESTING.md)** - Complete Docker guide
- **[../Dockerfile](../Dockerfile)** - Multi-stage builds for Python 3.7-3.14
- **[../docker-compose.yml](../docker-compose.yml)** - Service definitions
- **[../scripts/test_docker.sh](../scripts/test_docker.sh)** - Testing script

### Quick Commands
```bash
make test-docker            # Test all Python versions
make test-docker-py310      # Test specific version
make docker-dev             # Start development container
```

## 📋 Project Management

### Planning & Progress
- **[ROADMAP.md](ROADMAP.md)** - Project roadmap and future plans
- **[NEXT_STEPS.md](NEXT_STEPS.md)** - Immediate next steps
- **[CHANGELOG.md](CHANGELOG.md)** - Release history and changes

### Analysis & Background
- **[EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)** - Project overview
- **[COMPETITIVE_ANALYSIS.md](COMPETITIVE_ANALYSIS.md)** - Comparison with alternatives
- **[PACKAGE_MIGRATION.md](PACKAGE_MIGRATION.md)** - Package structure evolution

## 🔄 CI/CD & Quality Assurance

### Automation
- **[CI_CD_EXPLANATION.md](CI_CD_EXPLANATION.md)** - Complete CI/CD guide
- **[../.github/workflows/test.yml](../.github/workflows/test.yml)** - GitHub Actions workflow
- **[../codecov.yml](../codecov.yml)** - Coverage configuration

### Quality Tools
- **[../pyproject.toml](../pyproject.toml)** - Project configuration
  - Build system settings
  - Development dependencies
  - Tool configurations (black, mypy, pytest)

## 🛠️ Development Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| [../scripts/dev.sh](../scripts/dev.sh) | Development workflow | `./scripts/dev.sh validate` |
| [../scripts/test_docker.sh](../scripts/test_docker.sh) | Multi-version testing | `./scripts/test_docker.sh all` |

## 📊 Testing & Quality Metrics

### Test Results
- **33 total tests** across 8 test categories
- **100% functionality coverage** including live streaming
- **Multi-version compatibility** - Python 3.7 through 3.12
- **Docker-based testing** for consistency

### Quality Standards
- **Type checking** with mypy
- **Code formatting** with black and isort
- **Linting** with flake8
- **Coverage reporting** per Python version

## 🎯 Quick Navigation by Role

### 👨‍💻 Developers
1. Start with [../README.md](../README.md) for overview
2. Follow [DOCKER_TESTING.md](DOCKER_TESTING.md) for setup
3. Use `make help` for daily commands
4. Check [TESTS.md](TESTS.md) for testing

### 👩‍💼 Project Managers
1. [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) - Project overview
2. [ROADMAP.md](ROADMAP.md) - Future planning
3. [TEST_SUMMARY.md](TEST_SUMMARY.md) - Quality metrics
4. [CHANGELOG.md](CHANGELOG.md) - Release history

### 🔧 DevOps Engineers
1. [CI_CD_EXPLANATION.md](CI_CD_EXPLANATION.md) - Pipeline details
2. [DOCKER_TESTING.md](DOCKER_TESTING.md) - Container setup
3. [../.github/workflows/test.yml](../.github/workflows/test.yml) - GitHub Actions
4. [../codecov.yml](../codecov.yml) - Coverage configuration

### 👤 End Users
1. [../README.md](../README.md) - Complete user guide
2. `loggrep --help` - Command-line help
3. Examples in README for common use cases

## 🔍 Finding Specific Information

### Installation & Setup
- **User installation**: [../README.md](../README.md#installation)
- **Development setup**: [DOCKER_TESTING.md](DOCKER_TESTING.md#quick-start)
- **Docker setup**: [DOCKER_TESTING.md](DOCKER_TESTING.md#prerequisites)

### Usage Examples
- **Basic usage**: [../README.md](../README.md#usage)
- **Advanced examples**: [../README.md](../README.md#examples)
- **Live monitoring**: [../README.md](../README.md#live-log-monitoring)

### Testing
- **Running tests**: [TESTS.md](TESTS.md#running-tests)
- **Docker testing**: [DOCKER_TESTING.md](DOCKER_TESTING.md#basic-usage)
- **Test results**: [TEST_SUMMARY.md](TEST_SUMMARY.md)

### Development
- **Contributing**: [../README.md](../README.md#contributing)
- **Code quality**: [TESTS.md](TESTS.md#quality-assurance)
- **Development workflow**: [DOCKER_TESTING.md](DOCKER_TESTING.md#development-workflow)

This documentation is maintained and updated with each release. For the most current information, always refer to the main [../README.md](../README.md).