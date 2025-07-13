#!/usr/bin/env python3
"""
Simplified tests for the User Management API
These tests use basic HTTP calls instead of FastAPI TestClient to avoid Windows issues
"""

import unittest
import requests
import time
import sys
import os

# Import our client
import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
from client import UserAPIClient, APIClientError, generate_valid_israeli_id


class TestSimpleAPI(unittest.TestCase):
    """Simple API tests using actual HTTP calls"""

    @classmethod
    def setUpClass(cls):
        """Check if server is running"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            cls.server_available = response.status_code == 200
        except requests.exceptions.RequestException:
            cls.server_available = False

    def setUp(self):
        """Setup for each test"""
        if not self.server_available:
            self.skipTest("Server not available at http://localhost:8000")

        # Generate unique test ID with microseconds for uniqueness
        import time
        import random
        timestamp = int(time.time() * 1000) % 10000  # Last 4 digits of milliseconds
        random_part = random.randint(10, 99)  # 2 random digits
        base_id = f"99{timestamp:04d}{random_part:02d}"  # Total 8 digits
        self.test_id = generate_valid_israeli_id(base_id)
        print(f"Generated test ID: {self.test_id}")  # Debug info

    def test_health_check_direct(self):
        """Test health check with direct HTTP call"""
        response = requests.get("http://localhost:8000/health", timeout=5)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["version"], "1.0.0")

    def test_create_user_direct(self):
        """Test user creation with direct HTTP call"""
        user_data = {
            "id": self.test_id,
            "name": "Test User",
            "phone": "+972-50-1234567",
            "address": "Test Address"
        }

        response = requests.post(
            "http://localhost:8000/users",
            json=user_data,
            timeout=5
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["id"], self.test_id)
        self.assertEqual(data["name"], "Test User")

    def test_get_user_direct(self):
        """Test user retrieval with direct HTTP call"""
        # First create a user (or use existing if duplicate)
        user_data = {
            "id": self.test_id,
            "name": "Get Test User",
            "phone": "+972-50-1234567",
            "address": "Test Address"
        }

        create_response = requests.post(
            "http://localhost:8000/users",
            json=user_data,
            timeout=5
        )

        # Accept both 201 (created) and 409 (already exists)
        if create_response.status_code == 409:
            print(f"User {self.test_id} already exists, using existing user for test")
        else:
            self.assertEqual(create_response.status_code, 201)

        # Then retrieve it
        get_response = requests.get(f"http://localhost:8000/users/{self.test_id}", timeout=5)
        self.assertEqual(get_response.status_code, 200)

        data = get_response.json()
        self.assertEqual(data["id"], self.test_id)

    def test_list_users_direct(self):
        """Test user listing with direct HTTP call"""
        response = requests.get("http://localhost:8000/users", timeout=5)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsInstance(data, list)

    def test_validation_error_direct(self):
        """Test validation error with direct HTTP call"""
        invalid_user_data = {
            "id": "invalid123",  # Invalid format
            "name": "Test User",
            "phone": "+972-50-1234567",
            "address": "Test Address"
        }

        response = requests.post(
            "http://localhost:8000/users",
            json=invalid_user_data,
            timeout=5
        )

        self.assertEqual(response.status_code, 422)

    def test_user_not_found_direct(self):
        """Test user not found with direct HTTP call"""
        # Use a valid ID that doesn't exist
        non_existent_id = generate_valid_israeli_id("00000000")

        response = requests.get(f"http://localhost:8000/users/{non_existent_id}", timeout=5)
        self.assertEqual(response.status_code, 404)


class TestClientLibrary(unittest.TestCase):
    """Test the client library"""

    def setUp(self):
        """Setup for each test"""
        # Check if server is available
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code != 200:
                self.skipTest("Server not available")
        except requests.exceptions.RequestException:
            self.skipTest("Server not available")

        self.client = UserAPIClient()

        # Generate unique test ID with higher precision
        import time
        import random
        timestamp = int(time.time() * 1000) % 10000  # Last 4 digits of milliseconds
        random_part = random.randint(10, 99)  # 2 random digits
        base_id = f"88{timestamp:04d}{random_part:02d}"  # Total 8 digits
        self.test_id = generate_valid_israeli_id(base_id)
        print(f"Generated test ID: {self.test_id}")  # Debug info

    def tearDown(self):
        """Cleanup"""
        self.client.close()

    def test_client_health_check(self):
        """Test client health check"""
        health = self.client.health_check()
        self.assertEqual(health["status"], "healthy")

    def test_client_create_user(self):
        """Test client user creation"""
        user = self.client.create_user(
            user_id=self.test_id,
            name="Client Test User",
            phone="+972-50-1234567",
            address="Client Test Address"
        )

        self.assertEqual(user["id"], self.test_id)
        self.assertEqual(user["name"], "Client Test User")

    def test_client_get_user(self):
        """Test client user retrieval"""
        # Create user first (handle if already exists)
        try:
            self.client.create_user(
                user_id=self.test_id,
                name="Get Client User",
                phone="+972-50-1234567",
                address="Test Address"
            )
        except APIClientError as e:
            if e.status_code == 409:
                print(f"User {self.test_id} already exists, using existing user for test")
            else:
                raise  # Re-raise if it's not a duplicate error

        # Then retrieve
        user = self.client.get_user(self.test_id)
        self.assertEqual(user["id"], self.test_id)

    def test_client_list_users(self):
        """Test client user listing"""
        users = self.client.list_users()
        self.assertIsInstance(users, list)

    def test_client_user_exists(self):
        """Test client user existence check"""
        # Create user (handle if already exists)
        try:
            self.client.create_user(
                user_id=self.test_id,
                name="Exists Test User",
                phone="+972-50-1234567",
                address="Test Address"
            )
        except APIClientError as e:
            if e.status_code == 409:
                print(f"User {self.test_id} already exists, using existing user for test")
            else:
                raise  # Re-raise if it's not a duplicate error

        # Check existence
        exists = self.client.user_exists(self.test_id)
        self.assertTrue(exists)

        # Check non-existence - use valid ID that doesn't exist
        non_existent_id = generate_valid_israeli_id("00000000")
        not_exists = self.client.user_exists(non_existent_id)
        self.assertFalse(not_exists)

    def test_client_error_handling(self):
        """Test client error handling"""
        # Test user not found - use valid ID that doesn't exist
        non_existent_id = generate_valid_israeli_id("00000000")

        with self.assertRaises(APIClientError) as context:
            self.client.get_user(non_existent_id)

        self.assertEqual(context.exception.status_code, 404)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""

    def test_israeli_id_generation(self):
        """Test Israeli ID generation"""
        # Test known cases
        result = generate_valid_israeli_id("12345678")
        self.assertEqual(result, "123456782")

        result = generate_valid_israeli_id("20345817")
        self.assertEqual(result, "203458179")

    def test_israeli_id_generation_errors(self):
        """Test Israeli ID generation error cases"""
        # Too short
        with self.assertRaises(ValueError):
            generate_valid_israeli_id("1234567")

        # Too long
        with self.assertRaises(ValueError):
            generate_valid_israeli_id("123456789")

        # Non-numeric
        with self.assertRaises(ValueError):
            generate_valid_israeli_id("1234567a")


def run_simple_tests():
    """Run simple tests with proper server check"""
    print("🧪 Running Simple Tests")
    print("=" * 50)

    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server is not responding correctly")
            print("   Please start the server with: python main.py")
            return False
    except requests.exceptions.RequestException:
        print("❌ Server is not running")
        print("   Please start the server with: python main.py")
        return False

    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSimpleAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestClientLibrary))
    suite.addTests(loader.loadTestsFromTestCase(TestUtilityFunctions))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All simple tests passed!")
        return True
    else:
        print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")
        return False


if __name__ == "__main__":
    import sys

    success = run_simple_tests()
    sys.exit(0 if success else 1)