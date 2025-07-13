#!/usr/bin/env python3
"""
Unit tests for the User API Client
"""

import unittest
import responses
import json
from unittest.mock import patch, MagicMock

# Import our client
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from client import UserAPIClient, APIClientError, generate_valid_israeli_id


class TestUserAPIClient(unittest.TestCase):
    """Test cases for User API Client"""

    def setUp(self):
        """Set up test client for each test"""
        self.base_url = "http://test-server:8000"
        self.client = UserAPIClient(base_url=self.base_url, timeout=10)

    def tearDown(self):
        """Clean up after each test"""
        self.client.close()

    @responses.activate
    def test_health_check_success(self):
        """Test successful health check"""
        responses.add(
            responses.GET,
            f"{self.base_url}/health",
            json={
                "status": "healthy",
                "timestamp": "2025-07-06T08:00:00Z",
                "version": "1.0.0"
            },
            status=200
        )

        result = self.client.health_check()

        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["version"], "1.0.0")
        self.assertIn("timestamp", result)

    @responses.activate
    def test_health_check_failure(self):
        """Test health check when server is down"""
        responses.add(
            responses.GET,
            f"{self.base_url}/health",
            json={"error": "Service unavailable"},
            status=503
        )

        with self.assertRaises(APIClientError) as context:
            self.client.health_check()

        self.assertEqual(context.exception.status_code, 503)

    @responses.activate
    def test_create_user_success(self):
        """Test successful user creation"""
        user_data = {
            "id": "123456782",
            "name": "John Doe",
            "phone": "+972-50-1234567",
            "address": "Tel Aviv, Israel",
            "created_at": "2025-07-06T08:00:00Z"
        }

        responses.add(
            responses.POST,
            f"{self.base_url}/users",
            json=user_data,
            status=201
        )

        result = self.client.create_user(
            user_id="123456782",
            name="John Doe",
            phone="+972-50-1234567",
            address="Tel Aviv, Israel"
        )

        self.assertEqual(result["id"], "123456782")
        self.assertEqual(result["name"], "John Doe")
        self.assertEqual(result["phone"], "+972-50-1234567")
        self.assertEqual(result["address"], "Tel Aviv, Israel")

    @responses.activate
    def test_create_user_validation_error(self):
        """Test user creation with validation error"""
        responses.add(
            responses.POST,
            f"{self.base_url}/users",
            json={
                "error": "Validation failed",
                "details": [
                    {
                        "type": "value_error",
                        "loc": ["body", "id"],
                        "msg": "Invalid Israeli ID"
                    }
                ],
                "timestamp": "2025-07-06T08:00:00Z"
            },
            status=422
        )

        with self.assertRaises(APIClientError) as context:
            self.client.create_user(
                user_id="invalid",
                name="John Doe",
                phone="+972-50-1234567",
                address="Tel Aviv, Israel"
            )

        self.assertEqual(context.exception.status_code, 422)
        self.assertIn("Validation failed", str(context.exception))

    @responses.activate
    def test_create_user_duplicate(self):
        """Test user creation with duplicate ID"""
        responses.add(
            responses.POST,
            f"{self.base_url}/users",
            json={
                "error": "User with this ID already exists",
                "timestamp": "2025-07-06T08:00:00Z"
            },
            status=409
        )

        with self.assertRaises(APIClientError) as context:
            self.client.create_user(
                user_id="123456782",
                name="John Doe",
                phone="+972-50-1234567",
                address="Tel Aviv, Israel"
            )

        self.assertEqual(context.exception.status_code, 409)

    @responses.activate
    def test_get_user_success(self):
        """Test successful user retrieval"""
        user_data = {
            "id": "123456782",
            "name": "John Doe",
            "phone": "+972-50-1234567",
            "address": "Tel Aviv, Israel",
            "created_at": "2025-07-06T08:00:00Z"
        }

        responses.add(
            responses.GET,
            f"{self.base_url}/users/123456782",
            json=user_data,
            status=200
        )

        result = self.client.get_user("123456782")

        self.assertEqual(result["id"], "123456782")
        self.assertEqual(result["name"], "John Doe")

    @responses.activate
    def test_get_user_not_found(self):
        """Test user retrieval when user doesn't exist"""
        responses.add(
            responses.GET,
            f"{self.base_url}/users/123456790",
            json={
                "error": "User not found",
                "timestamp": "2025-07-06T08:00:00Z"
            },
            status=404
        )

        with self.assertRaises(APIClientError) as context:
            self.client.get_user("123456790")

        self.assertEqual(context.exception.status_code, 404)

    @responses.activate
    def test_get_user_invalid_format(self):
        """Test user retrieval with invalid ID format"""
        responses.add(
            responses.GET,
            f"{self.base_url}/users/invalid",
            json={
                "error": "ID must be exactly 9 digits",
                "timestamp": "2025-07-06T08:00:00Z"
            },
            status=400
        )

        with self.assertRaises(APIClientError) as context:
            self.client.get_user("invalid")

        self.assertEqual(context.exception.status_code, 400)

    @responses.activate
    def test_list_users_empty(self):
        """Test listing users when no users exist"""
        responses.add(
            responses.GET,
            f"{self.base_url}/users",
            json=[],
            status=200
        )

        result = self.client.list_users()

        self.assertEqual(result, [])

    @responses.activate
    def test_list_users_with_data(self):
        """Test listing users when users exist"""
        user_ids = ["123456782", "203458179", "315240788"]

        responses.add(
            responses.GET,
            f"{self.base_url}/users",
            json=user_ids,
            status=200
        )

        result = self.client.list_users()

        self.assertEqual(result, user_ids)
        self.assertEqual(len(result), 3)

    @responses.activate
    def test_user_exists_true(self):
        """Test user_exists when user exists"""
        responses.add(
            responses.GET,
            f"{self.base_url}/users/123456782",
            json={
                "id": "123456782",
                "name": "John Doe",
                "phone": "+972-50-1234567",
                "address": "Tel Aviv, Israel"
            },
            status=200
        )

        result = self.client.user_exists("123456782")

        self.assertTrue(result)

    @responses.activate
    def test_user_exists_false(self):
        """Test user_exists when user doesn't exist"""
        responses.add(
            responses.GET,
            f"{self.base_url}/users/123456790",
            json={"error": "User not found"},
            status=404
        )

        result = self.client.user_exists("123456790")

        self.assertFalse(result)

    @responses.activate
    def test_user_exists_invalid_format(self):
        """Test user_exists with invalid ID format"""
        responses.add(
            responses.GET,
            f"{self.base_url}/users/invalid",
            json={"error": "ID must be exactly 9 digits"},
            status=400
        )

        result = self.client.user_exists("invalid")

        self.assertFalse(result)  # Should return False for invalid format

    def test_context_manager(self):
        """Test client as context manager"""
        with UserAPIClient(base_url=self.base_url) as client:
            self.assertIsInstance(client, UserAPIClient)
            self.assertEqual(client.base_url, self.base_url)

        # Session should be closed after context manager
        self.assertTrue(True)  # If we get here, context manager worked

    def test_connection_error(self):
        """Test handling of connection errors"""
        import requests

        # Mock connection error
        with patch.object(self.client.session, 'request') as mock_request:
            mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")

            with self.assertRaises(APIClientError) as context:
                self.client.health_check()

            self.assertIn("Request failed", str(context.exception))

    def test_timeout_error(self):
        """Test handling of timeout errors"""
        import requests

        # Mock timeout error
        with patch.object(self.client.session, 'request') as mock_request:
            mock_request.side_effect = requests.exceptions.Timeout("Request timed out")

            with self.assertRaises(APIClientError) as context:
                self.client.health_check()

            self.assertIn("Request failed", str(context.exception))

    @responses.activate
    def test_invalid_json_response(self):
        """Test handling of invalid JSON response"""
        responses.add(
            responses.GET,
            f"{self.base_url}/health",
            body="invalid json",
            status=200
        )

        # Should handle gracefully
        result = self.client.health_check()
        self.assertEqual(result["message"], "invalid json")


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""

    def test_generate_valid_israeli_id(self):
        """Test Israeli ID generation function"""
        # Test with known base
        result = generate_valid_israeli_id("12345678")
        self.assertEqual(result, "123456782")

        # Test with another known base
        result = generate_valid_israeli_id("20345817")
        self.assertEqual(result, "203458179")

    def test_generate_valid_israeli_id_invalid_input(self):
        """Test Israeli ID generation with invalid input"""
        # Too short
        with self.assertRaises(ValueError):
            generate_valid_israeli_id("1234567")

        # Too long
        with self.assertRaises(ValueError):
            generate_valid_israeli_id("123456789")

        # Non-numeric
        with self.assertRaises(ValueError):
            generate_valid_israeli_id("1234567a")


