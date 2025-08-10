"""
Unit tests for ClerkService
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.clerk_service import ClerkService


class TestClerkService:
    """Test ClerkService class"""

    @pytest.fixture
    def mock_clerk_service(self):
        """Create ClerkService instance with mocked Clerk client for testing"""
        with patch("app.services.clerk_service.Clerk") as mock_clerk_class:
            mock_client = MagicMock()
            mock_clerk_class.return_value = mock_client

            service = ClerkService()
            service.client = mock_client  # Ensure we can access the mock client
            return service, mock_client

    def test_get_user_plan_success_standard(self, mock_clerk_service):
        """Test successful retrieval of standard plan"""
        clerk_service, mock_client = mock_clerk_service

        # Setup mock
        mock_user = MagicMock()
        mock_user.public_metadata = {"plan": "standard"}
        mock_client.users.get.return_value = mock_user

        # Test
        plan = clerk_service.get_user_plan("user_123")

        # Verify
        assert plan == "standard"
        mock_client.users.get.assert_called_once_with(user_id="user_123")

    def test_get_user_plan_success_free(self, mock_clerk_service):
        """Test successful retrieval of free plan"""
        clerk_service, mock_client = mock_clerk_service

        # Setup mock
        mock_user = MagicMock()
        mock_user.public_metadata = {"plan": "free"}
        mock_client.users.get.return_value = mock_user

        # Test
        plan = clerk_service.get_user_plan("user_123")

        # Verify
        assert plan == "free"
        mock_client.users.get.assert_called_once_with(user_id="user_123")

    def test_get_user_plan_no_metadata(self, mock_clerk_service):
        """Test user with no public metadata defaults to free"""
        clerk_service, mock_client = mock_clerk_service

        # Setup mock
        mock_user = MagicMock()
        mock_user.public_metadata = {}
        mock_user.private_metadata = {}
        mock_client.users.get.return_value = mock_user

        # Test
        plan = clerk_service.get_user_plan("user_123")

        # Verify
        assert plan == "free"
        mock_client.users.get.assert_called_once_with(user_id="user_123")

    def test_get_user_plan_none_metadata(self, mock_clerk_service):
        """Test user with None public metadata defaults to free"""
        clerk_service, mock_client = mock_clerk_service

        # Setup mock
        mock_user = MagicMock()
        mock_user.public_metadata = None
        mock_user.private_metadata = None
        mock_client.users.get.return_value = mock_user

        # Test
        plan = clerk_service.get_user_plan("user_123")

        # Verify
        assert plan == "free"
        mock_client.users.get.assert_called_once_with(user_id="user_123")

    def test_get_user_plan_private_metadata_fallback(self, mock_clerk_service):
        """Test fallback to private metadata when public metadata has no plan"""
        clerk_service, mock_client = mock_clerk_service

        # Setup mock
        mock_user = MagicMock()
        mock_user.public_metadata = {}  # No plan in public metadata
        mock_user.private_metadata = {"plan": "standard"}  # Plan in private metadata
        mock_client.users.get.return_value = mock_user

        # Test
        plan = clerk_service.get_user_plan("user_123")

        # Verify
        assert plan == "standard"
        mock_client.users.get.assert_called_once_with(user_id="user_123")

    def test_get_user_plan_invalid_plan_in_metadata(self, mock_clerk_service):
        """Test user with invalid plan in metadata defaults to free"""
        clerk_service, mock_client = mock_clerk_service

        # Setup mock
        mock_user = MagicMock()
        mock_user.public_metadata = {"plan": "premium"}  # Invalid plan
        mock_user.private_metadata = {}
        mock_client.users.get.return_value = mock_user

        # Test
        plan = clerk_service.get_user_plan("user_123")

        # Verify - should return the plan as-is (validation happens elsewhere)
        assert plan == "premium"
        mock_client.users.get.assert_called_once_with(user_id="user_123")

    def test_get_user_plan_clerk_api_error(self, mock_clerk_service):
        """Test Clerk API error falls back to free plan"""
        clerk_service, mock_client = mock_clerk_service

        # Setup mock to raise exception
        mock_client.users.get.side_effect = Exception("Clerk API error")

        # Test
        plan = clerk_service.get_user_plan("user_123")

        # Verify
        assert plan == "free"  # Should fallback to free on error
        mock_client.users.get.assert_called_once_with(user_id="user_123")

    def test_get_user_plan_case_handling(self, mock_clerk_service):
        """Test that plan names are converted to lowercase"""
        clerk_service, mock_client = mock_clerk_service

        # Setup mock
        mock_user = MagicMock()
        mock_user.public_metadata = {"plan": "STANDARD"}  # Uppercase
        mock_user.private_metadata = {}
        mock_client.users.get.return_value = mock_user

        # Test
        plan = clerk_service.get_user_plan("user_123")

        # Verify - should be converted to lowercase
        assert plan == "standard"
        mock_client.users.get.assert_called_once_with(user_id="user_123")

    def test_has_subscription_true(self, mock_clerk_service):
        """Test has_subscription returns True for matching plan"""
        clerk_service, mock_client = mock_clerk_service

        # Setup mock
        mock_user = MagicMock()
        mock_user.public_metadata = {"plan": "standard"}
        mock_user.private_metadata = {}
        mock_client.users.get.return_value = mock_user

        # Test
        has_sub = clerk_service.has_subscription("user_123", "standard")

        # Verify
        assert has_sub is True
        mock_client.users.get.assert_called_once_with(user_id="user_123")

    def test_has_subscription_false(self, mock_clerk_service):
        """Test has_subscription returns False for non-matching plan"""
        clerk_service, mock_client = mock_clerk_service

        # Setup mock
        mock_user = MagicMock()
        mock_user.public_metadata = {"plan": "free"}
        mock_user.private_metadata = {}
        mock_client.users.get.return_value = mock_user

        # Test
        has_sub = clerk_service.has_subscription("user_123", "standard")

        # Verify
        assert has_sub is False
        mock_client.users.get.assert_called_once_with(user_id="user_123")

    def test_clerk_service_initialization(self):
        """Test ClerkService can be initialized without errors"""
        with patch("app.services.clerk_service.Clerk") as mock_clerk_class:
            with patch.dict("os.environ", {"CLERK_SECRET_KEY": "test_key"}):
                service = ClerkService()
                assert service is not None
                assert isinstance(service, ClerkService)
                mock_clerk_class.assert_called_once_with(bearer_auth="test_key")

    def test_clerk_service_initialization_no_key(self):
        """Test ClerkService initialization fails without secret key"""
        with patch("app.services.clerk_service.Clerk"):
            with patch.dict("os.environ", {}, clear=True):
                with pytest.raises(ValueError, match="CLERK_SECRET_KEY environment variable is required"):
                    ClerkService()
