from uuid import UUID

from pydantic import BaseModel


class SubscriptionInfo(BaseModel):
    """Subscription information for a user."""

    isPremium: bool
    planName: str | None = None
    status: str | None = None
    currentPeriodEnd: float | None = None
    cancelAtPeriodEnd: bool = False
    stripeSubscriptionId: str | None = None
    stripePriceId: str | None = None


class UserModel(BaseModel):
    uuid: UUID
    email: str
    name: str | None = None


class UserWithSubscriptionModel(BaseModel):
    """User model with subscription information."""

    id: int
    uuid: str
    email: str | None
    name: str | None
    clerk_sub: str | None
    stripe_customer_id: str | None
    created_at: float
    subscription: SubscriptionInfo | None
