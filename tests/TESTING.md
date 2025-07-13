# Testing Guide - User Management API

This document describes the comprehensive testing strategy for the User Management API.

## 🧪 Test Structure

### Test Files Overview
- **`test_server.py`** - Unit tests for FastAPI server endpoints
- **`test_client.py`** - Unit tests for Python client library
- **`test_integration.py`** - End-to-end integration tests
- **`run_tests.py`** - Test runner with multiple execution modes

### Test Categories
- 🔧 **Unit Tests** - Fast, isolated tests with no external dependencies
- 🔗 **Integration Tests** - Full system tests requiring running server
- 📊 **Performance Tests** - Response time and load testing
- 🛡️ **Security Tests** - Input validation and error handling

## 🚀 Quick Start

### Prerequisites
```bash
# Install test dependencies
pip install -r test_requirements.txt
```

### Running Tests

#### 1. Unit Tests Only (No Server Required)
```bash
python run_tests.py unit
```

#### 2. Integration Tests (Server Required)
```bash
# Start server first
python main.py

# In another terminal
python run_tests.py integration
```

#### 3. All Tests
```bash
python run_tests.py all
```

#### 4. With Coverage Report
```bash
python run_tests.py coverage
```

#### 5. Using Pytest
```bash
python run_tests.py pytest
```

## 📋 Test Scenarios

### Server Tests (`test_server.py`)

#### Core Functionality
- ✅ Health check endpoint
- ✅ User creation with valid data
- ✅ User retrieval by ID
- ✅ User listing
- ✅ Duplicate prevention

#### Validation Tests
- ✅ Israeli ID validation algorithm
- ✅ Phone number format validation
- ✅ Required field validation
- ✅ Input sanitization

#### Error Handling
- ✅ 404 for non-existent users
- ✅ 400 for invalid input format
- ✅ 409 for duplicate IDs
- ✅ 422 for validation errors
- ✅ 500 error handling

### Client Tests (`test_client.py`)

#### API Interaction
- ✅ Health check calls
- ✅ User CRUD operations
- ✅ Error response parsing
- ✅ Session management

#### Utility Functions
- ✅ Israeli ID generation
- ✅ Input validation helpers
- ✅ Context manager support

#### Error Scenarios
- ✅ Connection failures
- ✅ Timeout handling
- ✅ Invalid JSON responses
- ✅ HTTP error codes

### Integration Tests (`test_integration.py`)

#### Live System Tests
- ✅ Complete user lifecycle
- ✅ Data persistence verification
- ✅ Concurrent request handling
- ✅ Performance benchmarks

#### Edge Cases
- ✅ Large data handling
- ✅ Special characters support
- ✅ Boundary conditions
- ✅ System resilience

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)
```ini
[tool:pytest]
testpaths = .
python_files = test_*.py
addopts = -v --tb=short --cov=. --cov-report=html
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
```

### Coverage Settings
- **Target**: 80% minimum coverage
- **Reports**: Terminal + HTML
- **Exclusions**: Test files themselves

## 📊 Test Reports

### Generate Comprehensive Report
```bash
python run_tests.py report
```

This creates `test_report.md` with:
- System information
- Server status
- Test results summary
- Coverage statistics

### Coverage Report
```bash
python run_tests.py coverage
# View: htmlcov/index.html
```

## 🎯 Specific Test Examples

### Testing Israeli ID Validation
```python
def test_israeli_id_validation(self):
    """Test Israeli ID validation algorithm"""
    test_cases = [
        ("123456782", True),   # Valid
        ("123456780", False),  # Invalid check digit
        ("12345678", False),   # Too short
    ]
    
    for test_id, should_be_valid in test_cases:
        # Test logic here
```

### Testing Error Handling
```python
def test_user_not_found(self):
    """Test 404 error for non-existent user"""
    response = self.client.get("/users/123456790")
    self.assertEqual(response.status_code, 404)
    self.assertEqual(response.json()["error"], "User not found")
```

### Integration Test Example
```python
def test_complete_workflow(self):
    """Test complete user management workflow"""
    # 1. Health check
    health = self.client.health_check()
    self.assertEqual(health["status"], "healthy")
    
    # 2. Create user
    user = self.client.create_user(...)
    
    # 3. Verify creation
    retrieved = self.client.get_user(user["id"])
    self.assertEqual(retrieved["name"], user["name"])
```

