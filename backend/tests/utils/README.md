# Test Utilities

This directory contains reusable test utilities for the backend test improvement project.

## Overview

The test utilities provide clean, reusable components for creating test data and simulating error conditions without polluting production code with test-specific logic.

## Components

### TestDataFactory

Factory class for creating test data objects with sensible defaults and customizable parameters.

```python
from tests.utils import TestDataFactory

# Create a user with default values
user = TestDataFactory.create_user()

# Create a user with custom values
user = TestDataFactory.create_user(
    email="custom@example.com",
    name="Custom User"
)

# Create usage records
usage = TestDataFactory.create_usage_record(
    user_id=1,
    usage_count=5
)

# Create tasks
task = TestDataFactory.create_task(
    user_id=1,
    title="Custom Task",
    completed=True
)
```

### UserFactory

Factory pattern implementation specifically for User objects, supporting both in-memory creation and database persistence.

```python
from tests.utils import UserFactory

# Build user object without persisting
user = UserFactory.build(email="test@example.com")

# Create and persist user to database
user = UserFactory.create(session, email="test@example.com")

# Create multiple users in batch
users = UserFactory.create_batch(session, count=5)
```

### TestErrorScenarios

Utility class for simulating various error conditions in tests.

```python
from tests.utils import TestErrorScenarios
from unittest.mock import patch

# Simulate specific errors
clerk_error = TestErrorScenarios.simulate_clerk_api_error()
db_error = TestErrorScenarios.simulate_database_error()
http_error = TestErrorScenarios.simulate_http_exception(404, "Not found")

# Use with mocks
with patch("app.services.clerk_service.get_user_plan", side_effect=clerk_error):
    # Test error handling
    pass

# Get common error scenarios for parameterized tests
error_scenarios = TestErrorScenarios.get_common_error_scenarios()

@pytest.mark.parametrize("error_name,error", error_scenarios.items())
def test_error_handling(error_name, error):
    # Test with different error types
    pass
```

## Usage in Tests

### Unit Tests

```python
import pytest
from tests.utils import TestDataFactory, UserFactory, TestErrorScenarios

class TestMyService:
    def test_service_with_test_data(self):
        # Use factory to create test data
        user = TestDataFactory.create_user()
        usage = TestDataFactory.create_usage_record(user_id=user.id)

        # Test your service logic
        assert service.process_user(user) is not None

    def test_error_handling(self):
        # Simulate errors cleanly
        error = TestErrorScenarios.simulate_clerk_api_error()

        with patch("service.external_call", side_effect=error):
            # Test error handling
            pass
```

### Integration Tests

```python
from tests.utils import UserFactory, TestErrorScenarios

class TestAPIIntegration:
    def test_api_with_real_user(self, session):
        # Create user in database
        user = UserFactory.create(session, email="integration@test.com")

        # Test API with real data
        response = client.get(f"/api/users/{user.id}")
        assert response.status_code == 200

    def test_api_error_handling(self):
        # Test API error responses
        scenarios = TestErrorScenarios.get_http_error_scenarios()

        for scenario_name, error in scenarios.items():
            with patch("service.method", side_effect=error):
                response = client.get("/api/endpoint")
                assert response.status_code == error.status_code
```

## Benefits

1. **Clean Separation**: Test utilities are completely separate from production code
2. **Reusability**: Common test patterns can be reused across different test files
3. **Consistency**: Standardized way to create test data and simulate errors
4. **Maintainability**: Changes to test data creation are centralized
5. **Readability**: Tests focus on business logic rather than test setup

## Requirements Satisfied

- **2.1**: All test setup is contained in test directory
- **2.2**: Test fixtures and utilities are properly organized
- **2.5**: Reusable test helpers are implemented for common patterns