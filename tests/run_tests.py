#!/usr/bin/env python3
"""
Test runner for loggrep.py

Usage:
    python3 run_tests.py                    # Run all tests
    python3 run_tests.py basic             # Run basic functionality tests
    python3 run_tests.py regex             # Run regex tests
    python3 run_tests.py case              # Run case-insensitive tests
    python3 run_tests.py invert            # Run invert match tests
    python3 run_tests.py context           # Run context lines tests
    python3 run_tests.py timestamp         # Run timestamp parsing tests
    python3 run_tests.py color             # Run color output tests
    python3 run_tests.py edge              # Run edge cases tests
    python3 run_tests.py integration       # Run integration tests
    python3 run_tests.py --help            # Show this help
"""

import subprocess
import sys


def run_tests(category=None):
    """Run tests with optional category filter."""
    cmd = ["python3", "-m", "pytest", "tests/test_loggrep.py", "-v"]

    if category:
        if category == "basic":
            cmd.extend(["-k", "TestBasicFunctionality"])
        elif category == "regex":
            cmd.extend(["-k", "TestRegexSupport"])
        elif category == "case":
            cmd.extend(["-k", "TestCaseInsensitive"])
        elif category == "invert":
            cmd.extend(["-k", "TestInvertMatch"])
        elif category == "context":
            cmd.extend(["-k", "TestContextLines"])
        elif category == "timestamp":
            cmd.extend(["-k", "TestTimestampParsing"])
        elif category == "color":
            cmd.extend(["-k", "TestColorOutput"])
        elif category == "edge":
            cmd.extend(["-k", "TestEdgeCases"])
        elif category == "integration":
            cmd.extend(["-k", "TestIntegrationScenarios"])
        else:
            print(f"Unknown category: {category}")
            print(__doc__)
            return 1

    return subprocess.call(cmd)


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h"]:
            print(__doc__)
            return 0
        category = sys.argv[1]
    else:
        category = None

    return run_tests(category)


if __name__ == "__main__":
    sys.exit(main())
