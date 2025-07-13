#!/usr/bin/env python3
"""
Integration tests for the complete User Management system
These tests require the server to be running
"""

import unittest
import time
import subprocess
import sys
import requests
from threading import Thread
import signal
import os

# Import our client
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from client import UserAPIClient, APIClientError, generate_valid_israeli_id


class TestLiveIntegration(unittest.TestCase):
    """Integration tests that run against live server"""

    @classmethod
    def setUpClass(cls):
        """Check if server is running, if not skip these tests"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                cls.server_available = True
                print("✅ Server is running - integration tests will run")
            else:
                cls.server_available = False
                print("⚠️ Server returned non-200 - skipping integration tests")
        except requests.exceptions.RequestException:
            cls.server_available = False
            print("⚠️ Server not available - skipping integration tests")
            print("   Start server with: python main.py")

    def setUp(self):
        """Set up test client"""
        if not self.server_available:
            self.skipTest("Server not available")

        self.client = UserAPIClient()

        # Generate unique test ID to avoid conflicts
        self.test_id = generate_valid_israeli_id(f"99988{int(time.time()) % 100:02d}")

    def tearDown(self):
        """Clean up"""
        if hasattr(self, 'client'):
            self.client.close()

    def test_server_health(self):
        """Test server health check"""
        health = self.client.health_check()

        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["version"], "1.0.0")
        self.assertIn("timestamp", health)

    def test_complete_user_lifecycle(self):
        """Test complete user lifecycle"""
        # 1. Verify user doesn't exist
        exists_before = self.client.user_exists(self.test_id)
        self.assertFalse(exists_before)

        # 2. Create user
        user_data = self.client.create_user(
            user_id=self.test_id,
            name="Integration Test User",
            phone="+972-50-9999999",
            address="Test Street 123, Tel Aviv"
        )

        self.assertEqual(user_data["id"], self.test_id)
        self.assertEqual(user_data["name"], "Integration Test User")
        self.assertIn("created_at", user_data)

        # 3. Verify user exists
        exists_after = self.client.user_exists(self.test_id)
        self.assertTrue(exists_after)

        # 4. Retrieve user
        retrieved_user = self.client.get_user(self.test_id)
        self.assertEqual(retrieved_user["id"], self.test_id)
        self.assertEqual(retrieved_user["name"], "Integration Test User")
        self.assertEqual(retrieved_user["phone"], "+972-50-9999999")

        # 5. List users (should include our user)
        user_list = self.client.list_users()
        self.assertIn(self.test_id, user_list)

        # 6. Try to create duplicate (should fail)
        with self.assertRaises(APIClientError) as context:
            self.client.create_user(
                user_id=self.test_id,
                name="Duplicate User",
                phone="+972-50-8888888",
                address="Another Address"
            )

        self.assertEqual(context.exception.status_code, 409)

    def test_validation_errors_live(self):
        """Test validation errors against live server"""
        # Invalid Israeli ID
        with self.assertRaises(APIClientError) as context:
            self.client.create_user(
                user_id="123456780",  # Wrong check digit
                name="Test User",
                phone="+972-50-1234567",
                address="Test Address"
            )
        self.assertEqual(context.exception.status_code, 422)

        # Invalid phone number
        with self.assertRaises(APIClientError) as context:
            self.client.create_user(
                user_id=self.test_id,
                name="Test User",
                phone="invalid-phone",
                address="Test Address"
            )
        self.assertEqual(context.exception.status_code, 422)

        # Empty name
        with self.assertRaises(APIClientError) as context:
            self.client.create_user(
                user_id=self.test_id,
                name="",
                phone="+972-50-1234567",
                address="Test Address"
            )
        self.assertEqual(context.exception.status_code, 422)

    def test_error_scenarios_live(self):
        """Test error scenarios against live server"""
        # User not found
        non_existent_id = generate_valid_israeli_id("00000000")

        with self.assertRaises(APIClientError) as context:
            self.client.get_user(non_existent_id)
        self.assertEqual(context.exception.status_code, 404)

        # Invalid ID format
        with self.assertRaises(APIClientError) as context:
            self.client.get_user("invalid123")
        self.assertEqual(context.exception.status_code, 400)

    def test_performance_benchmarks(self):
        """Test basic performance benchmarks"""
        # Health check performance
        start_time = time.time()
        self.client.health_check()
        health_time = time.time() - start_time

        # Should respond within reasonable time
        self.assertLess(health_time, 5.0, "Health check took too long")

        # User creation performance
        start_time = time.time()
        user = self.client.create_user(
            user_id=self.test_id,
            name="Performance Test User",
            phone="+972-50-7777777",
            address="Performance Test Address"
        )
        create_time = time.time() - start_time

        self.assertLess(create_time, 5.0, "User creation took too long")

        # User retrieval performance
        start_time = time.time()
        self.client.get_user(self.test_id)
        get_time = time.time() - start_time

        self.assertLess(get_time, 5.0, "User retrieval took too long")

    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import threading

        results = []
        errors = []

        def create_user_thread(thread_id):
            try:
                test_id = generate_valid_israeli_id(f"88877{thread_id:03d}")
                client = UserAPIClient()

                user = client.create_user(
                    user_id=test_id,
                    name=f"Concurrent User {thread_id}",
                    phone=f"+972-50-{thread_id:07d}",
                    address=f"Address {thread_id}"
                )
                results.append(user)
                client.close()

            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")

        # Create 5 concurrent threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_user_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0, f"Errors in concurrent requests: {errors}")
        self.assertEqual(len(results), 5, "Not all concurrent requests succeeded")

        # Verify all users have unique IDs
        ids = [user["id"] for user in results]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate IDs in concurrent creation")


class TestSystemResilience(unittest.TestCase):
    """Test system resilience and edge cases"""

    def setUp(self):
        """Check server availability"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code != 200:
                self.skipTest("Server not available")
        except requests.exceptions.RequestException:
            self.skipTest("Server not available")

        self.client = UserAPIClient()

    def tearDown(self):
        self.client.close()

    def test_large_data_handling(self):
        """Test handling of large data"""
        # Create user with very long name and address
        long_name = "A" * 1000  # 1000 character name
        long_address = "B" * 2000  # 2000 character address

        test_id = generate_valid_israeli_id(f"77766{int(time.time()) % 100:02d}")

        try:
            user = self.client.create_user(
                user_id=test_id,
                name=long_name,
                phone="+972-50-6666666",
                address=long_address
            )

            # Verify data was stored correctly
            retrieved = self.client.get_user(test_id)
            self.assertEqual(len(retrieved["name"]), 1000)
            self.assertEqual(len(retrieved["address"]), 2000)

        except APIClientError:
            # If server rejects large data, that's also acceptable
            pass

    def test_special_characters(self):
        """Test handling of special characters"""
        test_id = generate_valid_israeli_id(f"55544{int(time.time()) % 100:02d}")

        # Test with various special characters
        special_name = "José María O'Connor-Smith 中文 עברית"
        special_address = "123 Main St. 🏠 Apt #42, Tel Aviv-Yafo"

        user = self.client.create_user(
            user_id=test_id,
            name=special_name,
            phone="+972-50-5555555",
            address=special_address
        )

        # Verify special characters preserved
        retrieved = self.client.get_user(test_id)
        self.assertEqual(retrieved["name"], special_name)
        self.assertEqual(retrieved["address"], special_address)

    def test_boundary_conditions(self):
        """Test boundary conditions"""
        # Test with minimal valid data
        test_id = generate_valid_israeli_id(f"33322{int(time.time()) % 100:02d}")

        user = self.client.create_user(
            user_id=test_id,
            name="A",  # Single character name
            phone="+1",  # Minimal phone (if accepted)
            address="X"  # Single character address
        )

        retrieved = self.client.get_user(test_id)
        self.assertEqual(retrieved["name"], "A")
        self.assertEqual(retrieved["address"], "X")


def run_integration_tests():
    """Run integration tests with proper setup"""
    print("🚀 Starting Integration Tests")
    print("=" * 50)

    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server is not responding correctly")
            return False
    except requests.exceptions.RequestException:
        print("❌ Server is not running")
        print("   Please start the server with: python main.py")
        return False

    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestLiveIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemResilience))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All integration tests passed!")
        return True
    else:
        print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)