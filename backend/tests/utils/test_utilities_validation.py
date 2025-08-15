"""Validation tests for test utilities to ensure they work correctly."""

from app.schema import AIChatUsage, Tasks, User
from tests.utils import TestDataFactory, TestErrorScenarios, UserFactory


class TestTestUtilities:
    """Test the test utilities themselves to ensure they work correctly."""

    def test_test_data_factory_create_user(self):
        """Test TestDataFactory.create_user creates valid User objects."""
        user = TestDataFactory.create_user()

        assert isinstance(user, User)
        assert user.clerk_sub is not None
        assert user.email is not None
        assert user.name is not None
        assert user.created_at is not None
        assert "@example.com" in user.email

    def test_test_data_factory_create_user_with_custom_values(self):
        """Test TestDataFactory.create_user with custom values."""
        custom_email = "custom@test.com"
        custom_name = "Custom User"

        user = TestDataFactory.create_user(email=custom_email, name=custom_name)

        assert user.email == custom_email
        assert user.name == custom_name

    def test_test_data_factory_create_usage_record(self):
        """Test TestDataFactory.create_usage_record creates valid AIChatUsage objects."""
        usage = TestDataFactory.create_usage_record(user_id=1)

        assert isinstance(usage, AIChatUsage)
        assert usage.user_id == 1
        assert usage.usage_date is not None
        assert usage.usage_count == 1
        assert usage.created_at is not None
        assert usage.updated_at is not None

    def test_test_data_factory_create_task(self):
        """Test TestDataFactory.create_task creates valid Tasks objects."""
        task = TestDataFactory.create_task(user_id=1)

        assert isinstance(task, Tasks)
        assert task.user_id == 1
        assert task.title is not None
        assert task.completed is False
        assert task.expires_at is not None
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_user_factory_build(self):
        """Test UserFactory.build creates User objects without persistence."""
        user = UserFactory.build()

        assert isinstance(user, User)
        assert user.clerk_sub is not None
        assert user.email is not None
        assert user.name is not None
        assert user.created_at is not None

    def test_user_factory_build_with_custom_values(self):
        """Test UserFactory.build with custom values."""
        custom_email = "factory@test.com"
        user = UserFactory.build(email=custom_email)

        assert user.email == custom_email

    def test_error_scenarios_clerk_api_error(self):
        """Test TestErrorScenarios.simulate_clerk_api_error."""
        error = TestErrorScenarios.simulate_clerk_api_error()

        assert isinstance(error, Exception)
        assert "Clerk API error" in str(error)

    def test_error_scenarios_database_error(self):
        """Test TestErrorScenarios.simulate_database_error."""
        error = TestErrorScenarios.simulate_database_error()

        assert isinstance(error, Exception)
        assert "Database connection failed" in str(error)

    def test_error_scenarios_http_exception(self):
        """Test TestErrorScenarios.simulate_http_exception."""
        from fastapi import HTTPException

        error = TestErrorScenarios.simulate_http_exception(status_code=404, detail="Not found")

        assert isinstance(error, HTTPException)
        assert error.status_code == 404
        assert error.detail == "Not found"

    def test_error_scenarios_common_scenarios(self):
        """Test TestErrorScenarios.get_common_error_scenarios."""
        scenarios = TestErrorScenarios.get_common_error_scenarios()

        assert isinstance(scenarios, dict)
        assert "clerk_api_error" in scenarios
        assert "database_error" in scenarios
        assert "network_error" in scenarios
        assert all(isinstance(error, Exception) for error in scenarios.values())

    def test_error_scenarios_http_scenarios(self):
        """Test TestErrorScenarios.get_http_error_scenarios."""
        from fastapi import HTTPException

        scenarios = TestErrorScenarios.get_http_error_scenarios()

        assert isinstance(scenarios, dict)
        assert "bad_request" in scenarios
        assert "unauthorized" in scenarios
        assert "not_found" in scenarios
        assert all(isinstance(error, HTTPException) for error in scenarios.values())
        assert scenarios["bad_request"].status_code == 400
        assert scenarios["not_found"].status_code == 404
