#!/bin/bash
# Multi-version Python testing script for loggrep
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🐳 Loggrep Multi-Version Python Testing"
echo "======================================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed or not in PATH"
    exit 1
fi

# Function to test a specific Python version
test_python_version() {
    local version=$1
    local service_name="test_py${version//./}"
    
    echo ""
    echo "🐍 Testing Python $version..."
    echo "-----------------------------"
    
    if docker-compose run --rm "$service_name"; then
        echo "✅ Python $version tests passed"
        return 0
    else
        echo "❌ Python $version tests failed"
        return 1
    fi
}

# Function to run all tests
run_all_tests() {
    local failed_versions=()
    local versions=("3.7" "3.8" "3.9" "3.10" "3.11" "3.12")
    
    echo "🔨 Building Docker images..."
    docker-compose build
    
    for version in "${versions[@]}"; do
        if ! test_python_version "$version"; then
            failed_versions+=("$version")
        fi
    done
    
    echo ""
    echo "📊 Test Summary"
    echo "==============="
    
    if [ ${#failed_versions[@]} -eq 0 ]; then
        echo "🎉 All Python versions passed!"
        return 0
    else
        echo "❌ Failed versions: ${failed_versions[*]}"
        return 1
    fi
}

# Parse command line arguments
case "${1:-all}" in
    "3.7"|"37")
        docker-compose build test_py37
        test_python_version "3.7"
        ;;
    "3.8"|"38")
        docker-compose build test_py38
        test_python_version "3.8"
        ;;
    "3.9"|"39")
        docker-compose build test_py39
        test_python_version "3.9"
        ;;
    "3.10"|"310")
        docker-compose build test_py310
        test_python_version "3.10"
        ;;
    "3.11"|"311")
        docker-compose build test_py311
        test_python_version "3.11"
        ;;
    "3.12"|"312")
        docker-compose build test_py312
        test_python_version "3.12"
        ;;
    "all"|"")
        run_all_tests
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [version|all|help]"
        echo ""
        echo "Test loggrep against different Python versions using Docker"
        echo ""
        echo "Arguments:"
        echo "  3.7, 3.8, 3.9, 3.10, 3.11, 3.12  Test specific Python version"
        echo "  all                                Test all Python versions (default)"
        echo "  help                               Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0               # Test all versions"
        echo "  $0 3.10          # Test only Python 3.10"
        echo "  $0 all           # Test all versions"
        ;;
    *)
        echo "❌ Unknown option: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