## 🐛 Debugging Tests

### Verbose Mode
```bash
python -m unittest test_server -v
```

### Debug Single Test
```bash
python -m unittest test_server.TestUserAPI.test_create_user_valid -v
```

### Debug with Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# Run your test
```

### Server Logs During Tests
```bash
# Terminal 1: Start server with debug
python main.py

# Terminal 2: Run tests and watch server logs
python run_tests.py integration
```

## 🔍 Test Data Management

### Test Database
- Uses temporary SQLite database for unit tests
- Isolated from production data
- Automatically cleaned between tests

### Test User IDs
- Generated with valid Israeli ID check digits
- Time-based uniqueness to avoid conflicts
- Predictable patterns for debugging

### Mock Data
- Uses `responses` library for HTTP mocking
- Consistent test data across test runs
- Realistic edge cases and error scenarios

## ⚡ Performance Testing

### Response Time Benchmarks
```python
def test_performance_benchmarks(self):
    """Test basic performance requirements"""
    start_time = time.time()
    self.client.health_check()
    response_time = time.time() - start_time
    
    self.assertLess(response_time, 5.0, "Response too slow")
```

### Concurrent Request Testing
```python
def test_concurrent_requests(self):
    """Test handling of multiple simultaneous requests"""
    threads = []
    for i in range(10):
        thread = threading.Thread(target=self.create_user_thread, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait and verify all succeeded
```

### Load Testing Simulation
```bash
# Using the integration tests
python test_integration.py TestSystemResilience.test_concurrent_requests
```

## 🛡️ Security Testing

### Input Validation Tests
- SQL injection prevention
- XSS protection (JSON responses)
- Invalid data rejection
- Buffer overflow protection

### Authentication Testing (if implemented)
- Token validation
- Permission checking
- Session management
- Rate limiting

## 📈 Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r test_requirements.txt
      
      - name: Run unit tests
        run: python run_tests.py unit
      
      - name: Start server
        run: python main.py &
        
      - name: Run integration tests
        run: python run_tests.py integration
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Add to .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: Run Tests
        entry: python run_tests.py unit
        language: system
        pass_filenames: false
```

## 📝 Test Documentation Standards

### Test Method Naming
- `test_<functionality>_<scenario>`
- `test_create_user_valid_data`
- `test_get_user_not_found`

### Test Docstrings
```python
def test_israeli_id_validation(self):
    """
    Test Israeli ID validation algorithm.
    
    Verifies:
    - Valid IDs are accepted
    - Invalid check digits are rejected
    - Format validation works correctly
    """
```

### Assertion Messages
```python
self.assertEqual(
    response.status_code, 200,
    f"Expected 200, got {response.status_code}: {response.text}"
)
```

## 🔄 Test Maintenance

### Regular Test Review
- Update tests when API changes
- Add tests for new features
- Remove obsolete tests
- Maintain test data relevance

### Performance Monitoring
- Track test execution time
- Identify slow tests
- Optimize test database usage
- Monitor coverage trends

### Test Environment Management
- Keep test dependencies updated
- Maintain test data consistency
- Regular cleanup of test artifacts
- Documentation updates

## 🎯 Best Practices

### Test Organization
- One test file per module
- Logical test grouping
- Clear test dependencies
- Isolated test execution

### Data Management
- Use factories for test data
- Clean state between tests
- Realistic test scenarios
- Edge case coverage

### Error Testing
- Test all error paths
- Verify error messages
- Check error codes
- Validate error handling

### Documentation
- Document complex test logic
- Explain test data choices
- Maintain setup instructions
- Update troubleshooting guides

---

## 🆘 Troubleshooting

### Common Issues

#### Tests Fail with "Server not available"
```bash
# Check if server is running
python run_tests.py --server-check

# Start server
python main.py
```

#### Database locked errors
```bash
# Remove test database files
rm *.db
```

#### Import errors
```bash
# Install missing dependencies
pip install -r test_requirements.txt
```

#### Permission errors
```bash
# Fix file permissions
chmod +x run_tests.py
```

### Getting Help
- Check test logs for detailed error messages
- Use verbose mode: `-v` flag
- Review server logs during integration tests
- Verify all dependencies are installed

---

**For more information, see the main [README.md](README.md) file.**