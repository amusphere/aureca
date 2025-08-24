from uuid import UUID

from pydantic import BaseModel

from app.models.subscription import SubscriptionInfo

# SubscriptionInfo moved to models/subscription.py to avoid duplication


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
    subscription: SubscriptionInfo | None = None
