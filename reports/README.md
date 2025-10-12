# Reports Directory

This directory contains all generated reports and artifacts from testing, coverage, profiling, and benchmarking.

## Structure

### 📊 `/coverage/`
Contains all code coverage reports and artifacts:
- `coverage.xml` - Main coverage report for CI/CD
- `coverage_py*.xml` - Version-specific coverage reports from Docker testing
- `htmlcov/` - HTML coverage reports for local viewing
- `.coverage` - Raw coverage data files

### 🏃 `/benchmarks/`
Performance benchmark results:
- `benchmark_baseline.json` - Baseline performance measurements
- `benchmark_results.json` - Current performance test results

### 🔍 `/profiling/`
Detailed performance profiling data:
- `profile_results_*.prof` - Python profiler output files
- Use with tools like `snakeviz` or `py-spy` for analysis

## Usage

### Viewing Coverage Reports
```bash
# Generate coverage report
make coverage

# Open HTML report
open reports/coverage/htmlcov/index.html
```

### Running Benchmarks
```bash
# Run performance benchmarks
make benchmark

# View results
cat reports/benchmarks/benchmark_results.json
```

### Profiling Analysis
```bash
# Install profiling tools
pip install snakeviz

# View profiling results
snakeviz reports/profiling/profile_results_*.prof
```

## Notes

- All files in this directory are automatically generated
- The directory is included in `.gitignore` to avoid committing large reports
- Coverage reports are uploaded to CI/CD for tracking trends
- Legacy paths (`htmlcov/`, `coverage.xml`) are maintained for CI compatibility