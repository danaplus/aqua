import requests
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APIClientError(Exception):
    """Custom exception for API client errors"""

    def __init__(self, message: str, status_code: int = None, response_data: Dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class UserAPIClient:
    """
    Python client for User Management API

    This client provides a simple interface for test automation engineers
    to interact with the User Management API server.
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        """
        Initialize the API client

        Args:
            base_url: Base URL of the API server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

        logger.info(f"UserAPIClient initialized with base_url: {self.base_url}")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with error handling

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional request parameters

        Returns:
            Response object

        Raises:
            APIClientError: If request fails
        """
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))

        try:
            logger.debug(f"Making {method} request to {url}")
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )

            # Log request details
            logger.debug(f"Request: {method} {url}")
            if 'json' in kwargs:
                logger.debug(f"Request body: {kwargs['json']}")

            # Log response details
            logger.debug(f"Response: {response.status_code} - {response.text[:200]}...")

            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise APIClientError(f"Request failed: {str(e)}")

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and extract data

        Args:
            response: Response object

        Returns:
            Response data as dictionary

        Raises:
            APIClientError: If response indicates error
        """
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {"message": response.text}

        if response.status_code >= 400:
            error_message = response_data.get('error', f'HTTP {response.status_code}')
            logger.error(f"API error: {error_message}")
            raise APIClientError(
                message=error_message,
                status_code=response.status_code,
                response_data=response_data
            )

        return response_data

    def create_user(self, user_id: str, name: str, phone: str, address: str) -> Dict[str, Any]:
        """
        Create a new user

        Args:
            user_id: Israeli ID (9 digits)
            name: User's full name
            phone: Phone number in international format
            address: User's address

        Returns:
            Created user data

        Raises:
            APIClientError: If creation fails

        Example:
            >>> client = UserAPIClient()
            >>> user = client.create_user("123456789", "John Doe", "+972-50-1234567", "Tel Aviv, Israel")
        """
        user_data = {
            "id": user_id,
            "name": name,
            "phone": phone,
            "address": address
        }

        logger.info(f"Creating user with ID: {user_id}")
        response = self._make_request('POST', '/users', json=user_data)
        result = self._handle_response(response)

        logger.info(f"Successfully created user: {user_id}")
        return result

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information by ID

        Args:
            user_id: User ID to retrieve

        Returns:
            User data

        Raises:
            APIClientError: If user not found or request fails

        Example:
            >>> client = UserAPIClient()
            >>> user = client.get_user("123456789")
        """
        logger.info(f"Fetching user with ID: {user_id}")
        response = self._make_request('GET', f'/users/{user_id}')
        result = self._handle_response(response)

        logger.info(f"Successfully retrieved user: {user_id}")
        return result

    def list_users(self) -> List[str]:
        """
        List all user IDs

        Returns:
            List of user IDs

        Raises:
            APIClientError: If request fails

        Example:
            >>> client = UserAPIClient()
            >>> user_ids = client.list_users()
        """
        logger.info("Fetching all user IDs")
        response = self._make_request('GET', '/users')
        result = self._handle_response(response)

        logger.info(f"Retrieved {len(result)} user IDs")
        return result

    def health_check(self) -> Dict[str, Any]:
        """
        Check API server health

        Returns:
            Health status information

        Raises:
            APIClientError: If health check fails

        Example:
            >>> client = UserAPIClient()
            >>> health = client.health_check()
        """
        logger.info("Performing health check")
        response = self._make_request('GET', '/health')
        result = self._handle_response(response)

        logger.info("Health check successful")
        return result

    def user_exists(self, user_id: str) -> bool:
        """
        Check if user exists

        Args:
            user_id: User ID to check

        Returns:
            True if user exists, False otherwise

        Example:
            >>> client = UserAPIClient()
            >>> exists = client.user_exists("123456789")
        """
        try:
            self.get_user(user_id)
            return True
        except APIClientError as e:
            if e.status_code == 404:
                return False
            elif e.status_code == 400:
                # Invalid ID format
                logger.warning(f"Invalid ID format: {user_id}")
                return False
            raise  # Re-raise if it's not a 404 or 400 error

    def delete_user(self, user_id: str) -> None:
        """
        Delete user by ID (if server supports it)
        Note: This endpoint doesn't exist in current server implementation
        """
        logger.warning("delete_user method is not implemented on server side")
        raise NotImplementedError("Server does not support user deletion")

    def clear_test_data(self) -> None:
        """
        Clear test data by trying to get all users and handle conflicts
        This is a workaround since the server doesn't have delete endpoints
        """
        logger.info("Note: Server doesn't support deletion. Use fresh database for clean tests.")
        user_ids = self.list_users()
        if user_ids:
            logger.info(f"Existing users in database: {user_ids}")
            logger.info("To start fresh, delete the users.db file and restart the server")

    def close(self):
        """Close the HTTP session"""
        self.session.close()
        logger.info("API client session closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Convenience functions for quick testing
def generate_valid_israeli_id(base_digits: str = "12345678") -> str:
    """
    Generate a valid Israeli ID by calculating the correct check digit

    Args:
        base_digits: First 8 digits of the ID

    Returns:
        Complete 9-digit Israeli ID with valid check digit
    """
    if len(base_digits) != 8 or not base_digits.isdigit():
        raise ValueError("base_digits must be exactly 8 digits")

    digits = [int(d) for d in base_digits]
    check_sum = 0

    for i, digit in enumerate(digits):
        if i % 2 == 0:  # Even position (0-indexed) - multiply by 1
            check_sum += digit
        else:  # Odd position - multiply by 2
            doubled = digit * 2
            # If result is two digits, add them together
            check_sum += doubled if doubled < 10 else (doubled // 10) + (doubled % 10)

    # Calculate check digit
    remainder = check_sum % 10
    check_digit = (10 - remainder) % 10

    return base_digits + str(check_digit)


def create_test_user(client: UserAPIClient, user_id: str = None) -> Dict[str, Any]:
    """
    Create a test user with predefined data

    Args:
        client: UserAPIClient instance
        user_id: Israeli ID for the test user (if None, generates valid one)

    Returns:
        Created user data
    """
    if user_id is None:
        user_id = generate_valid_israeli_id()

    return client.create_user(
        user_id=user_id,
        name="Test User",
        phone="+972-50-1234567",
        address="Test Address, Tel Aviv"
    )


def run_basic_test():
    """
    Run basic functionality test
    """
    print("Running basic API test...")

    with UserAPIClient() as client:
        try:
            # Health check
            health = client.health_check()
            print(f"✅ Health check: {health['status']}")

            # Generate unique test ID to avoid conflicts
            import time
            base_id = f"12345{int(time.time()) % 1000:03d}"  # Use timestamp for uniqueness
            test_id = generate_valid_israeli_id(base_id)
            print(f"Using test ID: {test_id}")

            # Create user
            user = client.create_user(
                user_id=test_id,
                name="Test User",
                phone="+972-50-1234567",
                address="Test Street 1, Tel Aviv"
            )
            print(f"✅ Created user: {user['name']}")

            # Get user
            retrieved_user = client.get_user(test_id)
            print(f"✅ Retrieved user: {retrieved_user['name']}")

            # List users
            user_ids = client.list_users()
            print(f"✅ Listed {len(user_ids)} users")

            # Check if user exists
            exists = client.user_exists(test_id)
            print(f"✅ User exists: {exists}")

            # Test duplicate creation (should fail)
            try:
                duplicate_user = client.create_user(
                    user_id=test_id,
                    name="Duplicate User",
                    phone="+972-50-9999999",
                    address="Another Address"
                )
                print("❌ Duplicate creation should have failed")
            except APIClientError as e:
                if e.status_code == 409:
                    print("✅ Duplicate creation properly rejected")
                else:
                    print(f"❌ Unexpected error for duplicate: {e}")

        except APIClientError as e:
            print(f"❌ Test failed: {e}")
            if e.status_code:
                print(f"   Status code: {e.status_code}")
            if e.response_data:
                print(f"   Response: {e.response_data}")


if __name__ == "__main__":
    run_basic_test()