#!/usr/bin/env python3
"""
Performance benchmarking suite for Loggrep.

Tests various scenarios to measure performance and identify bottlenecks.
"""

import time
import tempfile
import os
import sys
import subprocess
import statistics
from typing import List, Dict, Any
from datetime import datetime
import psutil

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from loggrep.core import LogSearcher
from loggrep.timestamps import parse_timestamp, detect_timestamp_format


class PerformanceBenchmark:
    """Comprehensive performance benchmarking for Loggrep."""
    
    def __init__(self):
        self.results = {}
        self.test_data = {}
        
    def generate_test_data(self, size: str) -> str:
        """Generate test log data of various sizes."""
        sizes = {
            'small': 1000,      # 1K lines
            'medium': 10000,    # 10K lines  
            'large': 100000,    # 100K lines
            'xlarge': 1000000,  # 1M lines
        }
        
        num_lines = sizes.get(size, 1000)
        
        # Create realistic log entries with various timestamp formats
        log_templates = [
            "Oct 12 14:30:{:02d} server1 ERROR: Connection failed to database",
            "2025-10-12T14:30:{:02d}.123Z INFO: Processing request #{}",
            "10-12 14:30:{:02d}.456  1234  5678 E MyApp: Error in module {}",
            "2025/10/12 14:30:{:02d} [ERROR] Failed to parse config file",
            "12/Oct/2025:14:30:{:02d} +0000 \"GET /api/users HTTP/1.1\" 500",
            "05.10.2025 14:30:{:02d}.789 WARN: Memory usage is high",
        ]
        
        lines = []
        for i in range(num_lines):
            template = log_templates[i % len(log_templates)]
            second = i % 60
            lines.append(template.format(second, i))
            
        content = '\n'.join(lines) + '\n'
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(content)
            self.test_data[size] = {
                'file': f.name,
                'lines': num_lines,
                'size_mb': len(content) / (1024 * 1024)
            }
            
        return f.name

    def benchmark_function(self, func, *args, runs: int = 5, **kwargs) -> Dict[str, Any]:
        """Benchmark a function with multiple runs and collect statistics."""
        times = []
        memory_usage = []
        
        for _ in range(runs):
            # Measure memory before
            process = psutil.Process()
            mem_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Time the function
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            
            # Measure memory after
            mem_after = process.memory_info().rss / 1024 / 1024  # MB
            
            times.append(end_time - start_time)
            memory_usage.append(mem_after - mem_before)
            
        return {
            'mean_time': statistics.mean(times),
            'median_time': statistics.median(times),
            'min_time': min(times),
            'max_time': max(times),
            'std_time': statistics.stdev(times) if len(times) > 1 else 0,
            'mean_memory_mb': statistics.mean(memory_usage),
            'max_memory_mb': max(memory_usage),
            'times': times,
            'result_size': len(list(result)) if hasattr(result, '__iter__') else 1
        }

    def benchmark_timestamp_parsing(self) -> Dict[str, Any]:
        """Benchmark timestamp parsing performance."""
        print("🕒 Benchmarking timestamp parsing...")
        
        # Test various timestamp formats
        test_timestamps = [
            "Oct 12 14:30:45",
            "2025-10-12T14:30:45.123Z",
            "10-12 14:30:45.123",
            "2025/10/12 14:30:45",
            "12/Oct/2025:14:30:45",
            "05.10.2025 14:30:45.789",
        ]
        
        results = {}
        
        # Benchmark detection
        def detect_batch():
            return [detect_timestamp_format(f"Some log prefix {ts} rest of line") 
                   for ts in test_timestamps * 1000]
        
        results['detection'] = self.benchmark_function(detect_batch, runs=3)
        
        # Benchmark parsing
        def parse_batch():
            return [parse_timestamp(ts) for ts in test_timestamps * 1000]
        
        results['parsing'] = self.benchmark_function(parse_batch, runs=3)
        
        return results

    def benchmark_pattern_matching(self) -> Dict[str, Any]:
        """Benchmark pattern matching performance."""
        print("🔍 Benchmarking pattern matching...")
        
        # Generate test data
        test_file = self.generate_test_data('medium')
        
        results = {}
        patterns_tests = [
            (['ERROR'], 'single_pattern'),
            (['ERROR', 'WARN', 'FATAL'], 'multiple_patterns'),
            (['.*connection.*failed.*'], 'complex_regex'),
            (['(?i)error'], 'case_insensitive'),
        ]
        
        for patterns, test_name in patterns_tests:
            def search_test():
                searcher = LogSearcher(patterns=patterns)
                return list(searcher.search_file(test_file))
            
            results[test_name] = self.benchmark_function(search_test, runs=3)
            
        # Clean up
        os.unlink(test_file)
        return results

    def benchmark_file_sizes(self) -> Dict[str, Any]:
        """Benchmark performance across different file sizes."""
        print("📁 Benchmarking different file sizes...")
        
        results = {}
        
        for size in ['small', 'medium', 'large']:
            print(f"  Testing {size} file...")
            test_file = self.generate_test_data(size)
            
            def search_test():
                searcher = LogSearcher(patterns=['ERROR'])
                return list(searcher.search_file(test_file))
            
            benchmark_result = self.benchmark_function(search_test, runs=3)
            benchmark_result.update(self.test_data[size])
            
            # Calculate throughput
            lines_per_sec = self.test_data[size]['lines'] / benchmark_result['mean_time']
            mb_per_sec = self.test_data[size]['size_mb'] / benchmark_result['mean_time']
            
            benchmark_result['lines_per_second'] = lines_per_sec
            benchmark_result['mb_per_second'] = mb_per_sec
            
            results[size] = benchmark_result
            
            # Clean up
            os.unlink(test_file)
            
        return results

    def benchmark_context_lines(self) -> Dict[str, Any]:
        """Benchmark performance with different context line settings."""
        print("📋 Benchmarking context lines...")
        
        test_file = self.generate_test_data('medium')
        results = {}
        
        context_tests = [
            (0, 0, 0, 'no_context'),
            (3, 0, 0, 'after_context'),
            (0, 3, 0, 'before_context'),
            (0, 0, 3, 'around_context'),
            (5, 5, 0, 'large_context'),
        ]
        
        for after, before, context, test_name in context_tests:
            def search_test():
                searcher = LogSearcher(
                    patterns=['ERROR'],
                    after_context=after,
                    before_context=before,
                    context=context
                )
                return list(searcher.search_file(test_file))
            
            results[test_name] = self.benchmark_function(search_test, runs=3)
            
        # Clean up
        os.unlink(test_file)
        return results

    def benchmark_cli_overhead(self) -> Dict[str, Any]:
        """Benchmark CLI subprocess overhead vs direct API calls."""
        print("⚡ Benchmarking CLI overhead...")
        
        test_file = self.generate_test_data('medium')
        results = {}
        
        # Direct API call
        def direct_api():
            searcher = LogSearcher(patterns=['ERROR'])
            return list(searcher.search_file(test_file))
        
        results['direct_api'] = self.benchmark_function(direct_api, runs=5)
        
        # CLI subprocess call
        def cli_subprocess():
            result = subprocess.run(
                [sys.executable, '-m', 'loggrep.cli', 'ERROR', '--file', test_file],
                capture_output=True,
                text=True,
                cwd=os.path.join(os.path.dirname(__file__), '..')
            )
            return result.stdout.split('\n')
        
        results['cli_subprocess'] = self.benchmark_function(cli_subprocess, runs=5)
        
        # Calculate overhead
        overhead = results['cli_subprocess']['mean_time'] - results['direct_api']['mean_time']
        results['overhead_seconds'] = overhead
        results['overhead_percent'] = (overhead / results['direct_api']['mean_time']) * 100
        
        # Clean up
        os.unlink(test_file)
        return results

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all performance benchmarks."""
        print("🚀 Starting comprehensive performance benchmarks...\n")
        
        start_time = time.time()
        
        self.results = {
            'timestamp_parsing': self.benchmark_timestamp_parsing(),
            'pattern_matching': self.benchmark_pattern_matching(),
            'file_sizes': self.benchmark_file_sizes(),
            'context_lines': self.benchmark_context_lines(),
            'cli_overhead': self.benchmark_cli_overhead(),
        }
        
        total_time = time.time() - start_time
        self.results['benchmark_metadata'] = {
            'total_time': total_time,
            'timestamp': datetime.now().isoformat(),
            'python_version': sys.version,
            'platform': sys.platform,
        }
        
        return self.results

    def print_summary(self):
        """Print a summary of benchmark results."""
        print("\n" + "="*80)
        print("📊 PERFORMANCE BENCHMARK RESULTS")
        print("="*80)
        
        # File size performance
        print("\n🗂️  FILE SIZE PERFORMANCE:")
        for size, data in self.results['file_sizes'].items():
            print(f"  {size.upper()}: {data['lines']:,} lines ({data['size_mb']:.2f} MB)")
            print(f"    ⏱️  Time: {data['mean_time']:.3f}s (±{data['std_time']:.3f}s)")
            print(f"    🚀 Throughput: {data['lines_per_second']:,.0f} lines/sec, {data['mb_per_second']:.1f} MB/sec")
            print(f"    💾 Memory: {data['mean_memory_mb']:.1f} MB avg, {data['max_memory_mb']:.1f} MB peak")
            print()
            
        # Timestamp parsing
        print("🕒 TIMESTAMP PARSING:")
        ts_data = self.results['timestamp_parsing']
        print(f"    Detection: {ts_data['detection']['mean_time']*1000:.2f} ms per 6K timestamps")
        print(f"    Parsing: {ts_data['parsing']['mean_time']*1000:.2f} ms per 6K timestamps")
        print()
        
        # Pattern matching
        print("🔍 PATTERN MATCHING:")
        pm_data = self.results['pattern_matching']
        for test_name, data in pm_data.items():
            test_display = test_name.replace('_', ' ').title()
            print(f"    {test_display}: {data['mean_time']:.3f}s")
        print()
        
        # Context lines
        print("📋 CONTEXT LINES IMPACT:")
        ctx_data = self.results['context_lines']
        baseline = ctx_data['no_context']['mean_time']
        for test_name, data in ctx_data.items():
            if test_name != 'no_context':
                overhead = ((data['mean_time'] - baseline) / baseline) * 100
                test_display = test_name.replace('_', ' ').title()
                print(f"    {test_display}: +{overhead:.1f}% overhead")
        print()
        
        # CLI overhead
        print("⚡ CLI OVERHEAD:")
        cli_data = self.results['cli_overhead']
        print(f"    Direct API: {cli_data['direct_api']['mean_time']:.3f}s")
        print(f"    CLI Subprocess: {cli_data['cli_subprocess']['mean_time']:.3f}s")
        print(f"    Overhead: {cli_data['overhead_seconds']:.3f}s ({cli_data['overhead_percent']:.1f}%)")
        print()
        
        print("="*80)
        print(f"🏁 Benchmark completed in {self.results['benchmark_metadata']['total_time']:.1f} seconds")
        print("="*80)


def main():
    """Run the performance benchmark suite."""
    benchmark = PerformanceBenchmark()
    
    try:
        benchmark.run_all_benchmarks()
        benchmark.print_summary()
        
        # Save detailed results
        import json
        results_file = 'benchmark_results.json'
        with open(results_file, 'w') as f:
            json.dump(benchmark.results, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: {results_file}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Benchmark interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Benchmark failed: {e}")
        return 1
        
    return 0


if __name__ == '__main__':
    sys.exit(main())