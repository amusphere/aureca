"""Test error scenarios for simulating various error conditions in tests."""

from typing import Any
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError


class TestErrorScenarios:
    """Utility class for simulating various error scenarios in tests."""

    @staticmethod
    def simulate_clerk_api_error(error_message: str = "Clerk API error", error_type: type = Exception) -> Exception:
        """Simulate a Clerk API error.

        Args:
            error_message: Error message to use (default: "Clerk API error")
            error_type: Type of exception to raise (default: Exception)

        Returns:
            Exception instance that can be used with side_effect
        """
        return error_type(error_message)

    @staticmethod
    def simulate_database_error(
        error_message: str = "Database connection failed", error_type: type = SQLAlchemyError
    ) -> Exception:
        """Simulate a database error.

        Args:
            error_message: Error message to use (default: "Database connection failed")
            error_type: Type of exception to raise (default: SQLAlchemyError)

        Returns:
            Exception instance that can be used with side_effect
        """
        return error_type(error_message)

    @staticmethod
    def simulate_network_error(
        error_message: str = "Network unreachable", error_type: type = ConnectionError
    ) -> Exception:
        """Simulate a network error.

        Args:
            error_message: Error message to use (default: "Network unreachable")
            error_type: Type of exception to raise (default: ConnectionError)

        Returns:
            Exception instance that can be used with side_effect
        """
        return error_type(error_message)

    @staticmethod
    def simulate_http_exception(
        status_code: int = 500, detail: str = "Internal server error", headers: dict[str, Any] | None = None
    ) -> HTTPException:
        """Simulate an HTTP exception.

        Args:
            status_code: HTTP status code (default: 500)
            detail: Error detail message (default: "Internal server error")
            headers: Optional HTTP headers

        Returns:
            HTTPException instance that can be used with side_effect
        """
        return HTTPException(status_code=status_code, detail=detail, headers=headers)

    @staticmethod
    def simulate_timeout_error(
        error_message: str = "Operation timed out", error_type: type = TimeoutError
    ) -> Exception:
        """Simulate a timeout error.

        Args:
            error_message: Error message to use (default: "Operation timed out")
            error_type: Type of exception to raise (default: TimeoutError)

        Returns:
            Exception instance that can be used with side_effect
        """
        return error_type(error_message)

    @staticmethod
    def simulate_memory_error(error_message: str = "Out of memory") -> MemoryError:
        """Simulate a memory error.

        Args:
            error_message: Error message to use (default: "Out of memory")

        Returns:
            MemoryError instance that can be used with side_effect
        """
        return MemoryError(error_message)

    @staticmethod
    def create_failing_mock(error: Exception, method_name: str = "side_effect_method") -> MagicMock:
        """Create a mock that raises an exception when called.

        Args:
            error: Exception to raise when mock is called
            method_name: Name of the method that should fail

        Returns:
            MagicMock configured to raise the specified exception
        """
        mock = MagicMock()
        setattr(mock, method_name, MagicMock(side_effect=error))
        return mock

    @staticmethod
    def patch_with_error(target: str, error: Exception, **patch_kwargs):
        """Create a patch context manager that raises an error.

        Args:
            target: Target to patch (same as patch() target)
            error: Exception to raise when patched method is called
            **patch_kwargs: Additional keyword arguments for patch()

        Returns:
            Context manager that patches the target to raise the error
        """
        return patch(target, side_effect=error, **patch_kwargs)

    @classmethod
    def get_common_error_scenarios(cls) -> dict[str, Exception]:
        """Get a dictionary of common error scenarios for parameterized tests.

        Returns:
            Dictionary mapping scenario names to exception instances
        """
        return {
            "clerk_api_error": cls.simulate_clerk_api_error(),
            "database_error": cls.simulate_database_error(),
            "network_error": cls.simulate_network_error(),
            "timeout_error": cls.simulate_timeout_error(),
            "memory_error": cls.simulate_memory_error(),
            "generic_error": Exception("Generic test error"),
        }

    @classmethod
    def get_http_error_scenarios(cls) -> dict[str, HTTPException]:
        """Get a dictionary of common HTTP error scenarios for API tests.

        Returns:
            Dictionary mapping scenario names to HTTPException instances
        """
        return {
            "bad_request": cls.simulate_http_exception(400, "Bad request"),
            "unauthorized": cls.simulate_http_exception(401, "Unauthorized"),
            "forbidden": cls.simulate_http_exception(403, "Forbidden"),
            "not_found": cls.simulate_http_exception(404, "Not found"),
            "too_many_requests": cls.simulate_http_exception(429, "Too many requests"),
            "internal_server_error": cls.simulate_http_exception(500, "Internal server error"),
            "service_unavailable": cls.simulate_http_exception(503, "Service unavailable"),
        }
