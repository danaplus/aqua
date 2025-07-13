# User Management API - Automation Infrastructure

A RESTful API server and Python client for user management with Israeli ID validation, designed for automation testing infrastructure.

## 🎯 Overview

This project provides:
- **FastAPI REST Server** - Production-ready API with Israeli ID validation
- **Python Client** - Simple interface for test automation engineers
- **Docker Support** - Containerized deployment
- **Comprehensive Validation** - Israeli ID, phone numbers, required fields
- **Structured Logging** - Request/response tracking and error handling

## 📁 Project Structure

```
├── main.py                 # FastAPI server
├── client.py              # Python API client
├── example_usage.py       # Usage examples and demos
├── requirements.txt       # Server dependencies
├── Dockerfile             # Server containerization
├── docker-compose.yml     # Complete deployment setup
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- Docker (optional, for containerized deployment)

### 1. Setup & Installation

```bash
# Clone/download the project
cd aqua

# Install server dependencies
pip install -r requirements.txt


```

### 2. Run the Server

```bash
# Start the server
python main.py
```

Server will be available at: http://localhost:8000

**API Documentation**: http://localhost:8000/docs (Swagger UI)

### 3. Test the Client

```bash
# Basic functionality test
python client.py

# Comprehensive examples
python example_usage.py


```

## 🏗️ Architecture & Design Decisions

### Framework Choice: FastAPI
- **Modern & Fast**: Async support, automatic API documentation
- **Type Safety**: Pydantic models with automatic validation
- **Standards Compliant**: OpenAPI, JSON Schema
- **Developer Experience**: Auto-generated docs, clear error messages

### Database: SQLite
- **Simplicity**: Single file, no setup required
- **Persistence**: Data survives server restarts
- **Appropriate Scale**: Perfect for automation testing scenarios
- **Easy Migration**: Can easily switch to PostgreSQL/MySQL in production

### Client Design: Session-Based
- **Flexibility**: Supports both context manager and persistent usage
- **Error Handling**: Comprehensive exception handling with detailed error info
- **Logging**: Built-in request/response logging for debugging
- **Reusability**: Single interface for all API operations

### Validation Approach
- **Israeli ID**: Implements authentic check-digit algorithm
- **Phone Numbers**: International format validation (+country-area-number)
- **Required Fields**: Server-side validation with clear error messages
- **Input Sanitization**: Automatic trimming and formatting

## 📡 API Endpoints

### Core Endpoints
- `POST /users` - Create new user
- `GET /users/{id}` - Retrieve user by ID
- `GET /users` - List all user IDs
- `GET /health` - Health check

### Request/Response Examples

#### Create User
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "id": "123456782",
    "name": "John Doe",
    "phone": "+972-50-1234567",
    "address": "Rothschild 1, Tel Aviv"
  }'
```

**Response** (201 Created):
```json
{
  "id": "123456782",
  "name": "John Doe",
  "phone": "+972-50-1234567",
  "address": "Rothschild 1, Tel Aviv",
  "created_at": "2025-07-06T08:00:00Z"
}
```

#### Get User
```bash
curl http://localhost:8000/users/123456782
```

#### Error Response (422 Validation Error):
```json
{
  "error": "Validation failed",
  "details": [
    {
      "type": "value_error",
      "loc": ["body", "id"],
      "msg": "Invalid Israeli ID - check digit should be 2, got 7"
    }
  ],
  "timestamp": "2025-07-06T08:00:00Z"
}
```

## 🐍 Python Client Usage

### Basic Usage
```python
from client import UserAPIClient

# Context manager (recommended)
with UserAPIClient() as client:
    # Create user
    user = client.create_user(
        user_id="123456782",
        name="Test User",
        phone="+972-50-1234567",
        address="Test Address"
    )
    
    # Get user
    user_data = client.get_user("123456782")
    
    # List all users
    user_ids = client.list_users()
    
    # Check if user exists
    exists = client.user_exists("123456782")
```

### Persistent Client
```python
# For multiple operations
client = UserAPIClient()
user1 = client.create_user(...)
user2 = client.create_user(...)
client.close()  # When done
```

### Error Handling
```python
from client import APIClientError

try:
    user = client.create_user(...)
except APIClientError as e:
    print(f"Error: {e}")
    print(f"Status: {e.status_code}")
    print(f"Details: {e.response_data}")
```

## 🔧 Configuration

