"""Subscription related Pydantic models for API responses."""

from pydantic import BaseModel


class SubscriptionInfo(BaseModel):
    """Subscription information for API responses."""

    isPremium: bool
    planName: str | None = None
    status: str | None = None
    currentPeriodEnd: int | None = None
    cancelAtPeriodEnd: bool = False


class UserWithSubscription(BaseModel):
    """User model with subscription information."""

    id: int
    uuid: str
    email: str | None
    name: str | None
    subscription: SubscriptionInfo | None = None
