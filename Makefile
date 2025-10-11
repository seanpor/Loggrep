# Loggrep Makefile
# Provides convenient targets for development, testing, and CI/CD

.PHONY: help install install-dev test test-docker test-docker-all test-docker-py37 test-docker-py38 test-docker-py39 test-docker-py310 test-docker-py311 test-docker-py312 lint format clean build publish docker-build docker-dev

# Default target
help:
	@echo "Loggrep Development Commands"
	@echo "============================"
	@echo ""
	@echo "Development:"
	@echo "  install          Install loggrep in development mode"
	@echo "  install-dev      Install with all development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run tests with current Python version"
	@echo "  test-docker      Run tests across all Python versions (Docker)"
	@echo "  test-docker-py37 Test only Python 3.7 (Docker)"
	@echo "  test-docker-py38 Test only Python 3.8 (Docker)"
	@echo "  test-docker-py39 Test only Python 3.9 (Docker)"
	@echo "  test-docker-py310 Test only Python 3.10 (Docker)"
	@echo "  test-docker-py311 Test only Python 3.11 (Docker)"
	@echo "  test-docker-py312 Test only Python 3.12 (Docker)"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run linting checks (flake8, mypy)"
	@echo "  format           Format code (black, isort)"
	@echo ""
	@echo "Build & Release:"
	@echo "  build            Build distribution packages"
	@echo "  publish          Publish to PyPI (requires authentication)"
	@echo "  clean            Clean build artifacts"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build     Build all Docker images"
	@echo "  docker-dev       Start development container"

# Development setup
install:
	pip install .

install-dev:
	pip install ".[dev]"

install-editable:
	pip install -e ".[dev]"

# Local testing
test:
	@echo "Running tests..."
	rm -f coverage*.xml .coverage
	pytest --cov=src/loggrep --cov-report=term --cov-report=xml -v

# Docker-based multi-version testing
test-docker:
	./scripts/test_docker.sh all

test-docker-py37:
	./scripts/test_docker.sh 3.7

test-docker-py38:
	./scripts/test_docker.sh 3.8

test-docker-py39:
	./scripts/test_docker.sh 3.9

test-docker-py310:
	./scripts/test_docker.sh 3.10

test-docker-py311:
	./scripts/test_docker.sh 3.11

test-docker-py312:
	./scripts/test_docker.sh 3.12

# Code quality
lint:
	@echo "Running flake8..."
	flake8 src/ tests/
	@echo "Running mypy..."
	mypy src/

format:
	@echo "Running black..."
	black src/ tests/
	@echo "Running isort..."
	isort src/ tests/

# Build and publish
build: clean
	python -m build

publish: build
	python -m twine upload dist/*

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf coverage*.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Docker operations
docker-build:
	docker-compose build

docker-dev:
	docker-compose run --rm dev

# CI/CD helper targets
ci-test: test-docker
	@echo "All CI tests completed"

# Quick development workflow
dev-setup: install-dev
	@echo "Development environment ready!"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make test-docker' to test all Python versions"