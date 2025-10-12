#!/usr/bin/env python3
"""
Performance regression testing for Loggrep.

Compares current performance against expected benchmarks.
"""

import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scripts.benchmark import PerformanceBenchmark


def load_baseline_results():
    """Load baseline performance results if available."""
    baseline_file = 'benchmark_baseline.json'
    if os.path.exists(baseline_file):
        with open(baseline_file, 'r') as f:
            return json.load(f)
    return None


def save_current_as_baseline(results):
    """Save current results as baseline for future comparisons."""
    baseline_file = 'benchmark_baseline.json'
    with open(baseline_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"💾 Current results saved as baseline: {baseline_file}")


def compare_performance(current, baseline):
    """Compare current performance against baseline."""
    print("\n" + "="*80)
    print("📈 PERFORMANCE REGRESSION ANALYSIS")
    print("="*80)
    
    # Compare file size performance
    print("\n🗂️  FILE SIZE PERFORMANCE COMPARISON:")
    for size in ['small', 'medium', 'large']:
        if size in current['file_sizes'] and size in baseline['file_sizes']:
            curr = current['file_sizes'][size]
            base = baseline['file_sizes'][size]
            
            time_change = ((curr['mean_time'] - base['mean_time']) / base['mean_time']) * 100
            throughput_change = ((curr['lines_per_second'] - base['lines_per_second']) / base['lines_per_second']) * 100
            
            status = "🚀" if time_change < -5 else "⚠️" if time_change > 5 else "✅"
            print(f"  {size.upper()}: {status}")
            print(f"    Time: {curr['mean_time']:.3f}s vs {base['mean_time']:.3f}s ({time_change:+.1f}%)")
            print(f"    Throughput: {curr['lines_per_second']:,.0f} vs {base['lines_per_second']:,.0f} lines/sec ({throughput_change:+.1f}%)")
    
    # Compare timestamp parsing
    print("\n🕒 TIMESTAMP PARSING COMPARISON:")
    if 'timestamp_parsing' in current and 'timestamp_parsing' in baseline:
        curr_detect = current['timestamp_parsing']['detection']['mean_time']
        base_detect = baseline['timestamp_parsing']['detection']['mean_time']
        detect_change = ((curr_detect - base_detect) / base_detect) * 100
        
        curr_parse = current['timestamp_parsing']['parsing']['mean_time']
        base_parse = baseline['timestamp_parsing']['parsing']['mean_time']
        parse_change = ((curr_parse - base_parse) / base_parse) * 100
        
        detect_status = "🚀" if detect_change < -5 else "⚠️" if detect_change > 5 else "✅"
        parse_status = "🚀" if parse_change < -5 else "⚠️" if parse_change > 5 else "✅"
        
        print(f"    Detection: {detect_status} {curr_detect*1000:.2f}ms vs {base_detect*1000:.2f}ms ({detect_change:+.1f}%)")
        print(f"    Parsing: {parse_status} {curr_parse*1000:.2f}ms vs {base_parse*1000:.2f}ms ({parse_change:+.1f}%)")
    
    # Performance warnings
    print("\n⚠️  PERFORMANCE ALERTS:")
    alerts = []
    
    # Check for significant regressions
    for size in ['small', 'medium', 'large']:
        if size in current['file_sizes'] and size in baseline['file_sizes']:
            time_change = ((current['file_sizes'][size]['mean_time'] - baseline['file_sizes'][size]['mean_time']) / baseline['file_sizes'][size]['mean_time']) * 100
            if time_change > 10:
                alerts.append(f"❌ {size.upper()} file processing {time_change:.1f}% slower")
    
    if not alerts:
        print("    ✅ No performance regressions detected!")
    else:
        for alert in alerts:
            print(f"    {alert}")


def main():
    """Run performance regression testing."""
    print("🔍 Running Performance Regression Testing")
    print("="*60)
    
    # Run current benchmarks
    benchmark = PerformanceBenchmark()
    current_results = benchmark.run_all_benchmarks()
    
    # Load baseline if available
    baseline_results = load_baseline_results()
    
    if baseline_results:
        # Compare against baseline
        compare_performance(current_results, baseline_results)
    else:
        print("📊 No baseline found - saving current results as baseline")
        save_current_as_baseline(current_results)
        benchmark.print_summary()
    
    # Save current results
    with open('benchmark_results_latest.json', 'w') as f:
        json.dump(current_results, f, indent=2, default=str)
    
    # Performance targets check
    print("\n🎯 PERFORMANCE TARGETS:")
    large_file_perf = current_results['file_sizes']['large']
    target_throughput = 1000000  # 1M lines/sec target
    
    if large_file_perf['lines_per_second'] >= target_throughput:
        print(f"    ✅ Throughput target met: {large_file_perf['lines_per_second']:,.0f} >= {target_throughput:,} lines/sec")
    else:
        print(f"    ❌ Throughput below target: {large_file_perf['lines_per_second']:,.0f} < {target_throughput:,} lines/sec")
    
    # Memory target
    target_memory = 20  # 20MB max for 100K lines
    if large_file_perf['max_memory_mb'] <= target_memory:
        print(f"    ✅ Memory target met: {large_file_perf['max_memory_mb']:.1f} <= {target_memory} MB")
    else:
        print(f"    ❌ Memory above target: {large_file_perf['max_memory_mb']:.1f} > {target_memory} MB")


if __name__ == '__main__':
    main()