#!/usr/bin/env python3
"""
Unit tests for the User Management API Server
"""

import unittest
import asyncio
import json
import tempfile
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Fix for Windows + Python 3.8 asyncio issue
if sys.platform == "win32" and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Import our application
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from main import app, get_db, Base, UserDB


class TestUserAPI(unittest.TestCase):
    """Test cases for User Management API"""

    @classmethod
    def setUpClass(cls):
        """Set up test database and client once for all tests"""
        # Create temporary database for testing
        cls.test_db_fd, cls.test_db_path = tempfile.mkstemp()

        # Create test database engine
        cls.test_engine = create_engine(
            f"sqlite:///{cls.test_db_path}",
            connect_args={"check_same_thread": False}
        )

        # Create tables
        Base.metadata.create_all(bind=cls.test_engine)

        # Create test session
        TestingSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=cls.test_engine
        )

        # Override dependency
        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

        # Create test client
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        # Close all connections first
        cls.test_engine.dispose()

        # Clear dependency overrides
        app.dependency_overrides.clear()

        # Clean up temp file
        try:
            os.close(cls.test_db_fd)
            os.unlink(cls.test_db_path)
        except (OSError, PermissionError):
            # File might be in use, skip cleanup
            pass

    def setUp(self):
        """Clear database before each test"""
        # Clear all users from test database
        try:
            with self.test_engine.connect() as conn:
                conn.execute(UserDB.__table__.delete())
                conn.commit()
        except Exception:
            # If there's an issue, recreate the tables
            Base.metadata.drop_all(bind=self.test_engine)
            Base.metadata.create_all(bind=self.test_engine)

    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["version"], "1.0.0")
        self.assertIn("timestamp", data)

    def test_create_user_valid(self):
        """Test creating user with valid data"""
        user_data = {
            "id": "123456782",  # Valid Israeli ID
            "name": "John Doe",
            "phone": "+972-50-1234567",
            "address": "Tel Aviv, Israel"
        }

        response = self.client.post("/users", json=user_data)

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["id"], user_data["id"])
        self.assertEqual(data["name"], user_data["name"])
        self.assertEqual(data["phone"], user_data["phone"])
        self.assertEqual(data["address"], user_data["address"])
        self.assertIn("created_at", data)

    def test_create_user_invalid_id(self):
        """Test creating user with invalid Israeli ID"""
        user_data = {
            "id": "123456780",  # Invalid check digit
            "name": "John Doe",
            "phone": "+972-50-1234567",
            "address": "Tel Aviv, Israel"
        }

        response = self.client.post("/users", json=user_data)

        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertEqual(data["error"], "Validation failed")
        self.assertIn("Invalid Israeli ID", str(data["details"]))

    def test_create_user_invalid_phone(self):
        """Test creating user with invalid phone number"""
        user_data = {
            "id": "123456782",
            "name": "John Doe",
            "phone": "invalid-phone",
            "address": "Tel Aviv, Israel"
        }

        response = self.client.post("/users", json=user_data)

        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertEqual(data["error"], "Validation failed")
        self.assertIn("Phone number", str(data["details"]))

    def test_create_user_missing_required_fields(self):
        """Test creating user with missing required fields"""
        test_cases = [
            # Missing name
            {
                "id": "123456782",
                "phone": "+972-50-1234567",
                "address": "Tel Aviv, Israel"
            },
            # Missing address
            {
                "id": "123456782",
                "name": "John Doe",
                "phone": "+972-50-1234567"
            },
            # Empty name
            {
                "id": "123456782",
                "name": "",
                "phone": "+972-50-1234567",
                "address": "Tel Aviv, Israel"
            }
        ]

        for user_data in test_cases:
            with self.subTest(user_data=user_data):
                response = self.client.post("/users", json=user_data)
                self.assertEqual(response.status_code, 422)

    def test_create_user_duplicate_id(self):
        """Test creating user with duplicate ID"""
        user_data = {
            "id": "123456782",
            "name": "John Doe",
            "phone": "+972-50-1234567",
            "address": "Tel Aviv, Israel"
        }

        # Create first user
        response1 = self.client.post("/users", json=user_data)
        self.assertEqual(response1.status_code, 201)

        # Try to create duplicate
        response2 = self.client.post("/users", json=user_data)
        self.assertEqual(response2.status_code, 409)
        data = response2.json()
        self.assertEqual(data["error"], "User with this ID already exists")

    def test_get_user_exists(self):
        """Test getting user that exists"""
        # Create user first
        user_data = {
            "id": "123456782",
            "name": "John Doe",
            "phone": "+972-50-1234567",
            "address": "Tel Aviv, Israel"
        }
        create_response = self.client.post("/users", json=user_data)
        self.assertEqual(create_response.status_code, 201)

        # Get user
        response = self.client.get("/users/123456782")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], user_data["id"])
        self.assertEqual(data["name"], user_data["name"])

    def test_get_user_not_exists(self):
        """Test getting user that doesn't exist"""
        response = self.client.get("/users/123456790")  # Valid format but doesn't exist

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["error"], "User not found")

    def test_get_user_invalid_format(self):
        """Test getting user with invalid ID format"""
        response = self.client.get("/users/invalid123")

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["error"], "ID must be exactly 9 digits")

    def test_list_users_empty(self):
        """Test listing users when database is empty"""
        response = self.client.get("/users")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, [])

    def test_list_users_with_data(self):
        """Test listing users when database has data"""
        # Create multiple users
        users = [
            {
                "id": "123456782",
                "name": "User One",
                "phone": "+972-50-1111111",
                "address": "Address 1"
            },
            {
                "id": "203458179",
                "name": "User Two",
                "phone": "+972-50-2222222",
                "address": "Address 2"
            }
        ]

        for user in users:
            response = self.client.post("/users", json=user)
            self.assertEqual(response.status_code, 201)

        # List users
        response = self.client.get("/users")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(len(data), 2)
        self.assertIn("123456782", data)
        self.assertIn("203458179", data)

    def test_israeli_id_validation_algorithm(self):
        """Test Israeli ID validation algorithm with known valid/invalid IDs"""
        test_cases = [
            # (ID, should_be_valid)
            ("123456782", True),  # Valid
            ("123456780", False),  # Invalid check digit
            ("203458179", True),  # Valid
            ("203458178", False),  # Invalid check digit
            ("12345678", False),  # Too short
            ("1234567890", False),  # Too long
            ("12345678a", False),  # Non-numeric
        ]

        for test_id, should_be_valid in test_cases:
            with self.subTest(id=test_id, should_be_valid=should_be_valid):
                user_data = {
                    "id": test_id,
                    "name": "Test User",
                    "phone": "+972-50-1234567",
                    "address": "Test Address"
                }

                response = self.client.post("/users", json=user_data)

                if should_be_valid:
                    self.assertEqual(response.status_code, 201,
                                     f"ID {test_id} should be valid but got {response.status_code}")
                else:
                    self.assertEqual(response.status_code, 422,
                                     f"ID {test_id} should be invalid but got {response.status_code}")

    def test_phone_number_validation(self):
        """Test phone number validation with various formats"""
        test_cases = [
            # (phone, should_be_valid)
            ("+972-50-1234567", True),
            ("+972501234567", True),
            ("+1-555-123-4567", True),
            ("+15551234567", True),
            ("972-50-1234567", False),  # Missing +
            ("invalid-phone", False),
            ("123456789", False),  # No country code
            ("+", False),  # Just +
            ("", False),  # Empty
        ]

        for phone, should_be_valid in test_cases:
            with self.subTest(phone=phone, should_be_valid=should_be_valid):
                user_data = {
                    "id": "123456782",
                    "name": "Test User",
                    "phone": phone,
                    "address": "Test Address"
                }

                response = self.client.post("/users", json=user_data)

                if should_be_valid:
                    self.assertEqual(response.status_code, 201,
                                     f"Phone {phone} should be valid but got {response.status_code}")
                    # Clean up for next test
                    self.setUp()
                else:
                    self.assertEqual(response.status_code, 422,
                                     f"Phone {phone} should be invalid but got {response.status_code}")


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        response = self.client.post(
            "/users",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        # Should return 422 for malformed JSON
        self.assertIn(response.status_code, [400, 422])

    def test_missing_content_type(self):
        """Test handling requests without proper content type"""
        response = self.client.post("/users", data="some data")

        # Should return 422 for missing/wrong content type
        self.assertIn(response.status_code, [400, 422])

    def test_method_not_allowed(self):
        """Test method not allowed scenarios"""
        # PUT on /users (not implemented)
        response = self.client.put("/users", json={})
        self.assertEqual(response.status_code, 405)

        # DELETE on /users (not implemented)
        response = self.client.delete("/users")
        self.assertEqual(response.status_code, 405)


if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)