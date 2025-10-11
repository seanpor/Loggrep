#!/bin/bash
# Development workflow script for loggrep
# Provides a quick way to set up, test, and validate the project

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing=()
    
    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi
    
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        missing+=("pip")
    fi
    
    if ! command -v docker &> /dev/null; then
        log_warning "Docker not found - Docker-based testing will be unavailable"
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_warning "Docker Compose not found - Docker-based testing will be unavailable"
    fi
    
    if [ ${#missing[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing[*]}"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Set up development environment
setup_dev() {
    log_info "Setting up development environment..."
    
    # Install in development mode
    pip install ".[dev]"
    
    log_success "Development environment ready"
    log_info "Next steps:"
    log_info "- Run 'make test' to run tests"
    log_info "- Run 'make test-docker' to test all Python versions"
    log_info "- Check 'docs/DOCUMENTATION_INDEX.md' for comprehensive docs"
}

# Run local tests
run_local_tests() {
    log_info "Running local tests..."
    
    pytest --cov=src/loggrep --cov-report=term --cov-report=xml -v
    
    log_success "Local tests completed"
}

# Run code quality checks
run_quality_checks() {
    log_info "Running code quality checks..."
    
    log_info "Running flake8..."
    if flake8 src/ tests/; then
        log_success "flake8 passed"
    else
        log_error "flake8 failed"
        return 1
    fi
    
    log_info "Running mypy..."
    if mypy src/; then
        log_success "mypy passed"
    else
        log_error "mypy failed"
        return 1
    fi
    
    log_success "Code quality checks completed"
}

# Format code
format_code() {
    log_info "Formatting code..."
    
    black src/ tests/
    isort src/ tests/
    
    log_success "Code formatting completed"
}

# Run Docker tests
run_docker_tests() {
    log_info "Running Docker-based multi-version tests..."
    
    if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
        log_error "Docker or Docker Compose not available"
        return 1
    fi
    
    ./scripts/test_docker.sh all
    
    log_success "Docker tests completed"
}

# Full validation workflow
run_full_validation() {
    log_info "Starting full validation workflow..."
    
    check_prerequisites
    setup_dev
    format_code
    run_quality_checks
    run_local_tests
    
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        run_docker_tests
    else
        log_warning "Skipping Docker tests - Docker not available"
    fi
    
    log_success "Full validation completed successfully!"
}

# Show usage
show_usage() {
    echo "Loggrep Development Workflow"
    echo "=========================="
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup         Set up development environment"
    echo "  test          Run local tests"
    echo "  test-docker   Run Docker-based multi-version tests"
    echo "  lint          Run code quality checks"
    echo "  format        Format code with black and isort"
    echo "  validate      Run full validation workflow"
    echo "  help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup      # Set up development environment"
    echo "  $0 test       # Run local tests"
    echo "  $0 validate   # Run complete validation"
}

# Main script logic
case "${1:-help}" in
    "setup")
        check_prerequisites
        setup_dev
        ;;
    "test")
        run_local_tests
        ;;
    "test-docker")
        run_docker_tests
        ;;
    "lint")
        run_quality_checks
        ;;
    "format")
        format_code
        ;;
    "validate")
        run_full_validation
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac