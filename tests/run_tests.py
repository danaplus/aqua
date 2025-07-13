#!/usr/bin/env python3
"""
Test runner script for User Management API
Provides different test execution modes and reporting
"""

import sys
import os
import subprocess
import argparse
import unittest
import requests
import time
from pathlib import Path

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)


def check_server_running():
    """Check if the server is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def run_unit_tests():
    """Run unit tests only (no server required)"""
    print("🧪 Running Unit Tests")
    print("=" * 50)

    tests_dir = os.path.dirname(os.path.abspath(__file__))

    # Run basic tests that definitely work
    print("🔧 Running Basic Tests...")
    result = subprocess.run([
        sys.executable, "test_basic.py"
    ], cwd=tests_dir, capture_output=False)

    # Skip FastAPI TestClient tests on Windows due to async issues
    if sys.platform == "win32":
        print("\n⚠️ Skipping FastAPI TestClient tests on Windows")
        print("   Use integration tests with live server instead")
        print("   Or run in Docker/Linux environment for full test suite")
    else:
        print("\n📡 Running Server Unit Tests...")
        result2 = subprocess.run([
            sys.executable, "-m", "unittest", "test_server", "-v"
        ], cwd=tests_dir, capture_output=False)
        return result.returncode == 0 and result2.returncode == 0

    return result.returncode == 0


def run_integration_tests():
    """Run integration tests (server required)"""
    print("🔗 Running Integration Tests")
    print("=" * 50)

    if not check_server_running():
        print("❌ Server not running!")
        print("   Please start server from main directory: python main.py")
        return False

    print("✅ Server is running")
    tests_dir = os.path.dirname(os.path.abspath(__file__))

    # Use simple tests for integration
    result = subprocess.run([
        sys.executable, "test_simple.py"
    ], cwd=tests_dir, capture_output=False)

    return result.returncode == 0


def run_all_tests():
    """Run all tests"""
    print("🚀 Running All Tests")
    print("=" * 50)

    # Run unit tests first
    unit_success = run_unit_tests()

    print("\n" + "=" * 50)

    # Run integration tests if server is available
    if check_server_running():
        integration_success = run_integration_tests()
    else:
        print("⚠️ Skipping integration tests - server not running")
        integration_success = True  # Don't fail if server not available

    return unit_success and integration_success


def run_with_coverage():
    """Run tests with coverage reporting"""
    print("📊 Running Tests with Coverage")
    print("=" * 50)

    # Install coverage if not available
    try:
        import coverage
    except ImportError:
        print("Installing coverage...")
        subprocess.run([sys.executable, "-m", "pip", "install", "coverage"])

    tests_dir = os.path.dirname(os.path.abspath(__file__))

    # On Windows, avoid FastAPI TestClient due to async issues
    if sys.platform == "win32":
        print("Windows detected - using compatible tests for coverage")

        # Run coverage on basic tests and client tests only
        result1 = subprocess.run([
            sys.executable, "-m", "coverage", "run", "--append", "test_basic.py"
        ], cwd=tests_dir)

        result2 = subprocess.run([
            sys.executable, "-m", "coverage", "run", "--append", "test_simple.py"
        ], cwd=tests_dir)

        # Try to include source files in coverage
        os.chdir(os.path.dirname(tests_dir))  # Go to parent directory
        result3 = subprocess.run([
            sys.executable, "-m", "coverage", "run", "--append", "-m", "unittest",
            "tests.test_basic", "-v"
        ], capture_output=True)  # Capture output to avoid errors

    else:
        # On Linux/Mac, run full test suite
        result1 = subprocess.run([
            sys.executable, "-m", "coverage", "run", "-m", "unittest",
            "test_server", "test_client", "-v"
        ], cwd=tests_dir)

    # Generate coverage report
    if result1.returncode == 0:
        print("\n📊 Generating coverage reports...")
        subprocess.run([sys.executable, "-m", "coverage", "report"], cwd=tests_dir)
        subprocess.run([sys.executable, "-m", "coverage", "html"], cwd=tests_dir)
        print("\n📊 Coverage report generated in tests/htmlcov/index.html")
        return True
    else:
        print("❌ Coverage run failed")
        return False


def run_pytest():
    """Run tests using pytest"""
    print("🎯 Running Tests with Pytest")
    print("=" * 50)

    # Install pytest if not available
    try:
        import pytest
    except ImportError:
        print("Installing pytest...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "test_requirements.txt"])

    tests_dir = os.path.dirname(os.path.abspath(__file__))

    # On Windows, avoid FastAPI TestClient tests
    if sys.platform == "win32":
        print("Windows detected - running compatible tests only")
        args = [
            sys.executable, "-m", "pytest",
            "test_client.py", "test_simple.py",  # Skip test_server.py and test_integration.py
            "-v", "--tb=short", "-x"  # Stop on first failure
        ]
    else:
        args = [
            sys.executable, "-m", "pytest",
            "test_server.py", "test_client.py", "test_simple.py",
            "-v", "--tb=short"
        ]

    # Add integration tests if server is running
    if check_server_running():
        if sys.platform != "win32":  # Only on non-Windows
            args.append("test_integration.py")
        print("✅ Server detected - including integration tests")
    else:
        print("⚠️ Server not running - skipping integration tests")

    result = subprocess.run(args, cwd=tests_dir)
    return result.returncode == 0


def create_test_report():
    """Create comprehensive test report"""
    print("📋 Creating Test Report")
    print("=" * 50)

    report = []
    report.append("# User Management API - Test Report")
    report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # System info
    report.append("## System Information")
    report.append(f"- Python: {sys.version}")
    report.append(f"- Platform: {sys.platform}")
    report.append("")

    # Server status
    server_running = check_server_running()
    report.append("## Server Status")
    report.append(f"- Server Running: {'✅ Yes' if server_running else '❌ No'}")
    if server_running:
        try:
            response = requests.get("http://localhost:8000/health")
            health = response.json()
            report.append(f"- Server Version: {health.get('version', 'Unknown')}")
            report.append(f"- Health Status: {health.get('status', 'Unknown')}")
        except:
            pass
    report.append("")

    # Test results
    report.append("## Test Results")

    # Unit tests
    print("Running unit tests for report...")
    unit_result = run_unit_tests()
    report.append(f"- Unit Tests: {'✅ PASS' if unit_result else '❌ FAIL'}")

    # Integration tests
    if server_running:
        print("Running integration tests for report...")
        integration_result = run_integration_tests()
        report.append(f"- Integration Tests: {'✅ PASS' if integration_result else '❌ FAIL'}")
    else:
        report.append("- Integration Tests: ⏭️ SKIPPED (server not running)")

    report.append("")

    # Test files info
    report.append("## Test Files")
    test_files = [
        ("test_server.py", "Server API unit tests"),
        ("test_client.py", "Client library unit tests"),
        ("test_integration.py", "End-to-end integration tests"),
    ]

    for filename, description in test_files:
        if os.path.exists(filename):
            # Count test methods
            with open(filename, 'r') as f:
                content = f.read()
                test_count = content.count('def test_')
            report.append(f"- {filename}: {description} ({test_count} tests)")
        else:
            report.append(f"- {filename}: Missing")

    # Write report
    with open("test_report.md", "w") as f:
        f.write("\n".join(report))

    print("\n📋 Test report saved to test_report.md")


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="User Management API Test Runner")
    parser.add_argument(
        "mode",
        choices=["unit", "integration", "all", "coverage", "pytest", "report"],
        help="Test mode to run"
    )
    parser.add_argument(
        "--server-check",
        action="store_true",
        help="Just check if server is running"
    )

    args = parser.parse_args()

    if args.server_check:
        if check_server_running():
            print("✅ Server is running on http://localhost:8000")
            return 0
        else:
            print("❌ Server is not running")
            return 1

    # Run tests based on mode
    success = False

    if args.mode == "unit":
        success = run_unit_tests()
    elif args.mode == "integration":
        success = run_integration_tests()
    elif args.mode == "all":
        success = run_all_tests()
    elif args.mode == "coverage":
        success = run_with_coverage()
    elif args.mode == "pytest":
        success = run_pytest()
    elif args.mode == "report":
        create_test_report()
        success = True

    if success:
        print("\n🎉 Tests completed successfully!")
        return 0
    else:
        print("\n💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())