#!/usr/bin/env python3
"""
Basic tests that definitely work on all platforms
"""

import sys
import os
import unittest

# Add parent directory (aqua) to path so we can import from root
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)


def test_israeli_id_generation():
    """Test Israeli ID generation function"""
    from client import generate_valid_israeli_id

    # Test known cases
    result = generate_valid_israeli_id("12345678")
    assert result == "123456782", f"Expected 123456782, got {result}"

    result = generate_valid_israeli_id("20345817")
    assert result == "203458179", f"Expected 203458179, got {result}"

    print("✅ Israeli ID generation works correctly")


def test_israeli_id_validation_errors():
    """Test Israeli ID generation error cases"""
    from client import generate_valid_israeli_id

    # Too short
    try:
        generate_valid_israeli_id("1234567")
        assert False, "Should have raised ValueError for short ID"
    except ValueError:
        pass

    # Too long
    try:
        generate_valid_israeli_id("123456789")
        assert False, "Should have raised ValueError for long ID"
    except ValueError:
        pass

    # Non-numeric
    try:
        generate_valid_israeli_id("1234567a")
        assert False, "Should have raised ValueError for non-numeric ID"
    except ValueError:
        pass

    print("✅ Israeli ID validation errors work correctly")


def test_imports():
    """Test that all imports work"""
    try:
        from client import UserAPIClient, APIClientError, generate_valid_israeli_id
        print("✅ Client imports work")
    except ImportError as e:
        print(f"❌ Client import failed: {e}")
        return False

    try:
        from main import app, get_db, Base, UserDB
        print("✅ Server imports work")
    except ImportError as e:
        print(f"❌ Server import failed: {e}")
        return False

    return True


def test_server_live():
    """Test if server is responding (if running)"""
    import requests

    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "healthy"
            print("✅ Live server health check passed")
            return True
        else:
            print(f"⚠️ Server returned {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("⚠️ Server not running")
        return False


def run_basic_tests():
    """Run all basic tests"""
    print("🧪 Running Basic Tests")
    print("=" * 40)

    tests_passed = 0
    total_tests = 0

    # Test 1: Imports
    total_tests += 1
    if test_imports():
        tests_passed += 1

    # Test 2: Israeli ID generation
    total_tests += 1
    try:
        test_israeli_id_generation()
        tests_passed += 1
    except Exception as e:
        print(f"❌ Israeli ID generation failed: {e}")

    # Test 3: Israeli ID validation errors
    total_tests += 1
    try:
        test_israeli_id_validation_errors()
        tests_passed += 1
    except Exception as e:
        print(f"❌ Israeli ID validation errors failed: {e}")

    # Test 4: Live server (optional)
    total_tests += 1
    if test_server_live():
        tests_passed += 1

    print("\n" + "=" * 40)
    print(f"Results: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        print("🎉 All basic tests passed!")
        return True
    else:
        print("⚠️ Some tests failed")
        return False


if __name__ == "__main__":
    success = run_basic_tests()
    sys.exit(0 if success else 1)