### Environment Variables
- `API_BASE_URL` - Client default server URL (default: http://localhost:8000)
- `PYTHONUNBUFFERED` - Enable real-time logging

### Server Configuration
```python
# In main.py
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Client Configuration
```python
client = UserAPIClient(
    base_url="http://your-server:8000",
    timeout=30
)
```

## 🐳 Docker Deployment

### Build & Run Server Container
```bash
# Build image
docker build -t user-api .

# Run container
docker run -p 8000:8000 user-api

# With volume for persistent data
docker run -p 8000:8000 -v $(pwd)/data:/app/data user-api
```

### Docker Compose (Full Stack)
```bash
# Start all services
docker-compose up

# Background mode
docker-compose up -d

# With client testing
docker-compose --profile testing up
```

## 🧪 Testing

### Manual Testing
```bash
# Health check
curl http://localhost:8000/health

# Create test user
python -c "
from client import UserAPIClient
with UserAPIClient() as client:
    user = client.create_user('123456782', 'Test', '+972-50-1234567', 'Address')
    print(f'Created: {user}')
"
```

### Automated Test Examples
```bash
# Basic functionality
python client.py

# Comprehensive scenarios
python example_usage.py

```

### Test Scenarios Covered
- ✅ Health check
- ✅ User creation with valid data
- ✅ User retrieval
- ✅ User listing
- ✅ Duplicate prevention (409 Conflict)
- ✅ Validation errors (422)
- ✅ Not found errors (404)
- ✅ Invalid format errors (400)

## 📊 Logging & Monitoring

### Server Logs
- **Location**: `server.log` and console
- **Format**: `TIMESTAMP - LOGGER - LEVEL - MESSAGE`
- **Levels**: DEBUG, INFO, WARNING, ERROR

### Client Logs
- **Request/Response tracking**
- **Error details with status codes**
- **Operation timing**

### Log Examples
```
2025-07-06 11:00:00,000 - main - INFO - Attempting to create user with ID: 123456782
2025-07-06 11:00:00,005 - main - INFO - Successfully created user: 123456782
2025-07-06 11:00:00,010 - client - INFO - UserAPIClient initialized with base_url: http://localhost:8000
```

## 🔒 Security Considerations

### Input Validation
- **Israeli ID**: Mathematical validation with check-digit algorithm
- **Phone Numbers**: Format validation and sanitization
- **SQL Injection**: SQLAlchemy ORM prevents injection attacks
- **XSS Prevention**: JSON responses, no HTML rendering

### Error Handling
- **No Sensitive Data**: Error messages don't expose internal details
- **Structured Responses**: Consistent error format
- **Logging**: Security events logged for monitoring

## 🚀 Roadmap & Future Improvements

### Scalability Improvements
1. **Database**
   - Switch to PostgreSQL for production
   - Add connection pooling
   - Implement database migrations
   - Add read replicas for scaling

2. **Performance**
   - Add Redis caching layer
   - Implement pagination for user listing
   - Add database indexes
   - Async database operations

3. **Infrastructure**
   - Kubernetes deployment manifests
   - Load balancer configuration
   - Auto-scaling policies
   - Health check improvements

### Extensibility Enhancements
1. **API Features**
   - User update/delete endpoints
   - Bulk operations
   - Search and filtering
   - Data export/import

2. **Validation**
   - Configurable validation rules
   - Support for international IDs
   - Custom validation plugins
   - Field-level permissions

3. **Integration**
   - Webhook notifications
   - External system integrations
   - Audit trail
   - Event sourcing

### Maintainability Improvements
1. **Code Quality**
   - Unit test coverage (90%+)
   - Integration test suite
   - Code coverage reporting
   - Automated code quality checks

2. **Documentation**
   - API versioning strategy
   - Comprehensive API docs
   - Client SDK documentation
   - Deployment guides

3. **DevOps**
   - CI/CD pipeline setup
   - Automated testing
   - Security scanning
   - Performance monitoring

4. **Observability**
   - Metrics collection (Prometheus)
   - Distributed tracing
   - Application Performance Monitoring
   - Custom dashboards

### Authentication & Authorization (Bonus)
1. **JWT Implementation**
   - User registration/login
   - Token-based authentication
   - Refresh token support
   - Role-based access control

2. **Security Features**
   - Rate limiting
   - API key management
   - OAuth2 integration
   - Multi-factor authentication

## 🛠️ Development

### Code Style
- **Python**: PEP 8 compliance
- **FastAPI**: Async/await patterns
- **Type Hints**: Comprehensive typing
- **Docstrings**: Google style documentation

### Dependencies Management
```bash
# Update dependencies
pip freeze > requirements.txt
pip freeze > client_requirements.txt

# Security check
pip audit
```

### Development Workflow
1. Make changes
2. Test locally
3. Run examples
4. Update documentation
5. Build Docker image
6. Deploy

## ❓ Troubleshooting

### Common Issues

#### Server won't start
```bash
# Check if port is in use
netstat -an | findstr 8000

# Use different port
python main.py --port 8080
```

#### Database locked
```bash
# Remove database file
rm users.db
# Restart server
```

#### Client connection errors
```bash
# Verify server is running
curl http://localhost:8000/health

# Check server logs
tail -f server.log
```

### Debug Mode
```bash
# Enable debug logging
export PYTHONPATH=.
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# Run your code
"
```

## 📞 Support

For questions or issues:
- **Check logs**: `server.log` for server issues
- **Verify setup**: Ensure all dependencies installed
- **Test connectivity**: Use health check endpoint
- **Review examples**: `example_usage.py` for usage patterns

---

**Built for Aqua Security - Automation Infrastructure Team**

*This project demonstrates production-ready API development with comprehensive testing infrastructure suitable for automation engineering workflows.*