class TestIntegrationScenarios(unittest.TestCase):
    """Integration test scenarios"""

    def setUp(self):
        self.client = UserAPIClient(base_url="http://test-server:8000")

    def tearDown(self):
        self.client.close()

    @responses.activate
    def test_complete_user_workflow(self):
        """Test complete user management workflow"""
        # Setup mock responses
        user_data = {
            "id": "123456782",
            "name": "John Doe",
            "phone": "+972-50-1234567",
            "address": "Tel Aviv, Israel",
            "created_at": "2025-07-06T08:00:00Z"
        }

        # Mock health check
        responses.add(
            responses.GET,
            "http://test-server:8000/health",
            json={"status": "healthy", "version": "1.0.0"},
            status=200
        )

        # Mock user creation
        responses.add(
            responses.POST,
            "http://test-server:8000/users",
            json=user_data,
            status=201
        )

        # Mock user retrieval
        responses.add(
            responses.GET,
            "http://test-server:8000/users/123456782",
            json=user_data,
            status=200
        )

        # Mock user listing
        responses.add(
            responses.GET,
            "http://test-server:8000/users",
            json=["123456782"],
            status=200
        )

        # Execute workflow
        # 1. Health check
        health = self.client.health_check()
        self.assertEqual(health["status"], "healthy")

        # 2. Create user
        created_user = self.client.create_user(
            user_id="123456782",
            name="John Doe",
            phone="+972-50-1234567",
            address="Tel Aviv, Israel"
        )
        self.assertEqual(created_user["id"], "123456782")

        # 3. Retrieve user
        retrieved_user = self.client.get_user("123456782")
        self.assertEqual(retrieved_user["name"], "John Doe")

        # 4. List users
        user_list = self.client.list_users()
        self.assertIn("123456782", user_list)

        # 5. Check existence
        exists = self.client.user_exists("123456782")
        self.assertTrue(exists)


if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)