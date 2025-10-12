#!/usr/bin/env python3
"""
Profiling script for Loggrep to identify performance bottlenecks.

Uses cProfile and line_profiler to analyze where time is spent.
"""

import cProfile
import pstats
import tempfile
import os
import sys
from datetime import datetime
import io

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from loggrep.core import LogSearcher


def generate_large_log_file(num_lines: int = 100000) -> str:
    """Generate a large log file for profiling."""
    log_templates = [
        "Oct 12 14:30:{:02d} server1 INFO: Processing request #{}",
        "2025-10-12T14:30:{:02d}.123Z ERROR: Connection failed to database server {}",
        "10-12 14:30:{:02d}.456  1234  5678 W MyApp: Warning in module {} - performance degraded",
        "2025/10/12 14:30:{:02d} [DEBUG] Cache hit ratio: {}%",
        "12/Oct/2025:14:30:{:02d} +0000 \"GET /api/users/{} HTTP/1.1\" 200",
        "05.10.2025 14:30:{:02d}.789 FATAL: Critical error in subsystem {} - immediate attention required",
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        for i in range(num_lines):
            template = log_templates[i % len(log_templates)]
            second = i % 60
            f.write(template.format(second, i) + '\n')
        return f.name


def profile_search_operation():
    """Profile a typical search operation."""
    print("🔍 Generating test data...")
    log_file = generate_large_log_file(100000)
    
    def search_operation():
        """The operation we want to profile."""
        searcher = LogSearcher(
            patterns=['ERROR', 'FATAL'],
            ignore_case=False,
            invert_match=False,
            after_context=2,
            before_context=1,
            use_color=False
        )
        
        results = list(searcher.search_file(log_file))
        return len(results)
    
    try:
        print("📊 Running cProfile analysis...")
        
        # Profile with cProfile
        profiler = cProfile.Profile()
        profiler.enable()
        
        result_count = search_operation()
        
        profiler.disable()
        
        # Create string buffer for stats
        stats_buffer = io.StringIO()
        stats = pstats.Stats(profiler, stream=stats_buffer)
        
        print(f"✅ Found {result_count} matching lines")
        print("\n" + "="*80)
        print("🔥 TOP PERFORMANCE BOTTLENECKS")
        print("="*80)
        
        # Show top time consumers
        stats.sort_stats('cumulative')
        stats.print_stats(20)
        
        # Show functions called most often
        print("\n" + "="*80)
        print("📞 MOST FREQUENTLY CALLED FUNCTIONS")
        print("="*80)
        stats.sort_stats('calls')
        stats.print_stats(15)
        
        # Save detailed profile
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_file = f"profile_results_{timestamp}.prof"
        profiler.dump_stats(profile_file)
        print(f"\n💾 Detailed profile saved to: {profile_file}")
        print("   View with: python -m pstats", profile_file)
        
        return stats_buffer.getvalue()
        
    finally:
        # Clean up
        os.unlink(log_file)


def profile_timestamp_parsing():
    """Profile timestamp parsing specifically."""
    print("\n🕒 Profiling timestamp parsing...")
    
    from loggrep.timestamps import detect_timestamp_format, parse_timestamp
    
    test_lines = [
        "Oct 12 14:30:45 server1 ERROR: Connection failed",
        "2025-10-12T14:30:45.123Z INFO: Processing request",
        "10-12 14:30:45.456  1234  5678 E MyApp: Error occurred",
        "2025/10/12 14:30:45 [ERROR] Failed to parse config",
        "12/Oct/2025:14:30:45 +0000 \"GET /api HTTP/1.1\" 500",
    ] * 10000  # 50K lines
    
    def timestamp_operations():
        """Profile timestamp detection and parsing."""
        detections = 0
        parses = 0
        
        for line in test_lines:
            # Detect timestamp
            ts_str = detect_timestamp_format(line)
            if ts_str:
                detections += 1
                # Parse timestamp
                parsed = parse_timestamp(ts_str)
                if parsed:
                    parses += 1
                    
        return detections, parses
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    detections, parses = timestamp_operations()
    
    profiler.disable()
    
    print(f"✅ Detected {detections} timestamps, parsed {parses}")
    
    # Show timestamp-specific stats
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    
    print("\n📊 Timestamp parsing performance:")
    stats.print_stats('timestamps', 10)
    stats.print_stats('parse', 10)


def analyze_memory_usage():
    """Analyze memory usage patterns."""
    print("\n💾 Analyzing memory usage...")
    
    try:
        import psutil
        import tracemalloc
        
        # Start memory tracing
        tracemalloc.start()
        
        log_file = generate_large_log_file(50000)
        
        # Measure initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        searcher = LogSearcher(patterns=['ERROR'])
        results = list(searcher.search_file(log_file))
        
        # Measure final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Get memory trace
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"📈 Memory analysis:")
        print(f"   Initial: {initial_memory:.1f} MB")
        print(f"   Final: {final_memory:.1f} MB")
        print(f"   Peak usage: {peak / 1024 / 1024:.1f} MB")
        print(f"   Current usage: {current / 1024 / 1024:.1f} MB")
        print(f"   Results found: {len(results)}")
        
        # Clean up
        os.unlink(log_file)
        
    except ImportError:
        print("⚠️  psutil not available for memory analysis")


def main():
    """Run comprehensive profiling analysis."""
    print("🚀 Starting Loggrep Performance Profiling")
    print("="*60)
    
    try:
        # Profile main search operation
        profile_search_operation()
        
        # Profile timestamp parsing
        profile_timestamp_parsing()
        
        # Analyze memory usage
        analyze_memory_usage()
        
        print("\n✨ Profiling complete!")
        print("\n💡 Performance optimization suggestions:")
        print("   1. Check the top time-consuming functions")
        print("   2. Look for repeated function calls that could be cached")
        print("   3. Consider optimizing regex compilation")
        print("   4. Review timestamp parsing efficiency")
        
    except KeyboardInterrupt:
        print("\n⏹️  Profiling interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Profiling failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0


if __name__ == '__main__':
    sys.exit(main())