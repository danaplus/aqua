#!/usr/bin/env python3
"""
Example usage of the User API Client
This file demonstrates how test automation engineers can use the client
"""

from client import UserAPIClient, APIClientError, create_test_user
import logging

# Configure logging for examples
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_usage():
    """Basic usage example"""
    print("=== Basic Usage Example ===")

    # Create client instance
    client = UserAPIClient(base_url="http://localhost:8000")

    try:
        # Check server health
        health = client.health_check()
        print(f"Server status: {health['status']}")

        # Create a user
        user_data = client.create_user(
            user_id="123456782",  # Valid Israeli ID (correct check digit)
            name="Alice Johnson",
            phone="+972-50-1234567",
            address="Rothschild 1, Tel Aviv"
        )
        print(f"Created user: {user_data['name']}")

        # Retrieve the user
        retrieved_user = client.get_user("123456782")
        print(f"Retrieved user: {retrieved_user['name']}")

        # List all users
        user_ids = client.list_users()
        print(f"Total users: {len(user_ids)}")

    except APIClientError as e:
        print(f"Error: {e}")
    finally:
        client.close()


def example_context_manager():
    """Using context manager (recommended)"""
    print("\n=== Context Manager Example ===")

    with UserAPIClient() as client:
        try:
            # This will automatically close the session when done
            user = client.create_user(
                user_id="315240788",  # Valid Israeli ID
                name="Bob Smith",
                phone="+1-555-123-4567",
                address="Main St 123, New York"
            )
            print(f"Created user: {user['name']}")

        except APIClientError as e:
            print(f"Error: {e}")


def example_error_handling():
    """Error handling example"""
    print("\n=== Error Handling Example ===")

    with UserAPIClient() as client:
        try:
            # Try to get non-existent user (valid format but doesn't exist)
            user = client.get_user("123456790")  # Valid Israeli ID that doesn't exist

        except APIClientError as e:
            print(f"Caught expected error: {e}")
            print(f"Status code: {e.status_code}")

        # Check if user exists (safer approach)
        if client.user_exists("123456790"):
            print("User exists")
        else:
            print("User does not exist")

        # Test invalid ID format
        try:
            user = client.get_user("invalid123")
        except APIClientError as e:
            print(f"Invalid format error (expected): {e}")
            print(f"Status code: {e.status_code}")


def example_invalid_data():
    """Invalid data handling example"""
    print("\n=== Invalid Data Example ===")

    with UserAPIClient() as client:
        try:
            # Try to create user with invalid Israeli ID (wrong check digit)
            user = client.create_user(
                user_id="123456780",  # Invalid check digit - should be 2
                name="Invalid User",
                phone="+972-50-1234567",
                address="Some address"
            )

        except APIClientError as e:
            print(f"Validation error (expected): {e}")

        try:
            # Try to create user with invalid phone
            user = client.create_user(
                user_id="039065073",  # Valid ID
                name="Another User",
                phone="invalid-phone",
                address="Some address"
            )

        except APIClientError as e:
            print(f"Phone validation error (expected): {e}")


def example_automation_test_scenario():
    """Example automation test scenario"""
    print("\n=== Automation Test Scenario ===")

    with UserAPIClient() as client:
        # Test data - all with valid Israeli IDs
        test_users = [
            ("203458179", "User One", "+972-50-1111111", "Address 1"),
            ("315240788", "User Two", "+972-50-2222222", "Address 2"),
            ("039065073", "User Three", "+972-50-3333333", "Address 3"),
        ]

        created_users = []

        try:
            # Create multiple users
            for user_id, name, phone, address in test_users:
                user = client.create_user(user_id, name, phone, address)
                created_users.append(user_id)
                print(f"✅ Created: {name}")

            # Verify all users were created
            all_users = client.list_users()
            for user_id in created_users:
                assert user_id in all_users, f"User {user_id} not found in list"
            print(f"✅ All {len(created_users)} users verified")

            # Test duplicate creation (should fail)
            try:
                client.create_user(test_users[0][0], "Duplicate", "+972-50-9999999", "Duplicate Address")
                print("❌ Duplicate creation should have failed")
            except APIClientError as e:
                if e.status_code == 409:
                    print("✅ Duplicate creation properly rejected")
                else:
                    print(f"❌ Unexpected error: {e}")

            print("✅ Automation test scenario completed successfully")

        except APIClientError as e:
            print(f"❌ Test failed: {e}")
        except AssertionError as e:
            print(f"❌ Assertion failed: {e}")


def example_performance_test():
    """Simple performance test example"""
    print("\n=== Performance Test Example ===")

    import time

    with UserAPIClient() as client:
        # Test response time
        start_time = time.time()

        try:
            health = client.health_check()
            response_time = time.time() - start_time
            print(f"Health check response time: {response_time:.3f}s")

            if response_time < 1.0:
                print("✅ Response time acceptable")
            else:
                print("⚠️ Response time high")

        except APIClientError as e:
            print(f"❌ Performance test failed: {e}")


if __name__ == "__main__":
    print("User API Client - Example Usage")
    print("=" * 50)

    # Run all examples
    example_basic_usage()
    example_context_manager()
    example_error_handling()
    example_invalid_data()
    example_automation_test_scenario()
    example_performance_test()

    print("\n" + "=" * 50)
    print("Examples completed!")
    print("Make sure the server is running on http://localhost:8000")