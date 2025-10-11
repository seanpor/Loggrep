# Docker Testing Guide

This document describes the Docker-based multi-version testing setup for loggrep.

## Overview

The loggrep project supports Python 3.7-3.12 and uses Docker to ensure compatibility across all these versions. This setup provides:

- **Consistency**: Same environment across different development machines
- **Isolation**: Each Python version runs in its own container
- **Comprehensive Testing**: Automated testing across all supported versions
- **CI/CD Integration**: GitHub Actions workflows use the same Docker setup

## Quick Start

### Prerequisites
- Docker (20.10 or later)
- Docker Compose (v2.0 or later)

### Basic Usage

```bash
# Test all Python versions
make test-docker

# Test specific Python version
make test-docker-py312

# Quick development setup
make install-dev && make test
```

## Available Commands

### Make Targets
- `make test-docker` - Test all Python versions (3.7-3.12)
- `make test-docker-py37` - Test Python 3.7 only
- `make test-docker-py38` - Test Python 3.8 only
- `make test-docker-py39` - Test Python 3.9 only
- `make test-docker-py310` - Test Python 3.10 only
- `make test-docker-py311` - Test Python 3.11 only
- `make test-docker-py312` - Test Python 3.12 only
- `make docker-build` - Build all Docker images
- `make docker-dev` - Start development container

### Docker Compose Services
- `test_py37` through `test_py312` - Test services for each Python version
- `dev` - Development container with interactive shell

### Scripts
- `./scripts/test_docker.sh` - Multi-version testing script
- `./scripts/dev.sh` - Development workflow script

## Docker Configuration

### Dockerfile
The Dockerfile defines multi-stage builds for each Python version:

```dockerfile
# Python 3.12
FROM python:3.12-slim as py312
WORKDIR /app
COPY . .
RUN pip install --upgrade pip && \
    pip install -e ".[dev]"
```

Each stage:
1. Uses the official Python slim image
2. Sets up the working directory
3. Copies the project files
4. Installs the package in development mode with all dependencies

### docker-compose.yml
Defines services for each Python version with:
- Individual coverage reports
- Volume mounting for live development
- Proper build contexts and targets

## Testing Workflow

### Local Development
1. **Quick Test**: `make test` - Test with your local Python version
2. **Format Code**: `make format` - Auto-format with black and isort
3. **Lint Code**: `make lint` - Run flake8 and mypy checks
4. **Multi-Version Test**: `make test-docker` - Test all versions

### CI/CD Integration
The GitHub Actions workflow (`.github/workflows/test.yml`) includes:
- **Matrix Testing**: Traditional matrix testing with GitHub Actions
- **Docker Testing**: Docker-based testing for verification
- **Code Quality**: Linting, formatting, and type checking
- **Integration Testing**: Package building and installation verification

## Development Containers

### Interactive Development
Start a development container with full shell access:

```bash
# Start development container
docker-compose run --rm dev

# Or use make target
make docker-dev
```

The development container includes:
- All development dependencies pre-installed
- Volume-mounted source code for live editing
- Interactive bash shell
- All loggrep commands available

### VS Code Integration
For VS Code users, the development container can be used with the Remote-Containers extension:

1. Install the "Remote - Containers" extension
2. Open the project folder in VS Code
3. Use "Remote-Containers: Reopen in Container" command

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Add user to docker group (requires logout/login)
   sudo usermod -aG docker $USER
   
   # Or run with sudo
   sudo make test-docker
   ```

2. **Port Conflicts**
   ```bash
   # Stop conflicting containers
   docker-compose down
   
   # Remove all containers
   docker system prune
   ```

3. **Image Build Failures**
   ```bash
   # Force rebuild without cache
   docker-compose build --no-cache
   
   # Clean and rebuild
   make clean && make docker-build
   ```

4. **Out of Disk Space**
   ```bash
   # Clean unused Docker resources
   docker system prune -a
   
   # Remove old images
   docker image prune -a
   ```

### Performance Tips

1. **Layer Caching**: The Dockerfile is optimized for Docker layer caching
2. **Multi-stage Builds**: Each Python version is built in parallel when possible
3. **.dockerignore**: Reduces build context size by excluding unnecessary files
4. **Volume Mounts**: Source code changes don't require image rebuilds

## Advanced Usage

### Custom Test Commands
Run custom commands in any Python environment:

```bash
# Run custom command in Python 3.10
docker-compose run --rm test_py310 bash -c "python --version && loggrep --help"

# Interactive shell in specific version
docker-compose run --rm test_py310 bash
```

### Coverage Reports
Each Python version generates its own coverage report:
- `coverage_py37.xml` through `coverage_py312.xml`
- Terminal output shows coverage percentages
- XML reports can be uploaded to coverage services

### Parallel Testing
Run multiple Python versions in parallel:

```bash
# Run all versions in background
docker-compose up -d

# Check logs
docker-compose logs

# Clean up
docker-compose down
```

## Integration with CI/CD

The Docker setup integrates seamlessly with:
- **GitHub Actions**: Uses the same containers and commands
- **GitLab CI**: Can adapt the docker-compose commands
- **Jenkins**: Docker plugin can use our configurations
- **Local Development**: Same environment everywhere

## File Structure

```
├── Dockerfile              # Multi-stage builds for all Python versions
├── docker-compose.yml      # Service definitions
├── .dockerignore          # Build context optimization
├── Makefile               # Development commands
├── scripts/
│   ├── test_docker.sh     # Multi-version testing script
│   └── dev.sh             # Development workflow script
└── .github/
    └── workflows/
        └── test.yml        # GitHub Actions CI/CD
```

This setup ensures loggrep works reliably across all supported Python versions while providing a smooth development experience.