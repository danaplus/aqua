#!/usr/bin/env python3
"""
Integration tests using pytest (modern approach)
"""

import pytest
import requests
import time
import threading
import sys
import os

# Import our client
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
from client import UserAPIClient, APIClientError, generate_valid_israeli_id


# Fixtures
@pytest.fixture(scope="session")
def server_check():
    """Check if server is available once per test session"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            pytest.skip("Server not available")
    except requests.exceptions.RequestException:
        pytest.skip("Server not available - start with: python main.py")


@pytest.fixture
def api_client(server_check):
    """Create API client for each test"""
    client = UserAPIClient()
    yield client
    client.close()


@pytest.fixture
def unique_user_id():
    """Generate unique test user ID"""
    import random
    timestamp = int(time.time() * 1000) % 10000
    random_part = random.randint(10, 99)
    base_id = f"99{timestamp:04d}{random_part:02d}"
    return generate_valid_israeli_id(base_id)


@pytest.fixture
def test_user_data():
    """Common test user data"""
    return {
        "name": "Integration Test User",
        "phone": "+972-50-9999999",
        "address": "Test Street 123, Tel Aviv"
    }


# Basic Integration Tests
class TestBasicIntegration:
    """Basic integration tests"""

    def test_server_health(self, api_client):
        """Test server health check"""
        health = api_client.health_check()
        assert health["status"] == "healthy"
        assert health["version"] == "1.0.0"
        assert "timestamp" in health

    def test_user_lifecycle(self, api_client, unique_user_id, test_user_data):
        """Test complete user lifecycle"""
        # 1. Verify user doesn't exist
        assert not api_client.user_exists(unique_user_id)

        # 2. Create user
        user = api_client.create_user(
            user_id=unique_user_id,
            **test_user_data
        )
        assert user["id"] == unique_user_id
        assert user["name"] == test_user_data["name"]

        # 3. Verify user exists
        assert api_client.user_exists(unique_user_id)

        # 4. Retrieve user
        retrieved_user = api_client.get_user(unique_user_id)
        assert retrieved_user["id"] == unique_user_id
        assert retrieved_user["name"] == test_user_data["name"]

        # 5. List users should include our user
        user_list = api_client.list_users()
        assert unique_user_id in user_list

    def test_duplicate_user_prevention(self, api_client, unique_user_id, test_user_data):
        """Test duplicate user prevention"""
        # Create user
        api_client.create_user(user_id=unique_user_id, **test_user_data)

        # Try to create duplicate
        with pytest.raises(APIClientError) as exc_info:
            api_client.create_user(user_id=unique_user_id, **test_user_data)

        assert exc_info.value.status_code == 409


# Validation Tests
class TestValidation:
    """Test validation scenarios"""

    @pytest.mark.parametrize("invalid_id,expected_status", [
        ("12345678", 422),  # Wrong check digit
        ("1234567", 422),  # Too short
        ("123456789", 422),  # Too long (but maybe valid)
        ("12345678a", 422),  # Non-numeric
    ])
    def test_invalid_israeli_ids(self, api_client, invalid_id, expected_status, test_user_data):
        """Test various invalid Israeli IDs"""
        with pytest.raises(APIClientError) as exc_info:
            api_client.create_user(user_id=invalid_id, **test_user_data)

        assert exc_info.value.status_code == expected_status

    @pytest.mark.parametrize("invalid_phone", [
        "invalid-phone",
        "123456789",
        "+",
        "",
        "972-50-1234567",  # Missing +
    ])
    def test_invalid_phone_numbers(self, api_client, unique_user_id, invalid_phone):
        """Test various invalid phone numbers"""
        with pytest.raises(APIClientError) as exc_info:
            api_client.create_user(
                user_id=unique_user_id,
                name="Test User",
                phone=invalid_phone,
                address="Test Address"
            )

        assert exc_info.value.status_code == 422

    @pytest.mark.parametrize("missing_field", ["name", "address"])
    def test_missing_required_fields(self, api_client, unique_user_id, missing_field):
        """Test missing required fields"""
        user_data = {
            "name": "Test User",
            "phone": "+972-50-1234567",
            "address": "Test Address"
        }
        del user_data[missing_field]

        with pytest.raises(APIClientError) as exc_info:
            api_client.create_user(user_id=unique_user_id, **user_data)

        assert exc_info.value.status_code == 422


# Error Handling Tests
class TestErrorHandling:
    """Test error handling scenarios"""

    def test_user_not_found(self, api_client):
        """Test 404 for non-existent user"""
        non_existent_id = generate_valid_israeli_id("00000000")

        with pytest.raises(APIClientError) as exc_info:
            api_client.get_user(non_existent_id)

        assert exc_info.value.status_code == 404

    def test_invalid_id_format_in_get(self, api_client):
        """Test 400 for invalid ID format in GET"""
        with pytest.raises(APIClientError) as exc_info:
            api_client.get_user("invalid123")

        assert exc_info.value.status_code == 400


# Performance Tests
class TestPerformance:
    """Basic performance tests"""

    def test_response_times(self, api_client):
        """Test basic response time requirements"""
        # Health check performance
        start_time = time.time()
        api_client.health_check()
        health_time = time.time() - start_time
        assert health_time < 5.0, f"Health check too slow: {health_time:.2f}s"

        # User listing performance
        start_time = time.time()
        api_client.list_users()
        list_time = time.time() - start_time
        assert list_time < 5.0, f"User listing too slow: {list_time:.2f}s"

    def test_concurrent_requests(self, unique_user_id):
        """Test handling of concurrent requests"""
        results = []
        errors = []

        def create_user_thread(thread_id):
            try:
                timestamp = int(time.time() * 1000) % 1000
                base_id = f"888{timestamp:03d}{thread_id:02d}"
                test_id = generate_valid_israeli_id(base_id)

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

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0, f"Errors in concurrent requests: {errors}"
        assert len(results) == 5, "Not all concurrent requests succeeded"

        # Verify unique IDs
        ids = [user["id"] for user in results]
        assert len(ids) == len(set(ids)), "Duplicate IDs in concurrent creation"


# Edge Cases
class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_special_characters(self, api_client, unique_user_id):
        """Test handling of special characters"""
        special_name = "José María O'Connor-Smith 中文 עברית"
        special_address = "123 Main St. 🏠 Apt #42, Tel Aviv-Yafo"

        user = api_client.create_user(
            user_id=unique_user_id,
            name=special_name,
            phone="+972-50-5555555",
            address=special_address
        )

        # Verify special characters preserved
        retrieved = api_client.get_user(unique_user_id)
        assert retrieved["name"] == special_name
        assert retrieved["address"] == special_address

    def test_boundary_data_sizes(self, api_client, unique_user_id):
        """Test boundary conditions for data sizes"""
        # Test minimal valid data
        user = api_client.create_user(
            user_id=unique_user_id,
            name="A",  # Single character
            phone="+1",  # Minimal phone (if accepted)
            address="X"  # Single character
        )

        retrieved = api_client.get_user(unique_user_id)
        assert retrieved["name"] == "A"
        assert retrieved["address"] == "X"


# Custom markers for test organization
pytestmark = pytest.mark.integration