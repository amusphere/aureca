"""
Stripe webhook handler for processing subscription events.

This service handles incoming webhook events from Stripe and updates
the local database to maintain synchronization with Stripe's state.
"""

import logging
from typing import Any

import stripe

from app.database import get_session
from app.repositories import subscription as subscription_repo
from app.repositories import user as user_repo

logger = logging.getLogger(__name__)


class StripeWebhookHandler:
    """Handler for processing Stripe webhook events."""

    def __init__(self):
        """Initialize the webhook handler."""
        pass

    async def handle_event(self, event: stripe.Event) -> bool:
        """
        Handle a Stripe webhook event.

        Args:
            event: The verified Stripe event

        Returns:
            bool: True if event was handled successfully, False otherwise
        """
        try:
            event_type = event["type"]
            logger.info(f"Processing webhook event {event['id']} of type {event_type}")

            # Route to appropriate handler based on event type
            if event_type == "customer.subscription.created":
                return await self.handle_customer_subscription_created(event)
            elif event_type == "customer.subscription.updated":
                return await self.handle_customer_subscription_updated(event)
            elif event_type == "customer.subscription.deleted":
                return await self.handle_customer_subscription_deleted(event)
            elif event_type == "invoice.payment_succeeded":
                return await self.handle_invoice_payment_succeeded(event)
            elif event_type == "invoice.payment_failed":
                return await self.handle_invoice_payment_failed(event)
            else:
                logger.info(f"Unhandled event type: {event_type}")
                return True  # Return True for unhandled events to avoid retries

        except Exception as e:
            logger.error(f"Error handling webhook event {event.get('id', 'unknown')}: {e}")
            return False

    async def handle_customer_subscription_created(self, event: stripe.Event) -> bool:
        """
        Handle customer.subscription.created event.

        Creates a new subscription record in the database.

        Args:
            event: The Stripe event

        Returns:
            bool: True if handled successfully, False otherwise
        """
        try:
            subscription_data = event["data"]["object"]
            logger.info(f"Processing subscription created: {subscription_data['id']}")

            # Extract subscription details
            stripe_subscription_id = subscription_data["id"]
            stripe_customer_id = subscription_data["customer"]
            stripe_price_id = subscription_data["items"]["data"][0]["price"]["id"]
            status = subscription_data["status"]
            current_period_start = float(subscription_data["current_period_start"])
            current_period_end = float(subscription_data["current_period_end"])
            cancel_at_period_end = subscription_data.get("cancel_at_period_end", False)
            canceled_at = float(subscription_data["canceled_at"]) if subscription_data.get("canceled_at") else None
            trial_start = float(subscription_data["trial_start"]) if subscription_data.get("trial_start") else None
            trial_end = float(subscription_data["trial_end"]) if subscription_data.get("trial_end") else None

            # Get plan name from price metadata or use price nickname
            plan_name = self._extract_plan_name(subscription_data)

            with get_session() as session:
                # Find the user by stripe_customer_id
                user = user_repo.get_user_br_column(session, stripe_customer_id, "stripe_customer_id")
                if not user:
                    logger.error(f"User not found for Stripe customer {stripe_customer_id}")
                    return False

                # Check if subscription already exists (idempotency)
                existing_subscription = subscription_repo.get_subscription_by_stripe_id(session, stripe_subscription_id)
                if existing_subscription:
                    logger.info(f"Subscription {stripe_subscription_id} already exists, skipping creation")
                    return True

                # Create the subscription
                subscription_repo.create_subscription(
                    session=session,
                    user_id=user.id,
                    stripe_subscription_id=stripe_subscription_id,
                    stripe_customer_id=stripe_customer_id,
                    stripe_price_id=stripe_price_id,
                    plan_name=plan_name,
                    status=status,
                    current_period_start=current_period_start,
                    current_period_end=current_period_end,
                    cancel_at_period_end=cancel_at_period_end,
                    canceled_at=canceled_at,
                    trial_start=trial_start,
                    trial_end=trial_end,
                )

                logger.info(f"Created subscription {stripe_subscription_id} for user {user.id}")
                return True

        except Exception as e:
            logger.error(f"Error handling customer.subscription.created: {e}")
            return False

    async def handle_customer_subscription_updated(self, event: stripe.Event) -> bool:
        """
        Handle customer.subscription.updated event.

        Updates an existing subscription record in the database.

        Args:
            event: The Stripe event

        Returns:
            bool: True if handled successfully, False otherwise
        """
        try:
            subscription_data = event["data"]["object"]
            logger.info(f"Processing subscription updated: {subscription_data['id']}")

            # Extract subscription details
            stripe_subscription_id = subscription_data["id"]
            stripe_price_id = subscription_data["items"]["data"][0]["price"]["id"]
            status = subscription_data["status"]
            current_period_start = float(subscription_data["current_period_start"])
            current_period_end = float(subscription_data["current_period_end"])
            cancel_at_period_end = subscription_data.get("cancel_at_period_end", False)
            canceled_at = float(subscription_data["canceled_at"]) if subscription_data.get("canceled_at") else None
            trial_start = float(subscription_data["trial_start"]) if subscription_data.get("trial_start") else None
            trial_end = float(subscription_data["trial_end"]) if subscription_data.get("trial_end") else None

            # Get plan name from price metadata or use price nickname
            plan_name = self._extract_plan_name(subscription_data)

            with get_session() as session:
                # Update the subscription
                try:
                    subscription_repo.update_subscription_by_stripe_id(
                        session=session,
                        stripe_subscription_id=stripe_subscription_id,
                        stripe_price_id=stripe_price_id,
                        plan_name=plan_name,
                        status=status,
                        current_period_start=current_period_start,
                        current_period_end=current_period_end,
                        cancel_at_period_end=cancel_at_period_end,
                        canceled_at=canceled_at,
                        trial_start=trial_start,
                        trial_end=trial_end,
                    )

                    logger.info(f"Updated subscription {stripe_subscription_id}")
                    return True

                except ValueError as e:
                    if "subscription not found" in str(e):
                        logger.warning(f"Subscription {stripe_subscription_id} not found for update, creating new one")
                        # If subscription doesn't exist, create it
                        return await self._create_subscription_from_event(event, subscription_data)
                    else:
                        raise

        except Exception as e:
            logger.error(f"Error handling customer.subscription.updated: {e}")
            return False

    async def handle_customer_subscription_deleted(self, event: stripe.Event) -> bool:
        """
        Handle customer.subscription.deleted event.

        Marks a subscription as canceled in the database.

        Args:
            event: The Stripe event

        Returns:
            bool: True if handled successfully, False otherwise
        """
        try:
            subscription_data = event["data"]["object"]
            logger.info(f"Processing subscription deleted: {subscription_data['id']}")

            stripe_subscription_id = subscription_data["id"]

            with get_session() as session:
                try:
                    # Deactivate the subscription
                    subscription_repo.deactivate_subscription_by_stripe_id(session, stripe_subscription_id)
                    logger.info(f"Deactivated subscription {stripe_subscription_id}")
                    return True

                except ValueError as e:
                    if "subscription not found" in str(e):
                        logger.warning(f"Subscription {stripe_subscription_id} not found for deletion")
                        return True  # Consider this successful since the end result is the same
                    else:
                        raise

        except Exception as e:
            logger.error(f"Error handling customer.subscription.deleted: {e}")
            return False

    async def handle_invoice_payment_succeeded(self, event: stripe.Event) -> bool:
        """
        Handle invoice.payment_succeeded event.

        Updates subscription status and period information when payment succeeds.

        Args:
            event: The Stripe event

        Returns:
            bool: True if handled successfully, False otherwise
        """
        try:
            invoice_data = event["data"]["object"]
            logger.info(f"Processing invoice payment succeeded: {invoice_data['id']}")

            # Only process subscription invoices
            if not invoice_data.get("subscription"):
                logger.info("Invoice is not for a subscription, skipping")
                return True

            stripe_subscription_id = invoice_data["subscription"]

            with get_session() as session:
                try:
                    # Get the subscription from Stripe to get the latest status
                    stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)

                    # Update the subscription with the latest information
                    subscription_repo.update_subscription_by_stripe_id(
                        session=session,
                        stripe_subscription_id=stripe_subscription_id,
                        status=stripe_subscription.status,
                        current_period_start=float(stripe_subscription.current_period_start),
                        current_period_end=float(stripe_subscription.current_period_end),
                        cancel_at_period_end=stripe_subscription.cancel_at_period_end,
                    )

                    logger.info(f"Updated subscription {stripe_subscription_id} after successful payment")
                    return True

                except ValueError as e:
                    if "subscription not found" in str(e):
                        logger.warning(f"Subscription {stripe_subscription_id} not found for payment update")
                        return True  # Don't fail if subscription doesn't exist locally
                    else:
                        raise

        except Exception as e:
            logger.error(f"Error handling invoice.payment_succeeded: {e}")
            return False

    async def handle_invoice_payment_failed(self, event: stripe.Event) -> bool:
        """
        Handle invoice.payment_failed event.

        Updates subscription status when payment fails.

        Args:
            event: The Stripe event

        Returns:
            bool: True if handled successfully, False otherwise
        """
        try:
            invoice_data = event["data"]["object"]
            logger.info(f"Processing invoice payment failed: {invoice_data['id']}")

            # Only process subscription invoices
            if not invoice_data.get("subscription"):
                logger.info("Invoice is not for a subscription, skipping")
                return True

            stripe_subscription_id = invoice_data["subscription"]

            with get_session() as session:
                try:
                    # Get the subscription from Stripe to get the latest status
                    stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)

                    # Update the subscription with the latest status
                    subscription_repo.update_subscription_by_stripe_id(
                        session=session,
                        stripe_subscription_id=stripe_subscription_id,
                        status=stripe_subscription.status,
                    )

                    logger.info(f"Updated subscription {stripe_subscription_id} after failed payment")
                    return True

                except ValueError as e:
                    if "subscription not found" in str(e):
                        logger.warning(f"Subscription {stripe_subscription_id} not found for payment failure update")
                        return True  # Don't fail if subscription doesn't exist locally
                    else:
                        raise

        except Exception as e:
            logger.error(f"Error handling invoice.payment_failed: {e}")
            return False

    async def _create_subscription_from_event(self, event: stripe.Event, subscription_data: dict[str, Any]) -> bool:
        """
        Helper method to create a subscription from event data.

        Args:
            event: The Stripe event
            subscription_data: The subscription data from the event

        Returns:
            bool: True if created successfully, False otherwise
        """
        try:
            stripe_subscription_id = subscription_data["id"]
            stripe_customer_id = subscription_data["customer"]
            stripe_price_id = subscription_data["items"]["data"][0]["price"]["id"]
            status = subscription_data["status"]
            current_period_start = float(subscription_data["current_period_start"])
            current_period_end = float(subscription_data["current_period_end"])
            cancel_at_period_end = subscription_data.get("cancel_at_period_end", False)
            canceled_at = float(subscription_data["canceled_at"]) if subscription_data.get("canceled_at") else None
            trial_start = float(subscription_data["trial_start"]) if subscription_data.get("trial_start") else None
            trial_end = float(subscription_data["trial_end"]) if subscription_data.get("trial_end") else None

            # Get plan name from price metadata or use price nickname
            plan_name = self._extract_plan_name(subscription_data)

            with get_session() as session:
                # Find the user by stripe_customer_id
                user = user_repo.get_user_br_column(session, stripe_customer_id, "stripe_customer_id")
                if not user:
                    logger.error(f"User not found for Stripe customer {stripe_customer_id}")
                    return False

                # Create the subscription
                subscription_repo.create_subscription(
                    session=session,
                    user_id=user.id,
                    stripe_subscription_id=stripe_subscription_id,
                    stripe_customer_id=stripe_customer_id,
                    stripe_price_id=stripe_price_id,
                    plan_name=plan_name,
                    status=status,
                    current_period_start=current_period_start,
                    current_period_end=current_period_end,
                    cancel_at_period_end=cancel_at_period_end,
                    canceled_at=canceled_at,
                    trial_start=trial_start,
                    trial_end=trial_end,
                )

                logger.info(f"Created subscription {stripe_subscription_id} for user {user.id}")
                return True

        except Exception as e:
            logger.error(f"Error creating subscription from event: {e}")
            return False

    def _extract_plan_name(self, subscription_data: dict[str, Any]) -> str:
        """
        Extract plan name from subscription data.

        Args:
            subscription_data: The subscription data from Stripe

        Returns:
            str: The plan name
        """
        try:
            # Try to get plan name from price metadata
            price_data = subscription_data["items"]["data"][0]["price"]

            # First try metadata
            if price_data.get("metadata") and price_data["metadata"].get("plan_name"):
                return price_data["metadata"]["plan_name"]

            # Then try nickname
            if price_data.get("nickname"):
                return price_data["nickname"]

            # Then try product name
            if price_data.get("product") and isinstance(price_data["product"], dict):
                if price_data["product"].get("name"):
                    return price_data["product"]["name"]

            # Fallback to price ID
            return f"Plan {price_data['id']}"

        except Exception as e:
            logger.warning(f"Error extracting plan name: {e}")
            return "Unknown Plan"


# Global instance for dependency injection
stripe_webhook_handler = StripeWebhookHandler()
