"""
User service for handling user-related operations including Stripe customer management.

This service provides user management functionality with integrated Stripe customer
creation and management, following the repository pattern for data access.
"""

import logging

from sqlmodel import Session
from stripe import error as stripe_error

# Note: subscription repository import removed as part of Stripe migration
# Subscription data will be fetched directly from Stripe API
from app.repositories import user as user_repository
from app.schema import User
from app.services.stripe_service import StripeService
from app.utils.auth.clerk import create_user_by_clerk_sub

logger = logging.getLogger(__name__)


class UserService:
    """Service for handling user operations with Stripe integration."""

    def __init__(self, stripe_service: StripeService | None = None):
        """
        Initialize UserService with optional Stripe service dependency.

        Args:
            stripe_service: Optional StripeService instance for dependency injection
        """
        self.stripe_service = stripe_service or StripeService(raise_on_missing_config=False)

    def create_new_user(sub: str, session: Session) -> User:
        """
        Create a new user with the given Clerk subject ID.

        Args:
            sub: The Clerk subject ID for the new user
            session: Database session for transaction management

        Returns:
            User: The newly created user object

        Raises:
            Exception: If user creation fails
        """
        return create_user_by_clerk_sub

    async def ensure_stripe_customer(self, user: User, session: Session) -> str:
        """
        Ensure the user has a Stripe customer ID, creating one if necessary.

        This method implements idempotent customer creation - if the user already
        has a stripe_customer_id, it returns that ID. Otherwise, it creates a new
        Stripe customer and updates the user record.

        Args:
            user: The user to ensure has a Stripe customer
            session: Database session for transaction management

        Returns:
            str: The Stripe customer ID

        Raises:
            ValueError: If Stripe is not configured
            stripe.error.StripeError: If Stripe customer creation fails
            Exception: For unexpected errors during the process
        """
        if not self.stripe_service.is_configured():
            raise ValueError("Stripe is not configured. Cannot create customer.")

        # If user already has a Stripe customer ID, return it
        if user.stripe_customer_id:
            logger.debug(f"User {user.id} already has Stripe customer ID: {user.stripe_customer_id}")
            return user.stripe_customer_id

        try:
            # Create Stripe customer
            logger.info(f"Creating Stripe customer for user {user.id}")
            stripe_customer_id = await self.stripe_service.create_customer(user)

            # Update user record with Stripe customer ID
            updated_user = user_repository.update_user_stripe_customer_id(session, user.id, stripe_customer_id)

            if not updated_user:
                # This should not happen if user exists, but handle gracefully
                raise Exception(f"Failed to update user {user.id} with Stripe customer ID")

            # Update the user object in memory as well
            user.stripe_customer_id = stripe_customer_id

            logger.info(f"Successfully created and linked Stripe customer {stripe_customer_id} for user {user.id}")
            return stripe_customer_id

        except stripe_error.StripeError as e:
            logger.error(f"Stripe error creating customer for user {user.id}: {e}")
            # Rollback is handled by the session context
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating Stripe customer for user {user.id}: {e}")
            # Rollback is handled by the session context
            raise

    async def get_user_with_subscription(self, user_id: int, session: Session) -> dict:
        """
        Get user information with subscription details.

        Args:
            user_id: The user ID to retrieve
            session: Database session

        Returns:
            dict: User information with subscription details

        Raises:
            ValueError: If user is not found
        """
        user = user_repository.get_user_by_id(session, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        # TODO: Get subscription information from Stripe API (will be implemented in later tasks)
        # For now, return basic user data with no subscription
        user_data = {
            "id": user.id,
            "uuid": str(user.uuid),
            "email": user.email,
            "name": user.name,
            "clerk_sub": user.clerk_sub,
            "stripe_customer_id": user.stripe_customer_id,
            "created_at": user.created_at,
            "subscription": {
                "isPremium": False,
                "planName": None,
                "status": None,
                "currentPeriodEnd": None,
                "cancelAtPeriodEnd": False,
                "stripeSubscriptionId": None,
                "stripePriceId": None,
            },
        }

        return user_data

    async def update_user_stripe_customer_id(self, user_id: int, stripe_customer_id: str, session: Session) -> User:
        """
        Update a user's Stripe customer ID.

        Args:
            user_id: The user ID to update
            stripe_customer_id: The Stripe customer ID to set
            session: Database session

        Returns:
            User: The updated user object

        Raises:
            ValueError: If user is not found
        """
        updated_user = user_repository.update_user_stripe_customer_id(session, user_id, stripe_customer_id)
        if not updated_user:
            raise ValueError(f"User with ID {user_id} not found")

        logger.info(f"Updated user {user_id} with Stripe customer ID {stripe_customer_id}")
        return updated_user


# Global instance for dependency injection
user_service = UserService()
