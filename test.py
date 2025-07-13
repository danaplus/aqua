#!/usr/bin/env python3
"""
Main test runner - runs from aqua directory
"""

import sys
import os
import subprocess


def main():
    """Run tests from main directory"""
    # Get script arguments
    if len(sys.argv) < 2:
        mode = "unit"
    else:
        mode = sys.argv[1]

    # Navigate to tests directory and run
    tests_dir = os.path.join(os.path.dirname(__file__), "tests")

    result = subprocess.run([
        sys.executable, "run_tests.py", mode
    ], cwd=tests_dir)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())